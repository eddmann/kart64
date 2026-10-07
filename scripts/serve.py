#!/usr/bin/env python3
"""Static server for a build directory.

Usage: serve.py [dir] [port] [--plain]   (defaults: cwd, 8099)

Sends the cross-origin-isolation headers the pthreads build needs. --plain
leaves them off, which is how GitHub Pages serves: the page then isolates
itself with its service worker (web/coi-sw.js).

To try a local build on a phone, put a tunnel in front (`ngrok http 8099`):
the page needs HTTPS there. A dev build dir may hold an extracted mk64.o2r
for the ?prebuilt shortcut, so that file is only ever served to localhost.
"""
import http.server
import mimetypes
import posixpath
import re
import sys
from urllib.parse import urlsplit

# Python does not know this one, and an octet-stream manifest is ignored.
mimetypes.add_type("application/manifest+json", ".webmanifest")

ROM_DERIVED = re.compile(r"^(mk64|baserom)|\.(z64|v64|n64)$", re.I)
LOCAL_HOSTS = ("localhost", "127.0.0.1")


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        name = posixpath.basename(urlsplit(self.path).path)
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if ROM_DERIVED.search(name) and host not in LOCAL_HOSTS:
            self.send_error(404)
            return None
        return super().send_head()

    def end_headers(self):
        if not PLAIN:
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


args = [a for a in sys.argv[1:] if not a.startswith("--")]
PLAIN = "--plain" in sys.argv
directory = args[0] if len(args) > 0 else "."
port = int(args[1]) if len(args) > 1 else 8099

http.server.ThreadingHTTPServer(
    ("127.0.0.1", port),
    lambda *a, **kw: Handler(*a, directory=directory, **kw),
).serve_forever()
