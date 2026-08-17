"""
Vercel Serverless: DB helper for all API routes.
Uses psycopg2-binary to connect directly to Neon Postgres via DATABASE_URL.
Falls back to PostgREST API if NEON_API_URL + NEON_API_KEY are set.
"""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

# ---------------------------------------------------------------------------
# HTML / text cleanup
# ---------------------------------------------------------------------------

_RE_TAGS = re.compile(r'<[^>]*?>|<[^>]*$', re.DOTALL)
_RE_ENTITIES = re.compile(r'&(?:nbsp|amp|lt|gt|quot|#0?39|#x27|#\d{1,5});?', re.IGNORECASE)

_ENTITY_MAP = {
    'nbsp': ' ', 'amp': '&', 'lt': '<', 'gt': '>',
    'quot': '"', '#039': "'", '#0039': "'", '#x27': "'",
}


def _decode_entity(m):
    key = m.group(0).lstrip('&').rstrip(';').lower()
    if key in _ENTITY_MAP:
        return _ENTITY_MAP[key]
    if key.startswith('#'):
        try:
            return chr(int(key[1:]))
        except (ValueError, OverflowError):
            pass
    return m.group(0)


def strip_html(text):
    """Remove HTML tags (including truncated ones) and decode entities."""
    if not text:
        return text
    s = str(text)
    s = _RE_TAGS.sub('', s)
    s = _RE_ENTITIES.sub(_decode_entity, s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def clean_article(article):
    """Strip HTML from title, summary, content, and ai_summary fields."""
    for field in ('title', 'summary', 'content', 'ai_summary'):
        if field in article and article[field]:
            article[field] = strip_html(article[field])
    return article


def clean_articles(articles):
    """Strip HTML from a list of articles."""
    for a in articles:
        clean_article(a)
    return articles


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


# ---------------------------------------------------------------------------
# Safe query builder
# ---------------------------------------------------------------------------
#
# SECURITY: every SQL identifier (table / column) is validated against a strict
# lowercase-identifier regex, and every user-supplied *value* is passed to the
# driver as a bound parameter (%s), never interpolated into the SQL string.
# This closes the SQL-injection vector documented in the audit addendum (B1).

class BadRequest(ValueError):
    """Raised when a request references an invalid identifier or operator.

    API handlers should map this to HTTP 400 (not 500)."""


_IDENT_RE = re.compile(r'^[a-z_][a-z0-9_]*$')

# PostgREST-style operator -> SQL operator. Anything not here is rejected.
_OP_MAP = {
    'eq': '=', 'neq': '!=', 'gt': '>', 'gte': '>=',
    'lt': '<', 'lte': '<=', 'like': 'LIKE', 'ilike': 'ILIKE',
}


def _ident(name: str) -> str:
    """Validate a single SQL identifier (table or column). Returns it unchanged."""
    if not isinstance(name, str) or not _IDENT_RE.match(name):
        raise BadRequest(f"invalid identifier: {name!r}")
    return name


def neon_get(table: str, params: dict = None, select: str = '*',
             order: str = None, limit: int = None, offset: int = None) -> list:
    """
    Query a table safely. Uses PostgREST if configured, otherwise builds a
    parameterized SQL query and runs it via a direct Postgres connection.

    Identifiers (table/columns/order columns) are validated; all filter values
    are bound as parameters. Raises BadRequest (-> HTTP 400) on invalid input.
    """
    if _USE_POSTGREST:
        return _postgrest_get(table, params, select, order, limit, offset)

    table = _ident(table)

    # --- SELECT columns (validated identifiers only) ---
    if select and select != '*':
        cols = [_ident(c.strip()) for c in select.split(',') if c.strip()]
        columns = ', '.join(cols) if cols else '*'
    else:
        columns = '*'

    sql = f"SELECT {columns} FROM {table}"
    values: list = []

    # --- WHERE clauses: identifiers validated, values bound ---
    where_clauses = []
    if params:
        for col, expr in params.items():
            col = _ident(col)
            if expr == 'is.null':
                where_clauses.append(f"{col} IS NULL")
            elif expr == 'not.is.null':
                where_clauses.append(f"{col} IS NOT NULL")
            elif isinstance(expr, str) and '.' in expr:
                op, val = expr.split('.', 1)
                if op not in _OP_MAP:
                    raise BadRequest(f"invalid operator: {op!r}")
                where_clauses.append(f"{col} {_OP_MAP[op]} %s")
                values.append(val)
            else:
                where_clauses.append(f"{col} = %s")
                values.append(expr)

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    # --- ORDER BY: column identifiers validated, direction from fixed set ---
    if order:
        order_parts = []
        for part in order.split(','):
            tokens = part.strip().split('.')
            col_name = _ident(tokens[0])
            direction = 'ASC'
            nulls = ''
            for t in tokens[1:]:
                tl = t.lower()
                if tl == 'desc':
                    direction = 'DESC'
                elif tl == 'asc':
                    direction = 'ASC'
                elif tl == 'nullslast':
                    nulls = ' NULLS LAST'
                elif tl == 'nullsfirst':
                    nulls = ' NULLS FIRST'
                else:
                    raise BadRequest(f"invalid order token: {t!r}")
            order_parts.append(f"{col_name} {direction}{nulls}")
        sql += " ORDER BY " + ", ".join(order_parts)

    # --- LIMIT / OFFSET: bound integers ---
    if limit is not None:
        sql += " LIMIT %s"
        values.append(int(limit))
    if offset:
        sql += " OFFSET %s"
        values.append(int(offset))

    return _pg_query(sql, tuple(values) if values else None)


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
        raise RuntimeError(f"Neon API {e.code}: {body}") from e


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
        raise RuntimeError(f"Neon RPC {e.code}: {body}") from e


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
    # psycopg2 returns Decimal for AVG / numeric columns
    try:
        from decimal import Decimal
        if isinstance(obj, Decimal):
            return float(obj)
    except ImportError:
        pass
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


def error_from_exc(exc):
    """Map an exception to a safe HTTP response.

    SECURITY: never leak internal detail (SQL, driver messages, stack traces)
    to the client. BadRequest -> 400 with a generic 'invalid request'; anything
    else -> 500 with a generic message. Full detail is logged server-side with a
    correlation id the client can quote when reporting a problem (addendum B3).
    """
    import logging
    import uuid
    correlation_id = uuid.uuid4().hex[:12]
    if isinstance(exc, BadRequest):
        logging.getLogger('riskmap.api').warning(
            "bad request [%s]: %s", correlation_id, exc)
        return json_response(
            {'error': 'invalid request parameters', 'ref': correlation_id}, 400)
    logging.getLogger('riskmap.api').exception(
        "unhandled error [%s]", correlation_id)
    return json_response(
        {'error': 'internal server error', 'ref': correlation_id}, 500)


def send_response(handler, resp):
    """Send a json_response/error_response dict through a BaseHTTPRequestHandler."""
    handler.send_response(resp['statusCode'])
    for k, v in resp['headers'].items():
        handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(resp['body'].encode())
