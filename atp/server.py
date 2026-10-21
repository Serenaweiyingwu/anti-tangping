"""Phone triggers over the local Wi-Fi: an iPhone Shortcut calls http://<laptop-ip>:8765/alarm when the alarm
is stopped. The same paths work from a browser for testing."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def serve(brain, port: int = 8765) -> ThreadingHTTPServer:
    commands = {
        "/alarm": brain.alarm,
        "/work/on": brain.start_work,
        "/work/off": brain.stop_work,
        "/desk": brain.desk,
        "/bed": brain.bed,
        "/home": brain.home,
    }

    class Handler(BaseHTTPRequestHandler):
        def _answer(self):
            command = commands.get(self.path.split("?")[0].rstrip("/") or "/")
            if command:
                command()
            self.send_response(200 if command else 404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok\n" if command else ("paths: " + " ".join(commands) + "\n").encode())

        do_GET = do_POST = _answer

        def log_message(self, fmt, *args):
            print(f"[phone] {self.path}", flush=True)

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
