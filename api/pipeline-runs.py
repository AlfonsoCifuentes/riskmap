"""
GET /api/pipeline-runs
Recent pipeline stage runs for the System Observatory / Pipeline Run Explorer
(spec §107). Reads the pipeline_runs table populated by src.core.observability.
Degrades gracefully to an empty list if the table has no rows yet.
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._db import error_from_exc, json_response, neon_sql, send_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            limit = min(int(qs.get("limit", ["30"])[0]), 200)
            try:
                rows = neon_sql(
                    """
                    SELECT id, stage, started_at, finished_at, status,
                           items_in, items_out, errors, cost_estimate_eur,
                           git_sha, notes
                    FROM pipeline_runs
                    ORDER BY started_at DESC
                    LIMIT %s
                    """,
                    [limit],
                )
            except Exception:
                rows = []  # table may not exist yet on a fresh DB

            runs = []
            for r in rows:
                started = r.get("started_at")
                finished = r.get("finished_at")
                duration = None
                if started and finished:
                    duration = round((finished - started).total_seconds(), 1)
                runs.append({
                    "id": r.get("id"),
                    "stage": r.get("stage"),
                    "status": r.get("status"),
                    "started_at": started.isoformat() if started else None,
                    "finished_at": finished.isoformat() if finished else None,
                    "duration_seconds": duration,
                    "items_in": r.get("items_in"),
                    "items_out": r.get("items_out"),
                    "errors": r.get("errors"),
                    "cost_estimate_eur": r.get("cost_estimate_eur"),
                    "git_sha": (r.get("git_sha") or "")[:12] or None,
                    "notes": r.get("notes"),
                })

            send_response(self, json_response({"runs": runs, "count": len(runs)}))
        except Exception as e:
            send_response(self, error_from_exc(e))
