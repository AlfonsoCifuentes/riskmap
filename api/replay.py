"""
GET /api/replay                 -> list available replay scenarios
GET /api/replay?scenario=<id>   -> run a scenario through the core pipeline

Deterministic demonstration data (spec §39/§93). Every response is flagged
REPLAY so it can never be mistaken for live data. Runs with zero external deps,
so the demo always works even when providers are down.
"""
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Make the project root importable (src.core.replay lives outside api/).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api._db import error_from_exc, json_response, send_response  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from src.core import replay
            qs = parse_qs(urlparse(self.path).query)
            scenario = qs.get("scenario", [None])[0]

            if not scenario:
                send_response(self, json_response({
                    "data_kind": "REPLAY",
                    "scenarios": replay.list_scenarios(),
                }))
                return

            try:
                result = replay.run(scenario)
            except FileNotFoundError:
                send_response(self, json_response(
                    {"error": "unknown scenario",
                     "scenarios": [s["id"] for s in replay.list_scenarios()]},
                    404))
                return

            send_response(self, json_response(result))
        except Exception as e:
            send_response(self, error_from_exc(e))
