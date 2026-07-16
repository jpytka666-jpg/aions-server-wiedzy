"""Minimal HTTP stub: /health, /v1/speak, /v1/understand (port 11435)."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from . import mouth


def _json_response(handler: BaseHTTPRequestHandler, code: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:  # quieter
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("[aions-gguf] " + (fmt % args) + "\n")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/health", "/v1/health"):
            _json_response(self, 200, mouth.health())
            return
        if path == "/v1/models":
            h = mouth.health()
            _json_response(
                self,
                200,
                {"ok": True, "models": [{"id": h.get("model"), "backend": h.get("backend")}]},
            )
            return
        _json_response(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            _json_response(self, 400, {"ok": False, "error": "invalid JSON"})
            return

        if path == "/v1/understand":
            _json_response(self, 200, mouth.understand(str(data.get("text") or "")))
            return
        if path == "/v1/speak":
            _json_response(
                self,
                200,
                mouth.speak_with_gate(
                    str(data.get("context") or ""),
                    user_lang=str(data.get("user_lang") or "pl"),
                    gate_query=data.get("gate_query"),
                ),
            )
            return
        _json_response(self, 404, {"ok": False, "error": "not found"})


def serve(host: str = "127.0.0.1", port: int = 11435) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"aions-gguf listening on http://{host}:{port}  (Ctrl+C to stop)")
    print("  GET  /health")
    print("  POST /v1/understand  POST /v1/speak")
    httpd.serve_forever()
