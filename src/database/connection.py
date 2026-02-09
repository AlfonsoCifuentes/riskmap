"""
RiskMap Database Abstraction Layer
===================================
Transparently supports SQLite (local dev) and Neon Postgres (production/Vercel).

Usage:
    from src.database.connection import get_db, get_conn

    db = get_db()           # singleton
    conn = db.get_conn()    # context-manager-ready connection
    db.execute("SELECT 1")  # quick helper
"""

import os
import re
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PH_RE = re.compile(r'\?')          # SQLite placeholder
_SERIAL_RE = re.compile(r'\bINTEGER PRIMARY KEY AUTOINCREMENT\b', re.I)
_BOOL_RE = re.compile(r"\bINTEGER\s+DEFAULT\s+([01])\b", re.I)


def _sqlite_to_pg(sql: str) -> str:
    """Minimal SQLite → Postgres DDL/DML translation."""
    sql = _SERIAL_RE.sub('SERIAL PRIMARY KEY', sql)
    sql = sql.replace('DATETIME', 'TIMESTAMPTZ')
    sql = sql.replace('datetime', 'TIMESTAMPTZ')
    # Replace ? → %s for parameterized queries
    sql = _PH_RE.sub('%s', sql)
    return sql


def _detect_backend() -> str:
    """Return 'postgres' or 'sqlite' based on DATABASE_URL env var."""
    url = os.getenv('DATABASE_URL', '')
    if url.startswith('postgres'):
        return 'postgres'
    return 'sqlite'


# ---------------------------------------------------------------------------
# Backend: SQLite
# ---------------------------------------------------------------------------

class _SQLiteBackend:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()

    def _conn(self):
        c = getattr(self._local, 'conn', None)
        if c is None:
            c = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA foreign_keys=ON")
            self._local.conn = c
        return c

    @contextmanager
    def get_conn(self):
        conn = self._conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute(self, sql: str, params: tuple = (), *, fetch: bool = False):
        with self.get_conn() as conn:
            cur = conn.execute(sql, params)
            if fetch:
                return [dict(r) for r in cur.fetchall()]
            return cur

    def executemany(self, sql: str, seq):
        with self.get_conn() as conn:
            conn.executemany(sql, seq)

    def execute_script(self, script: str):
        with self.get_conn() as conn:
            conn.executescript(script)

    @property
    def placeholder(self):
        return '?'

    @property
    def backend_name(self):
        return 'sqlite'

    def close(self):
        c = getattr(self._local, 'conn', None)
        if c:
            c.close()
            self._local.conn = None


# ---------------------------------------------------------------------------
# Backend: Postgres (Neon)
# ---------------------------------------------------------------------------

class _PostgresBackend:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._pool = None

    def _get_pool(self):
        if self._pool is None:
            try:
                import psycopg2
                from psycopg2 import pool as pg_pool
                from psycopg2.extras import RealDictCursor
                # Neon requires SSL
                self._pool = pg_pool.ThreadedConnectionPool(
                    minconn=1, maxconn=5,
                    dsn=self.dsn,
                    cursor_factory=RealDictCursor,
                    sslmode='require',
                )
                logger.info("✅ Neon Postgres pool created")
            except Exception as e:
                logger.error(f"❌ Postgres pool failed: {e}")
                raise
        return self._pool

    @contextmanager
    def get_conn(self):
        pool = self._get_pool()
        conn = pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)

    def execute(self, sql: str, params: tuple = (), *, fetch: bool = False):
        sql = _sqlite_to_pg(sql)
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            if fetch:
                return cur.fetchall()
            return cur

    def executemany(self, sql: str, seq):
        sql = _sqlite_to_pg(sql)
        with self.get_conn() as conn:
            cur = conn.cursor()
            import psycopg2.extras
            psycopg2.extras.execute_batch(cur, sql, seq)

    def execute_script(self, script: str):
        """Execute a multi-statement script (Postgres version)."""
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(script)

    @property
    def placeholder(self):
        return '%s'

    @property
    def backend_name(self):
        return 'postgres'

    def close(self):
        if self._pool:
            self._pool.closeall()
            self._pool = None


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_instance = None
_lock = threading.Lock()


def get_db():
    """Return the global DB backend (creates on first call)."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                backend = _detect_backend()
                if backend == 'postgres':
                    dsn = os.getenv('DATABASE_URL', '')
                    _instance = _PostgresBackend(dsn)
                    logger.info("🐘 Using Neon Postgres backend")
                else:
                    path = os.getenv('DATABASE_PATH', './data/geopolitical_intel.db')
                    url = os.getenv('DATABASE_URL', '')
                    if url.startswith('sqlite:///'):
                        path = url.replace('sqlite:///', '')
                    _instance = _SQLiteBackend(path)
                    logger.info(f"📁 Using SQLite backend: {path}")
    return _instance


def get_conn():
    """Shortcut: get_db().get_conn() context manager."""
    return get_db().get_conn()


def reset_db():
    """Close and reset singleton (for tests)."""
    global _instance
    if _instance:
        _instance.close()
    _instance = None
