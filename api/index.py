"""
GET /api/index — Redirect to homepage.
Dashboard is served as a static file from public/index.html.
"""

from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
