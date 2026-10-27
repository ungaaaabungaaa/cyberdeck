"""Loopback-only, read-only viewer. Not a hosted or multi-user service."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
import re
from pathlib import Path
import time
from urllib.parse import parse_qsl, urlsplit
from .metrics import collect_live, replay_status
from .models import budget

PUBLIC = Path(__file__).resolve().parents[1] / "web"
ASSETS = {
    "index.html": "text/html; charset=utf-8",
    "styles.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
    "view-model.js": "text/javascript; charset=utf-8",
    "assets/panel.svg": "image/svg+xml",
    "assets/enclosure.scad": "text/plain; charset=utf-8",
    "assets/enclosure.json": "application/json",
    "assets/bom.csv": "text/csv; charset=utf-8",
}
HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


def make_server(port=8794, live=False, public=None, elapsed=None):
    public = Path(public or PUBLIC).resolve()
    started = time.monotonic()
    elapsed = elapsed or (lambda: time.monotonic() - started)

    class Handler(BaseHTTPRequestHandler):
        server_version = "CyberDeck"
        sys_version = ""

        def setup(self):
            super().setup()
            self.connection.settimeout(2)

        def log_message(self, *_args):
            pass

        def reply(self, code, body, kind="application/json; charset=utf-8"):
            if not isinstance(body, bytes):
                body = json.dumps(body, allow_nan=False).encode("utf-8")
            self.send_response(code)
            for name, value in HEADERS.items():
                self.send_header(name, value)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def send_error(self, code, message=None, explain=None):
            self.reply(
                405 if code == 501 else code,
                {"error": "Unsupported or malformed request."},
            )

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            try:
                expected = {
                    f"127.0.0.1:{self.server.server_port}",
                    f"localhost:{self.server.server_port}",
                }
                if (
                    len(self.headers.get_all("Host", [])) != 1
                    or self.headers.get("Host") not in expected
                ):
                    self.reply(403, {"error": "A matching loopback Host is required."})
                    return
                if len(self.path) > 2048:
                    raise ValueError("Request target exceeds the 2048-character limit.")
                url = urlsplit(self.path)
                if url.scheme or url.netloc or url.fragment:
                    raise ValueError("Use a local path without a fragment.")
                if url.path == "/api/v1/status":
                    if url.query:
                        raise ValueError("Status accepts no query parameters.")
                    self.reply(
                        200, collect_live() if live else replay_status(elapsed())
                    )
                elif url.path == "/api/v1/budget":
                    pairs = parse_qsl(
                        url.query,
                        keep_blank_values=True,
                        errors="strict",
                        max_num_fields=5,
                    )
                    if len({key for key, _ in pairs}) != len(pairs):
                        raise ValueError("Repeated query parameters are unsupported.")
                    values = {}
                    for key, value in pairs:
                        if not re.fullmatch(
                            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
                            value,
                            flags=re.ASCII,
                        ):
                            raise ValueError(
                                "Calculator parameters must use decimal numeric syntax."
                            )
                        try:
                            number = float(value)
                        except ValueError:
                            raise ValueError(
                                "Calculator parameters must be finite decimal numbers."
                            ) from None
                        if not math.isfinite(number):
                            raise ValueError(
                                "Calculator parameters must be finite decimal numbers."
                            )
                        values[key] = number
                    self.reply(200, budget(values))
                else:
                    name = "index.html" if url.path == "/" else url.path.lstrip("/")
                    if name not in ASSETS or url.query:
                        self.reply(404, {"error": "Public asset not found."})
                        return
                    try:
                        path = public / name
                        if (
                            path.is_symlink()
                            or not path.is_file()
                            or not path.resolve().is_relative_to(public)
                        ):
                            raise OSError("Non-public asset")
                        with path.open("rb") as stream:
                            data = stream.read(1024 * 1024 + 1)
                        if len(data) > 1024 * 1024:
                            raise OSError("Oversized asset")
                        self.reply(200, data, ASSETS[name])
                    except OSError:
                        self.reply(404, {"error": "Public asset unavailable."})
            except (ValueError, UnicodeError):
                self.reply(
                    400,
                    {
                        "error": "Invalid request or calculator parameters; see the documented limits."
                    },
                )
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
            except Exception:
                self.reply(500, {"error": "Local data could not be read."})

    class Server(HTTPServer):
        allow_reuse_address = True

    return Server(("127.0.0.1", port), Handler)
