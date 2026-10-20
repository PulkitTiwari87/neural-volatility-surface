"""Standard-library HTTP transport for the read-only research API (Phase 5). Local use only.

* GET only (every other method -> 405); loopback bind enforced because no authentication exists yet (Phase 6).
* ``dispatch`` is a pure function (path -> status, content type, body) so routes are testable without sockets.
* All logic lives in ``service.RunStore``; this module only maps URLs to it and errors to status codes.

    python -m volatility_lab.api.server --root <runs dir> [--port 8765]
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from volatility_lab.api.service import BadRequest, NotFound, RunStore

FRONTEND = Path(__file__).resolve().parents[4] / "frontend" / "index.html"
LOOPBACK = ("127.0.0.1", "localhost", "::1")
HEADERS = {
    "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                               "connect-src 'self'; base-uri 'none'; form-action 'none'",
}
_SURFACE = re.compile(r"^/api/runs/([^/]+)/surface/(\d{1,7})$")
_FORECAST = re.compile(r"^/api/runs/([^/]+)/forecasts/([^/]+)/(\d{1,7})$")
_TABLE = re.compile(r"^/api/runs/([^/]+)/tables/([^/]+)$")
_RUN = re.compile(r"^/api/runs/([^/]+)$")
_HOST = re.compile(r"^(?:\[([0-9a-f:.]+)\]|([^:\[\]@\s]+))(?::\d{1,5})?$")


def _json(code: int, obj) -> tuple:
    return code, "application/json", json.dumps(obj, allow_nan=False).encode()


def dispatch(store: RunStore, raw_path: str, frontend: Path = FRONTEND) -> tuple:
    path = urlsplit(raw_path).path
    try:
        if path in ("/", "/index.html"):
            return 200, "text/html; charset=utf-8", frontend.read_bytes()
        if path == "/api/runs":
            return _json(200, store.list_runs())
        if m := _SURFACE.match(path):
            return _json(200, store.surface(m.group(1), int(m.group(2))))
        if m := _FORECAST.match(path):
            return _json(200, store.forecast(m.group(1), m.group(2), int(m.group(3))))
        if m := _TABLE.match(path):
            return _json(200, store.table(m.group(1), m.group(2)))
        if m := _RUN.match(path):
            return _json(200, store.run_info(m.group(1)))
        return _json(404, {"error": "not found"})
    except BadRequest as e:
        return _json(400, {"error": str(e)})
    except NotFound as e:
        return _json(404, {"error": str(e)})
    except FileNotFoundError:
        return _json(404, {"error": "not found"})
    except (KeyError, IndexError, OSError, ValueError, zipfile.BadZipFile):
        # Safety net for a corrupt run file the service did not anticipate: a predictable generic body, never a
        # dropped connection or a stack trace / filesystem path in the response.
        return _json(500, {"error": "the run data could not be read"})


def make_handler(store: RunStore, frontend: Path = FRONTEND):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, ctype: str, body: bytes, extra: dict) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in {**HEADERS, **extra}.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _host_ok(self) -> bool:
            """DNS-rebinding guard for a local-only tool: only a loopback name may address this server. An absent or
            empty Host header (HTTP/1.0 clients) is allowed; the socket is loopback-bound regardless."""
            host = (self.headers.get("Host") or "").strip().lower()
            if not host:
                return True
            m = _HOST.match(host)
            return bool(m) and (m.group(1) or m.group(2)) in LOOPBACK

        def do_GET(self):  # noqa: N802
            if not self._host_ok():
                return self._send(*_json(400, {"error": "unexpected Host header"}), {})
            self._send(*dispatch(store, self.path, frontend), {})

        def _refuse(self):
            self._send(*_json(405, {"error": "read-only API"}), {"Allow": "GET"})

        do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = _refuse  # noqa: N815

        def log_message(self, *_):  # no request logging
            pass

    return Handler


def create_server(root, host: str = "127.0.0.1", port: int = 8765, frontend: Path = FRONTEND) -> ThreadingHTTPServer:
    if host not in LOOPBACK:
        raise ValueError("refusing non-loopback bind: the API has no authentication (Phase 6 scope)")
    return ThreadingHTTPServer((host, port), make_handler(RunStore(root), frontend))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True, help="directory containing one sub-directory per run")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    srv = create_server(a.root, port=a.port)
    print(f"serving {a.root} on http://127.0.0.1:{a.port}/ (read-only, local)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
