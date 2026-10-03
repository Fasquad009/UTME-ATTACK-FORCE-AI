import os
from http.server import BaseHTTPRequestHandler, HTTPServer

print("UTME ATTACK FORCE AI is starting...")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"UTME ATTACK FORCE AI is running!")

    def log_message(self, format, *args):
        pass

port = int(os.environ.get("PORT", 10000))

server = HTTPServer(("0.0.0.0", port), Handler)

print("Welcome to UTME ATTACK FORCE AI!")
print("Subjects: English, Mathematics, Chemistry, Physics, Biology")
print("AI is ready to help you study.")
print(f"Server running on port {port}")

server.serve_forever()
