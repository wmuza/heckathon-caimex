"""Serve web/ on its own port and forward /api/* to the backend.

Usage: python tools/frontend.py [front_port] [backend_url]
       python tools/frontend.py 5173 http://127.0.0.1:8000
"""

import sys
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5173
BACKEND = (sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000").rstrip("/")
PAGES = {"/welcome", "/nurse", "/outbreaks", "/national", "/board", "/doctor",
         "/pharmacy", "/vitals", "/engine", "/check", "/demo"}
SKIP_REQ = {"host", "connection", "content-length"}
SKIP_RESP = {"transfer-encoding", "connection"}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(WEB), **kw)

    def _proxy(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(BACKEND + self.path, data=body, method=self.command)
        for k, v in self.headers.items():
            if k.lower() not in SKIP_REQ:
                req.add_header(k, v)
        try:
            resp = urllib.request.urlopen(req, timeout=300)
        except urllib.error.HTTPError as e:
            resp = e
        except urllib.error.URLError as e:
            self.send_error(502, f"Backend not reachable at {BACKEND}: {e.reason}")
            return
        self.send_response(resp.status)
        for k, v in resp.headers.items():
            if k.lower() not in SKIP_RESP:
                self.send_header(k, v)
        self.end_headers()
        while chunk := resp.read1(8192) if hasattr(resp, "read1") else resp.read(8192):
            self.wfile.write(chunk)
            self.wfile.flush()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path.startswith("/api/"):
            return self._proxy()
        if path in PAGES:  # /nurse -> nurse.html, as the backend does
            self.path = path + ".html"
        super().do_GET()

    do_POST = do_PUT = do_PATCH = do_DELETE = _proxy


if __name__ == "__main__":
    print(f"Frontend  http://127.0.0.1:{PORT}   ->   API {BACKEND}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
