from http.client import HTTPConnection
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from cyberdeck.metrics import collect_live
from jsonschema import Draft202012Validator, FormatChecker
from cyberdeck.server import make_server


SPEC = json.loads((Path(__file__).parents[1] / "docs/api/openapi.json").read_text())


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "index.html").write_text("<p>CyberDeck</p>")
        (self.root / "private.key").write_text("private")
        self.server = make_server(port=0, public=self.root, elapsed=lambda: 10)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def request(self, path, method="GET", host=None):
        client = HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            client.request(
                method, path, headers={"Host": host or f"127.0.0.1:{self.port}"}
            )
            response = client.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            client.close()

    def validate(self, name, value):
        schema = {
            "$ref": f"#/components/schemas/{name}",
            "components": SPEC["components"],
        }
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)

    def test_each_api_response_matches_reviewed_openapi_schema(self):
        for path, name in [("/api/v1/status", "Status"), ("/api/v1/budget", "Budget")]:
            code, headers, data = self.request(path)
            self.assertEqual(code, 200)
            self.validate(name, json.loads(data))
            self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
            self.assertNotIn("Access-Control-Allow-Origin", headers)
        code, _, data = self.request(
            "/api/v1/budget?capacity_wh=100&load_w=10&efficiency=0.8&reserve_fraction=0.25&supply_w=15"
        )
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(data)["usable_runtime_hours"], 6)

    def test_live_status_uses_startup_filesystem_selection(self):
        sample = collect_live(root=self.root, disk_usage=lambda _: (1000, 600, 400), disk_path=self.root)
        server = make_server(port=0, live=True, disk_path=self.root)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch("cyberdeck.server.collect_live", return_value=sample) as reader:
                client = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                try:
                    client.request("GET", "/api/v1/status")
                    response = client.getresponse()
                    self.assertEqual(response.status, 200)
                    result = json.loads(response.read())
                    self.validate("Status", result)
                    self.assertEqual(result["metrics"]["disk_free_bytes"], 400)
                    reader.assert_called_once_with(disk_path=self.root)
                finally:
                    client.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_bad_queries_host_methods_private_paths_and_head(self):
        for path in [
            "/api/v1/status?x=1",
            "/api/v1/budget?unknown=1",
            "/api/v1/budget?load_w=",
            "/api/v1/budget?load_w=1&load_w=2",
            "/api/v1/budget?load_w=nan",
            "/api/v1/budget?load_w=1_0",
            "/api/v1/budget?efficiency=2",
            "/api/v1/budget?" + "x" * 2050,
        ]:
            code, _, data = self.request(path)
            self.assertEqual(code, 400, path)
            self.validate("Error", json.loads(data))
        self.assertEqual(self.request("/", host="attacker.example")[0], 403)
        for method in ["POST", "PUT", "DELETE", "PATCH", "BREW"]:
            self.assertEqual(self.request("/", method=method)[0], 405)
        for path in ["/private.key", "/../docs/contract.md", "/docs/api/openapi.json"]:
            self.assertEqual(self.request(path)[0], 404)
        code, headers, data = self.request("/", method="HEAD")
        self.assertEqual(code, 200)
        self.assertEqual(data, b"")
        self.assertEqual(int(headers["Content-Length"]), len(b"<p>CyberDeck</p>"))

    def test_public_assets_reject_oversized_files_and_links(self):
        (self.root / "app.js").write_bytes(b"x" * (1024 * 1024 + 1))
        self.assertEqual(self.request("/app.js")[0], 404)
        try:
            (self.root / "styles.css").symlink_to(self.root / "private.key")
        except OSError:
            return  # Some Windows runners do not grant symlink creation.
        self.assertEqual(self.request("/styles.css")[0], 404)


if __name__ == "__main__":
    unittest.main()
