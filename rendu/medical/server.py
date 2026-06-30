#!/usr/bin/env python3
"""Serveur local pour MedAssist — sert l'interface et proxifie Ollama (résout le CORS)."""
import http.server, urllib.request, urllib.error, json, sys, os

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
OLLAMA = "http://localhost:11434"
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/ollama/"):
            self._proxy("GET", self.path[7:])
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/ollama/"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else None
            self._proxy("POST", self.path[7:], body)
        else:
            self.send_error(404)

    def _proxy(self, method, path, body=None):
        url = OLLAMA + path
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                self._cors()
                ct = resp.headers.get("Content-Type", "application/json")
                self.send_header("Content-Type", ct)
                self.end_headers()
                # Streaming chunk par chunk
                while True:
                    chunk = resp.read(1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.URLError as e:
            self.send_error(502, str(e))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):
        pass  # silencieux

print(f"MedAssist disponible sur http://localhost:{PORT}")
print("Ctrl+C pour arrêter")
http.server.HTTPServer(("", PORT), Handler).serve_forever()
