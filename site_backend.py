#!/usr/bin/env python3
"""Local studio page for http://127.0.0.1:4174.

The last preview failed closed: nothing was listening, so the browser reported
connection refused. This process is the page and the health check. It does not
start a paid render.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = "127.0.0.1"
PORT = 4174

HEALTH = {
    "ok": True,
    "service": "asteriq-studio",
    "port": PORT,
    "real_test_allowed": False,
    "blockers": [
        "the picture proof must pass the frame gate before another render",
        "the voice must be altered; the original soundtrack cannot be copied",
        "background and room voices must be removed from the mix",
        "anime and the other styles must stay upright; a sideways frame cannot be saved as the reusable 3D character",
    ],
}

PAGE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Asteriq studio</title>
<style>
  body { margin: 0; background: #1b1d21; color: #e8e6e3; font: 16px/1.5 sans-serif; }
  main { max-width: 720px; margin: 8vh auto; padding: 0 24px; }
  h1 { font-size: 28px; font-weight: 650; }
  .ok { color: #8fd18a; }
  li { margin: 8px 0; }
  code { color: #f0d090; }
</style>
<main>
  <p class="ok" id="status">Checking the local studio…</p>
  <h1>Asteriq is running on this machine.</h1>
  <p>The real test stays off until the last failure is closed. The blue ghosted picture, the unchanged voice, and the background voice are blockers, not a master.</p>
  <ul id="blockers"></ul>
</main>
<script>
fetch("/api/health").then(r => r.json()).then(health => {
  document.getElementById("status").textContent = health.ok
    ? "Local studio is reachable."
    : "Local studio reported a problem.";
  const list = document.getElementById("blockers");
  for (const item of health.blockers || []) {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  }
}).catch(() => {
  document.getElementById("status").textContent = "The health check did not answer.";
});
</script>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] == "/api/health":
            self._send(200, json.dumps(HEALTH).encode(), "application/json")
            return
        if self.path.split("?", 1)[0] in {"/", "/index.html"}:
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
            return
        self._send(404, b'{"ok": false}', "application/json")

    def log_message(self, fmt: str, *args) -> None:
        print(f"[asteriq] {self.address_string()} {fmt % args}", flush=True)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(json.dumps({"listening": f"http://{HOST}:{PORT}", "health": f"http://{HOST}:{PORT}/api/health"}), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
