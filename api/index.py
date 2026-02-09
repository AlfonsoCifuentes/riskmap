"""
GET / — Serves the main dashboard SPA (catch-all route for Vercel).
Reads dashboard_BUENO.html from disk and serves it as the homepage.
"""

import os
from http.server import BaseHTTPRequestHandler

# Cache the dashboard HTML in module scope (cold-start optimisation)
_DASHBOARD_HTML: bytes | None = None


def _load_dashboard() -> bytes:
    """Read dashboard_BUENO.html once and cache it."""
    global _DASHBOARD_HTML
    if _DASHBOARD_HTML is None:
        template_path = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'web', 'templates', 'dashboard_BUENO.html'
        )
        with open(template_path, 'r', encoding='utf-8') as f:
            _DASHBOARD_HTML = f.read().encode('utf-8')
    return _DASHBOARD_HTML


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            html = _load_dashboard()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=600')
            self.end_headers()
            self.wfile.write(html)
        except FileNotFoundError:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Dashboard template not found')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Error loading dashboard: {e}'.encode())
