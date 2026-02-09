"""
Vercel Serverless: DB helper for all API routes.
Uses Neon Data API (PostgREST-compatible REST) — no psycopg2 needed in serverless.
Falls back to psycopg2 if NEON_API_URL is not set.
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, date


# ---------------------------------------------------------------------------
# Neon REST API client
# ---------------------------------------------------------------------------

NEON_API_URL = os.getenv('NEON_API_URL', '')
NEON_API_KEY = os.getenv('NEON_API_KEY', '')


def _neon_headers():
    """Build auth headers for Neon Data API."""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    if NEON_API_KEY:
        headers['Authorization'] = f'Bearer {NEON_API_KEY}'
    return headers


def neon_get(table: str, params: dict = None, select: str = '*',
             order: str = None, limit: int = None, offset: int = None) -> list:
    """
    Query a table via Neon REST API (PostgREST syntax).
    Example: neon_get('unified_articles', {'geopolitical_relevance': 'eq.1'}, limit=20)
    """
    url = f"{NEON_API_URL}/{table}"
    qs = {}
    if select != '*':
        qs['select'] = select
    if order:
        qs['order'] = order
    if limit:
        qs['limit'] = str(limit)
    if offset:
        qs['offset'] = str(offset)
    if params:
        qs.update(params)

    if qs:
        url += '?' + urllib.parse.urlencode(qs, doseq=True)

    req = urllib.request.Request(url, headers=_neon_headers(), method='GET')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ''
        raise RuntimeError(f"Neon API {e.code}: {body}")


def neon_rpc(function_name: str, params: dict = None) -> list:
    """Call a Postgres function via Neon REST API RPC endpoint."""
    url = f"{NEON_API_URL}/rpc/{function_name}"
    data = json.dumps(params or {}).encode()
    req = urllib.request.Request(url, data=data, headers=_neon_headers(), method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ''
        raise RuntimeError(f"Neon RPC {e.code}: {body}")


def neon_sql(query: str, params: list = None) -> list:
    """
    Execute raw SQL via Neon's /query endpoint (if available).
    Falls back to psycopg2 if not supported.
    """
    # Try the Neon SQL-over-HTTP endpoint
    base = NEON_API_URL.rsplit('/rest/', 1)[0] if '/rest/' in NEON_API_URL else ''
    if base:
        url = f"{base}/sql"
        payload = json.dumps({'query': query, 'params': params or []}).encode()
        headers = _neon_headers()
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                # Neon SQL endpoint returns {columns: [...], rows: [[...]]}
                if 'rows' in data and 'columns' in data:
                    cols = [c['name'] for c in data['columns']]
                    return [dict(zip(cols, row)) for row in data['rows']]
                return data if isinstance(data, list) else []
        except Exception:
            pass

    # Fallback: psycopg2 direct connection
    return _psycopg2_query(query, params)


def _psycopg2_query(query: str, params: list = None) -> list:
    """Fallback: direct psycopg2 connection to Neon Postgres."""
    dsn = os.getenv('DATABASE_URL', '')
    if not dsn or not dsn.startswith('postgres'):
        raise RuntimeError("Neither NEON_API_URL nor DATABASE_URL (postgres) is configured")
    import psycopg2
    from psycopg2.extras import RealDictCursor
    conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(query, params or [])
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def json_serial(obj):
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, memoryview):
        return None
    if isinstance(obj, bytes):
        return None
    raise TypeError(f"Type {type(obj)} not serializable")


def json_response(data, status=200):
    """Build a JSON HTTP response dict for Vercel."""
    body = json.dumps(data, default=json_serial, ensure_ascii=False)
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, s-maxage=60, stale-while-revalidate=120',
        },
        'body': body,
    }


def error_response(message, status=500):
    return json_response({'error': message}, status)


def send_response(handler, resp):
    """Send a json_response/error_response dict through a BaseHTTPRequestHandler."""
    handler.send_response(resp['statusCode'])
    for k, v in resp['headers'].items():
        handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(resp['body'].encode())
