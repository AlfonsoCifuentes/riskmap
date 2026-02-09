"""
GET / — Landing page (catch-all route for Vercel).
Serves the dashboard SPA or a redirect.
"""

from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RiskMap — Geopolitical Intelligence</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0e17;
            color: #e0e0e0;
            font-family: 'Segoe UI', system-ui, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container { text-align: center; max-width: 600px; padding: 2rem; }
        h1 { font-size: 2.5rem; color: #00e5ff; margin-bottom: 0.5rem; }
        .subtitle { color: #90a4ae; margin-bottom: 2rem; }
        .endpoints {
            text-align: left;
            background: #141924;
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 1.5rem;
        }
        .endpoints h3 { color: #00e5ff; margin-bottom: 1rem; }
        .endpoint {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #1e2a3a;
        }
        .endpoint:last-child { border: none; }
        a { color: #4fc3f7; text-decoration: none; }
        a:hover { color: #00e5ff; }
        .method { color: #66bb6a; font-weight: bold; font-family: monospace; }
        .status { color: #66bb6a; font-size: 0.9rem; margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌍 RiskMap</h1>
        <p class="subtitle">Geopolitical Intelligence Platform — API Gateway</p>
        <div class="endpoints">
            <h3>API Endpoints</h3>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/articles">/api/articles</a></span>
                <span>Geopolitical articles</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/events">/api/events</a></span>
                <span>Conflict & disaster events</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/signals">/api/signals</a></span>
                <span>CV detection signals</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/images">/api/images</a></span>
                <span>Satellite & webcam imagery</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/heatmap">/api/heatmap</a></span>
                <span>Risk heatmap data</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/status">/api/status</a></span>
                <span>System status</span>
            </div>
        </div>
        <p class="status">✅ Powered by Neon Postgres · Deployed on Vercel</p>
    </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
