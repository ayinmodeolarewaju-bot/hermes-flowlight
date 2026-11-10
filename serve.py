"""Loopback page that draws the same picture as the Desktop pane."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import webapi

_ROOT = Path(__file__).resolve().parent / "frontend"
_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/engine.js": ("engine.js", "text/javascript; charset=utf-8"),
    "/boot.js": ("boot.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


def serve(port: int = 8787, demo: bool = False) -> None:
    if demo:
        webapi.shared_deps().settings.demo_mode = True
    handler = _handler_factory()
    server = ThreadingHTTPServer(("127.0.0.1", int(port)), handler)
    print(f"Flowlight picture at http://127.0.0.1:{int(port)}/")
    print("Read-only. This page does not sign or send transactions. Ctrl-C stops it.")
    if demo:
        print("Opened in demo fixture mode. The page can still request live data.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def _handler_factory():
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: object) -> None:
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload: dict) -> None:
            self._send(status, json.dumps(payload, default=str).encode("utf-8"), "application/json; charset=utf-8")

        def _query(self) -> dict[str, str]:
            parsed = urlparse(self.path)
            raw = parse_qs(parsed.query)
            return {key: values[-1] for key, values in raw.items() if values}

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0 or length > 20000:
                return {}
            raw = self.rfile.read(length)
            try:
                loaded = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                return {}
            return loaded if isinstance(loaded, dict) else {}

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/graph":
                self._json(200, webapi.view_graph(self._query()))
                return
            if path == "/api/summary":
                self._json(200, webapi.view_summary(self._query()))
                return
            if path == "/api/flows":
                self._json(200, webapi.view_flows(self._query()))
                return
            if path == "/api/watches":
                self._json(200, webapi.view_watches())
                return
            if path == "/api/health":
                self._json(200, {"ok": True, "plugin": "flowlight", "read_only": True, "funds_moved": False})
                return
            spec = _FILES.get(path)
            if spec is None:
                self._send(404, b"Not found", "text/plain; charset=utf-8")
                return
            file_path = _ROOT / spec[0]
            if not file_path.is_file():
                self._send(404, b"Missing frontend file", "text/plain; charset=utf-8")
                return
            self._send(200, file_path.read_bytes(), spec[1])

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            body = self._body()
            if path == "/api/watch":
                self._json(200, webapi.post_watch(body))
                return
            if path == "/api/unwatch":
                self._json(200, webapi.post_unwatch(body))
                return
            self._json(404, {"ok": False, "error": "Unknown path"})

    return Handler
