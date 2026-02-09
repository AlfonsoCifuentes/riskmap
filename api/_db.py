"""
Vercel Serverless: DB helper for all API routes.
Uses psycopg2-binary to connect directly to Neon Postgres via DATABASE_URL.
Falls back to PostgREST API if NEON_API_URL + NEON_API_KEY are set.
"""

import os
import re
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, date


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NEON_API_URL = os.getenv('NEON_API_URL', '')
NEON_API_KEY = os.getenv('NEON_API_KEY', '')
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Prefer direct psycopg2 connection (reliable, standard).
# Only fall back to PostgREST if DATABASE_URL is NOT set but API URL+KEY are.
_USE_POSTGREST = bool(
    not DATABASE_URL
    and NEON_API_URL and NEON_API_KEY
    and not NEON_API_URL.startswith('${')
)


# ---------------------------------------------------------------------------
# Direct Postgres connection (primary method — uses DATABASE_URL)
# ---------------------------------------------------------------------------

def _pg_query(query: str, params: tuple = None) -> list:
    """Execute SQL via psycopg2 direct connection to Neon Postgres."""
    import psycopg2
    import psycopg2.extras
    dsn = DATABASE_URL
    if not dsn or not dsn.startswith('postgres'):
        raise RuntimeError("DATABASE_URL is not configured")
    conn = psycopg2.connect(dsn, sslmode='require')
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        rows = [dict(row) for row in cur.fetchall()]
        cur.close()
        return rows
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# PostgREST client (alternative if NEON_API_URL + NEON_API_KEY configured)
# ---------------------------------------------------------------------------


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
    Query a table. Uses PostgREST if configured, otherwise builds SQL
    and queries via direct Postgres connection (psycopg2).
    """
    if _USE_POSTGREST:
        return _postgrest_get(table, params, select, order, limit, offset)

    # Build SQL query from PostgREST-style params
    columns = select if select != '*' else '*'
    sql = f"SELECT {columns} FROM {table}"

    where_clauses = []
    if params:
        for col, expr in params.items():
            # Handle PostgREST IS NULL / IS NOT NULL operators
            if expr == 'is.null':
                where_clauses.append(f"{col} IS NULL")
            elif expr == 'not.is.null':
                where_clauses.append(f"{col} IS NOT NULL")
            elif '.' in expr:
                # Parse PostgREST operators: eq.val, gte.val, etc.
                op, val = expr.split('.', 1)
                op_map = {
                    'eq': '=', 'neq': '!=', 'gt': '>', 'gte': '>=',
                    'lt': '<', 'lte': '<=', 'like': 'LIKE', 'ilike': 'ILIKE',
                }
                sql_op = op_map.get(op, '=')
                where_clauses.append(f"{col} {sql_op} '{val}'")
            else:
                where_clauses.append(f"{col} = '{expr}'")

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    if order:
        # Convert PostgREST order: "published_at.desc.nullslast" → "published_at DESC NULLS LAST"
        order_parts = []
        for part in order.split(','):
            tokens = part.strip().split('.')
            col_name = tokens[0]
            direction = 'ASC'
            nulls = ''
            for t in tokens[1:]:
                if t.lower() == 'desc':
                    direction = 'DESC'
                elif t.lower() == 'asc':
                    direction = 'ASC'
                elif t.lower() == 'nullslast':
                    nulls = ' NULLS LAST'
                elif t.lower() == 'nullsfirst':
                    nulls = ' NULLS FIRST'
            order_parts.append(f"{col_name} {direction}{nulls}")
        sql += " ORDER BY " + ", ".join(order_parts)

    if limit:
        sql += f" LIMIT {int(limit)}"
    if offset:
        sql += f" OFFSET {int(offset)}"

    return _pg_query(sql)


def _postgrest_get(table, params, select, order, limit, offset):
    """Query via PostgREST API (requires NEON_API_URL + NEON_API_KEY)."""
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
    """Execute raw SQL via direct Postgres connection."""
    return _pg_query(query, tuple(params) if params else None)


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
