#!/usr/bin/env python3
"""Cloud resolver for montemusic.pages.dev.

Runs on Render (or any host), reachable over the public internet with a
real trusted HTTPS cert — unlike the local Mac helper, this doesn't need
the Mac or the home WiFi. It only does the "resolve a YouTube link into a
direct playable audio URL" step; VLC (on the phone) and the Marantz still
need their own delivery path.

Routes:
  GET /resolve?url=<youtube-url>  -> {ok, streamUrl} or {ok: false, error}
  GET /health
"""
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("PORT", 8080))
ALLOWED_ORIGIN = "https://montemusic.pages.dev"


def resolve_audio_url(youtube_url):
    result = subprocess.run(
        ["yt-dlp", "--no-playlist", "-f", "bestaudio[ext=m4a]", "-g", youtube_url],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "yt-dlp failed")
    stream_url = result.stdout.strip().splitlines()[0]
    if not stream_url:
        raise RuntimeError("yt-dlp returned no stream URL")
    return stream_url


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/resolve":
            youtube_url = params.get("url", [None])[0]
            if not youtube_url:
                return self._send_json(400, {"ok": False, "error": "missing url param"})
            try:
                stream_url = resolve_audio_url(youtube_url)
                return self._send_json(200, {"ok": True, "streamUrl": stream_url})
            except Exception as e:
                print("resolve failed:", e)
                return self._send_json(500, {"ok": False, "error": str(e)})

        if parsed.path == "/health":
            return self._send_json(200, {"ok": True})

        self._send_json(404, {"ok": False, "error": "not found"})


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"montemusic resolver listening on 0.0.0.0:{PORT}")
    server.serve_forever()
