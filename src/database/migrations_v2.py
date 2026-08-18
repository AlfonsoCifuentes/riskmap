"""Event-centric v2 migration DDL (spec §55, addendum B11/B14).

Additive and idempotent: new tables use CREATE TABLE IF NOT EXISTS; new columns
are added via the caller's column-if-missing helper. Nothing here drops or
rewrites existing data, so it is safe to run on every pipeline start in
GitHub Actions.

Two dialects are provided (Postgres for Neon, SQLite for local/tests) because
the project supports both (§87.4). Keep them in lock-step.
"""
from __future__ import annotations

# --- New columns on existing tables ---------------------------------------
# {table: [(column, postgres_type, sqlite_type), ...]}
V2_COLUMNS: dict[str, list[tuple[str, str, str]]] = {
    "unified_articles": [
        ("geo_method", "TEXT", "TEXT"),
        ("geo_precision", "TEXT", "TEXT"),
        ("geo_precision_m", "REAL", "REAL"),
        ("geo_confidence", "REAL", "REAL"),
        ("geo_is_fallback", "BOOLEAN", "INTEGER"),
        ("risk_engine_version", "TEXT", "TEXT"),
        ("event_confidence", "REAL", "REAL"),
        ("source_domain", "TEXT", "TEXT"),
        # Preserve originals — translation must never overwrite (spec §4.3).
        ("title_original", "TEXT", "TEXT"),
        ("summary_original", "TEXT", "TEXT"),
        ("language_original", "TEXT", "TEXT"),
    ],
    "events": [
        ("risk_score", "REAL", "REAL"),
        ("risk_level", "TEXT", "TEXT"),
        ("confidence_score", "REAL", "REAL"),
        ("severity_normalized", "REAL", "REAL"),
        ("exposure", "REAL", "REAL"),
        ("vulnerability", "REAL", "REAL"),
        ("geo_method", "TEXT", "TEXT"),
        ("geo_precision", "TEXT", "TEXT"),
        ("geo_precision_m", "REAL", "REAL"),
        ("geo_confidence", "REAL", "REAL"),
        ("geo_is_fallback", "BOOLEAN", "INTEGER"),
        ("risk_engine_version", "TEXT", "TEXT"),
        ("source_count", "INTEGER", "INTEGER"),
        ("independent_source_count", "INTEGER", "INTEGER"),
        ("status", "TEXT", "TEXT"),
        ("first_seen_at", "TIMESTAMPTZ", "TIMESTAMP"),
        ("last_evidence_at", "TIMESTAMPTZ", "TIMESTAMP"),
        ("risk_factors_json", "TEXT", "TEXT"),
    ],
}

# --- New tables ------------------------------------------------------------
_EVENT_EVIDENCE_PG = """
CREATE TABLE IF NOT EXISTS event_evidence (
    id              SERIAL PRIMARY KEY,
    event_id        INTEGER REFERENCES events(id) ON DELETE CASCADE,
    evidence_type   TEXT NOT NULL,           -- article | official | firms | eo | cv | camera
    article_id      INTEGER,
    source          TEXT,
    source_url      TEXT,
    source_domain   TEXT,
    published_at    TIMESTAMPTZ,
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    trust_weight    REAL DEFAULT 0.5,
    payload_json    TEXT
);
CREATE INDEX IF NOT EXISTS idx_evev_event ON event_evidence (event_id);
CREATE INDEX IF NOT EXISTS idx_evev_type ON event_evidence (evidence_type);
"""

_EVENT_EVIDENCE_SQLITE = """
CREATE TABLE IF NOT EXISTS event_evidence (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER REFERENCES events(id) ON DELETE CASCADE,
    evidence_type   TEXT NOT NULL,
    article_id      INTEGER,
    source          TEXT,
    source_url      TEXT,
    source_domain   TEXT,
    published_at    TIMESTAMP,
    ingested_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trust_weight    REAL DEFAULT 0.5,
    payload_json    TEXT
);
CREATE INDEX IF NOT EXISTS idx_evev_event ON event_evidence (event_id);
CREATE INDEX IF NOT EXISTS idx_evev_type ON event_evidence (evidence_type);
"""

_PIPELINE_RUNS_PG = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              SERIAL PRIMARY KEY,
    stage           TEXT NOT NULL,           -- ingest | enrich | fuse | imagery | detect
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    status          TEXT DEFAULT 'running',  -- running | success | failed | degraded
    items_in        INTEGER DEFAULT 0,
    items_out       INTEGER DEFAULT 0,
    errors          INTEGER DEFAULT 0,
    cost_estimate_eur REAL DEFAULT 0,
    git_sha         TEXT,
    notes           TEXT
);
CREATE INDEX IF NOT EXISTS idx_prun_stage ON pipeline_runs (stage, started_at DESC);
"""

_PIPELINE_RUNS_SQLITE = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stage           TEXT NOT NULL,
    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at     TIMESTAMP,
    status          TEXT DEFAULT 'running',
    items_in        INTEGER DEFAULT 0,
    items_out       INTEGER DEFAULT 0,
    errors          INTEGER DEFAULT 0,
    cost_estimate_eur REAL DEFAULT 0,
    git_sha         TEXT,
    notes           TEXT
);
CREATE INDEX IF NOT EXISTS idx_prun_stage ON pipeline_runs (stage, started_at DESC);
"""

_PROVIDER_HEALTH_PG = """
CREATE TABLE IF NOT EXISTS provider_health (
    id              SERIAL PRIMARY KEY,
    provider        TEXT NOT NULL,
    checked_at      TIMESTAMPTZ DEFAULT NOW(),
    status          TEXT,                    -- healthy | degraded | failed | rate_limited
    latency_ms      INTEGER,
    detail          TEXT
);
CREATE INDEX IF NOT EXISTS idx_phealth_provider ON provider_health (provider, checked_at DESC);
"""

_PROVIDER_HEALTH_SQLITE = """
CREATE TABLE IF NOT EXISTS provider_health (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider        TEXT NOT NULL,
    checked_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status          TEXT,
    latency_ms      INTEGER,
    detail          TEXT
);
CREATE INDEX IF NOT EXISTS idx_phealth_provider ON provider_health (provider, checked_at DESC);
"""

_DQ_SNAPSHOTS_PG = """
CREATE TABLE IF NOT EXISTS data_quality_snapshots (
    id              SERIAL PRIMARY KEY,
    captured_at     TIMESTAMPTZ DEFAULT NOW(),
    dimension       TEXT NOT NULL,           -- completeness | validity | uniqueness | timeliness | provenance
    metric          TEXT NOT NULL,
    value           REAL,
    dataset         TEXT
);
CREATE INDEX IF NOT EXISTS idx_dq_captured ON data_quality_snapshots (captured_at DESC);
"""

_DQ_SNAPSHOTS_SQLITE = """
CREATE TABLE IF NOT EXISTS data_quality_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dimension       TEXT NOT NULL,
    metric          TEXT NOT NULL,
    value           REAL,
    dataset         TEXT
);
CREATE INDEX IF NOT EXISTS idx_dq_captured ON data_quality_snapshots (captured_at DESC);
"""

V2_TABLES_PG = [_EVENT_EVIDENCE_PG, _PIPELINE_RUNS_PG, _PROVIDER_HEALTH_PG, _DQ_SNAPSHOTS_PG]
V2_TABLES_SQLITE = [_EVENT_EVIDENCE_SQLITE, _PIPELINE_RUNS_SQLITE,
                    _PROVIDER_HEALTH_SQLITE, _DQ_SNAPSHOTS_SQLITE]

# Tables the v2 migration guarantees to exist (for schema_init verification).
V2_EXPECTED_TABLES = {
    "event_evidence", "pipeline_runs", "provider_health", "data_quality_snapshots",
}
