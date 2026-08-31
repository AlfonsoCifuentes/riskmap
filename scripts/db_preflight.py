"""
RiskMap DB Preflight
=====================
Fails fast when the pipeline database is unreachable, *before* a workflow
spends minutes installing torch/ultralytics only to die on the first query.

Emits a GitHub Actions ``::error::`` annotation naming the actual cause, so a
quota exhaustion is not mistaken for a code regression.

Usage:
    python scripts/db_preflight.py
"""

import os
import sys

CONNECT_TIMEOUT = 15

# Substrings that mark a provider-side capacity/billing stop rather than an
# outage or a bad DSN — these need a plan change or a quota reset, not a fix.
_QUOTA_MARKERS = (
    'data transfer quota',
    'exceeded the',
    'quota',
    'compute time',
    'limit exceeded',
)


def main() -> int:
    dsn = os.environ.get('DATABASE_URL', '').strip()
    if not dsn:
        print('::error::DATABASE_URL is not set — the pipeline has no database to write to.')
        return 1

    try:
        import psycopg2
    except ImportError:
        print('::error::psycopg2 is not installed; cannot run the database preflight.')
        return 1

    try:
        conn = psycopg2.connect(dsn, sslmode='require', connect_timeout=CONNECT_TIMEOUT)
    except psycopg2.OperationalError as exc:
        msg = ' '.join(str(exc).split())
        print(f'::error::Database unreachable: {msg}')
        if any(m in msg.lower() for m in _QUOTA_MARKERS):
            print(
                '::error::This is a provider quota stop, not a code failure. The '
                'pipeline cannot run until the quota resets or the plan is upgraded.'
            )
        return 1

    conn.close()
    print('✅ Database reachable')
    return 0


if __name__ == '__main__':
    sys.exit(main())
