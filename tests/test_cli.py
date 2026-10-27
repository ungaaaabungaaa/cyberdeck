from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from cyberdeck.cli import main
from cyberdeck.files import read_config, write_bundle


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_commands_produce_actual_reports_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            code, out, _ = self.invoke("status")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["mode"], "replay")
            code, out, _ = self.invoke("budget")
            self.assertEqual(code, 0)
            self.assertAlmostEqual(
                json.loads(out)["usable_runtime_hours"], 74 * 0.85 * 0.8 / 13
            )
            destination = root / "design"
            self.assertEqual(self.invoke("enclosure", "--out", str(destination))[0], 0)
            self.assertEqual(
                set(p.name for p in destination.iterdir()),
                {"enclosure.scad", "panel.svg", "enclosure.json"},
            )
            self.assertEqual(self.invoke("enclosure", "--out", str(destination))[0], 1)
            setup = root / "setup"
            self.assertEqual(
                self.invoke("prepare", "--out", str(setup), "--user", "deck")[0], 0
            )
            service = (setup / "cyberdeck.service").read_text()
            self.assertIn("/home/deck/cyberdeck", service)
            self.assertIn("-m cyberdeck serve --live", service)
            self.assertNotIn("After=default.target", service)
            self.assertNotIn("sudo", service)
            self.assertEqual(
                self.invoke(
                    "prepare", "--out", str(root / "bad"), "--user", "../root;bad"
                )[0],
                2,
            )
            self.assertFalse((root / "bad").exists())

    def test_invalid_config_utf8_depth_size_and_failed_bundle_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "config.json"
            for content in [
                b"\xff",
                b"x" * 16385,
                b"{",
                b"null",
                b"[1]",
                b'{"load_w":NaN}',
                ('{"x":' * 10 + "0" + "}" * 10).encode(),
            ]:
                path.write_bytes(content)
                with self.assertRaises(ValueError):
                    read_config(path)
            path.write_text('{"load_w":10}')
            self.assertEqual(read_config(path), {"load_w": 10})
            destination = root / "failed"
            with self.assertRaises(OSError):
                write_bundle(destination, {"first": "value", "missing/second": "fail"})
            self.assertFalse(destination.exists())
            try:
                link = root / "linked.json"
                link.symlink_to(path)
            except OSError:
                return
            with self.assertRaises(ValueError):
                read_config(link)


if __name__ == "__main__":
    unittest.main()
