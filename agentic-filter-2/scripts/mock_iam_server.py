#!/usr/bin/env python3
"""Minimal IAM stub: GET /v1/token/validate → JSON claims for demo user.

Run from repo root:
  python scripts/mock_iam_server.py

Env:
  MOCK_IAM_PORT (default 9999)
  MOCK_IAM_BIND (default on Windows: 127.0.0.1 — avoids WinError 10013 on 0.0.0.0;
                  default elsewhere: 0.0.0.0)
  DEMO_USER_ID (optional override UUID string)
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "demo_constants", Path(__file__).resolve().parent / "demo_constants.py"
)
_dc = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_dc)
_DEFAULT_DEMO_USER_ID = _dc.DEMO_USER_ID


def _claims() -> dict:
    uid = os.environ.get("DEMO_USER_ID", str(_DEFAULT_DEMO_USER_ID))
    return {
        "user_id": uid,
        "username": "demo_user",
        "email": "demo@example.com",
        "is_active": True,
    }


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path != "/v1/token/validate":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(_claims()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print(f"[mock-iam] {self.address_string()} {args[0]}")


def main() -> None:
    port = int(os.environ.get("MOCK_IAM_PORT", "9999"))
    bind = os.environ.get("MOCK_IAM_BIND")
    if bind is None or bind.strip() == "":
        bind = "127.0.0.1" if sys.platform == "win32" else "0.0.0.0"
    print(
        f"Mock IAM listening on http://127.0.0.1:{port}/v1/token/validate "
        f"(bound {bind}:{port})"
    )
    HTTPServer((bind, port), _Handler).serve_forever()


if __name__ == "__main__":
    main()
