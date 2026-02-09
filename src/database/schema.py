"""
RiskMap Database Schema
========================
Postgres-compatible schema that also works on SQLite.
Covers: unified_articles, conflict events, locations, AOIs, imagery, CV detections.
"""

# ------------------------------------------------------------------
# Postgres DDL  (run via schema_init.py or GitHub Actions migration)
# ------------------------------------------------------------------

POSTGRES_SCHEMA = """
-- ============================================================
-- 1. UNIFIED ARTICLES  (existing columns kept, new columns added)
-- ============================================================
CREATE TABLE IF NOT EXISTS unified_articles (
    id                      SERIAL PRIMARY KEY,
    title                   TEXT,
    content                 TEXT,
    summary                 TEXT,
    url                     TEXT,
    source                  TEXT,
    published_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    -- i18N
    language                VARCHAR(10) DEFAULT 'es',
    original_language       VARCHAR(10),
    is_translated           SMALLINT DEFAULT 0,

    -- Geopolitical
    geopolitical_relevance  SMALLINT DEFAULT 0,
    risk_level              VARCHAR(20),
    risk_score              REAL,
    conflict_type           VARCHAR(50),
    conflict_intensity      REAL,

    -- Location
    country                 TEXT,
    region                  TEXT,
    latitude                REAL,
    longitude               REAL,
    location_extracted      TEXT,
    coordinates_source      VARCHAR(30),

    -- Image
    image_url               TEXT,
    original_image_url      TEXT,
    cv_analysis             TEXT,
    satellite_image_url     TEXT,
    has_image               SMALLINT DEFAULT 0,

    -- AI / ML
    ai_importance           REAL,
    ai_summary              TEXT,
    auto_generated_summary  TEXT,
    ai_sentiment            VARCHAR(20),
    ai_tags                 TEXT,
    enrichment_status       VARCHAR(30),

    -- Entity Extraction
    entities_json           TEXT,
    extracted_entities_json  TEXT,
    countries_involved      TEXT,
    politicians_involved    TEXT,

    -- Analysis
    sentiment_score         REAL,
    quality_score           REAL,
    processing_confidence   REAL,
    enrichment_confidence   REAL,

    -- Metadata
    source_country          VARCHAR(100),
    source_bias             VARCHAR(20),
    source_credibility      REAL,
    metadata_json           TEXT,
    processing_notes        TEXT,

    -- NEW: event linkage
    event_id                INTEGER
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ua_geo_rel ON unified_articles (geopolitical_relevance);
CREATE INDEX IF NOT EXISTS idx_ua_published ON unified_articles (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_ua_country ON unified_articles (country);
CREATE INDEX IF NOT EXISTS idx_ua_risk ON unified_articles (risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_ua_event ON unified_articles (event_id);


-- ============================================================
-- 2. CONFLICT / DISASTER EVENTS  (aggregated from articles)
-- ============================================================
CREATE TABLE IF NOT EXISTS events (
    id              SERIAL PRIMARY KEY,
    event_type      VARCHAR(20) NOT NULL,       -- 'conflict' | 'disaster'
    subtype         VARCHAR(50),                -- 'armed_conflict','flood','wildfire',…
    title           TEXT,
    severity        REAL DEFAULT 0,             -- 0-1 normalised
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    last_updated    TIMESTAMPTZ DEFAULT NOW(),
    explanation     TEXT,                        -- AI-generated summary
    metadata_json   TEXT
);

CREATE INDEX IF NOT EXISTS idx_ev_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_ev_severity ON events (severity DESC);


-- ============================================================
-- 3. EVENT LOCATIONS  (one event can span multiple coords)
-- ============================================================
CREATE TABLE IF NOT EXISTS event_locations (
    id              SERIAL PRIMARY KEY,
    event_id        INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    latitude        REAL NOT NULL,
    longitude       REAL NOT NULL,
    name            TEXT,
    precision_km    REAL,                       -- radius of uncertainty
    source          VARCHAR(30),                -- 'article','geocoder','satellite'
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_el_event ON event_locations (event_id);
CREATE INDEX IF NOT EXISTS idx_el_coords ON event_locations (latitude, longitude);


-- ============================================================
-- 4. AREAS OF INTEREST  (for satellite acquisition & heatmap)
-- ============================================================
CREATE TABLE IF NOT EXISTS aois (
    id              SERIAL PRIMARY KEY,
    name            TEXT,
    event_id        INTEGER REFERENCES events(id) ON DELETE SET NULL,
    bbox_json       TEXT NOT NULL,               -- [west,south,east,north]
    priority        REAL DEFAULT 0.5,
    active          SMALLINT DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aoi_active ON aois (active, priority DESC);


-- ============================================================
-- 5. IMAGES  (satellite, webcam, news — compressed store)
-- ============================================================
CREATE TABLE IF NOT EXISTS images (
    id              SERIAL PRIMARY KEY,
    source_type     VARCHAR(20) NOT NULL,        -- 'sentinel','landsat','webcam','news','firms','modis'
    source_url      TEXT,
    aoi_id          INTEGER REFERENCES aois(id) ON DELETE SET NULL,
    event_id        INTEGER REFERENCES events(id) ON DELETE SET NULL,
    latitude        REAL,
    longitude       REAL,
    captured_at     TIMESTAMPTZ,
    stored_at       TIMESTAMPTZ DEFAULT NOW(),

    -- Compressed image data
    image_data      BYTEA,                       -- WebP-compressed thumbnail/full
    image_format    VARCHAR(10) DEFAULT 'webp',
    image_width     INTEGER,
    image_height    INTEGER,
    image_size_kb   REAL,

    -- Metadata
    cloud_cover     REAL,
    resolution_m    REAL,
    band_info       TEXT,                         -- JSON: which bands
    metadata_json   TEXT,

    -- Retention
    is_latest       SMALLINT DEFAULT 1,           -- only keep latest per AOI+source
    expires_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_img_aoi ON images (aoi_id, is_latest);
CREATE INDEX IF NOT EXISTS idx_img_event ON images (event_id);
CREATE INDEX IF NOT EXISTS idx_img_source ON images (source_type);
CREATE INDEX IF NOT EXISTS idx_img_captured ON images (captured_at DESC);


-- ============================================================
-- 6. CV DETECTIONS  (YOLO / classification results on images)
-- ============================================================
CREATE TABLE IF NOT EXISTS detections (
    id              SERIAL PRIMARY KEY,
    image_id        INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    event_id        INTEGER REFERENCES events(id) ON DELETE SET NULL,
    detector        VARCHAR(30) NOT NULL,        -- 'yolov8','resnet','custom'
    detection_type  VARCHAR(20) NOT NULL,        -- 'indicator' | 'signal'

    -- Results
    classes_json    TEXT NOT NULL,                -- [{"class":"tank","score":0.91,"bbox":[x,y,w,h]}, …]
    top_class       VARCHAR(50),
    top_score       REAL,
    total_objects    INTEGER DEFAULT 0,

    -- Context
    is_conflict     SMALLINT DEFAULT 0,
    is_disaster     SMALLINT DEFAULT 0,
    explanation     TEXT,
    detected_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_det_image ON detections (image_id);
CREATE INDEX IF NOT EXISTS idx_det_type ON detections (detection_type);
CREATE INDEX IF NOT EXISTS idx_det_conflict ON detections (is_conflict);
CREATE INDEX IF NOT EXISTS idx_det_disaster ON detections (is_disaster);


-- ============================================================
-- 7. SIGNALS LOG  (human-readable event+detection summary)
-- ============================================================
CREATE TABLE IF NOT EXISTS signals (
    id              SERIAL PRIMARY KEY,
    event_id        INTEGER REFERENCES events(id) ON DELETE CASCADE,
    detection_id    INTEGER REFERENCES detections(id) ON DELETE SET NULL,
    image_id        INTEGER REFERENCES images(id) ON DELETE SET NULL,
    signal_type     VARCHAR(20) NOT NULL,        -- 'conflict_indicator' | 'disaster_signal'
    severity        REAL,
    title           TEXT,
    description     TEXT,
    latitude        REAL,
    longitude       REAL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sig_event ON signals (event_id);
CREATE INDEX IF NOT EXISTS idx_sig_type ON signals (signal_type);


-- ============================================================
-- 8. EXISTING SUPPORTING TABLES (preserved for compatibility)
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id              SERIAL PRIMARY KEY,
    alert_type      VARCHAR(50),
    title           TEXT,
    message         TEXT,
    severity        VARCHAR(20),
    latitude        REAL,
    longitude       REAL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    resolved        SMALLINT DEFAULT 0,
    metadata_json   TEXT
);

CREATE TABLE IF NOT EXISTS conflict_zones (
    id              SERIAL PRIMARY KEY,
    name            TEXT,
    country         TEXT,
    region          TEXT,
    latitude        REAL,
    longitude       REAL,
    radius_km       REAL,
    risk_level      VARCHAR(20),
    active          SMALLINT DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    metadata_json   TEXT
);

CREATE TABLE IF NOT EXISTS enrichment_log (
    id              SERIAL PRIMARY KEY,
    article_id      INTEGER,
    enrichment_type VARCHAR(50),
    status          VARCHAR(20),
    details         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gpr_index (
    id              SERIAL PRIMARY KEY,
    date            DATE,
    gpr_value       REAL,
    country         VARCHAR(100),
    source          VARCHAR(30),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
"""


# ------------------------------------------------------------------
# SQLite DDL  (subset — keeps existing table, adds new ones)
# ------------------------------------------------------------------

SQLITE_SCHEMA = """
-- New tables for SQLite local dev (unified_articles already exists)

CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      TEXT NOT NULL,
    subtype         TEXT,
    title           TEXT,
    severity        REAL DEFAULT 0,
    started_at      DATETIME,
    ended_at        DATETIME,
    last_updated    DATETIME DEFAULT CURRENT_TIMESTAMP,
    explanation     TEXT,
    metadata_json   TEXT
);

CREATE TABLE IF NOT EXISTS event_locations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    latitude        REAL NOT NULL,
    longitude       REAL NOT NULL,
    name            TEXT,
    precision_km    REAL,
    source          TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aois (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT,
    event_id        INTEGER REFERENCES events(id) ON DELETE SET NULL,
    bbox_json       TEXT NOT NULL,
    priority        REAL DEFAULT 0.5,
    active          INTEGER DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS images (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type     TEXT NOT NULL,
    source_url      TEXT,
    aoi_id          INTEGER REFERENCES aois(id) ON DELETE SET NULL,
    event_id        INTEGER REFERENCES events(id) ON DELETE SET NULL,
    latitude        REAL,
    longitude       REAL,
    captured_at     DATETIME,
    stored_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_data      BLOB,
    image_format    TEXT DEFAULT 'webp',
    image_width     INTEGER,
    image_height    INTEGER,
    image_size_kb   REAL,
    cloud_cover     REAL,
    resolution_m    REAL,
    band_info       TEXT,
    metadata_json   TEXT,
    is_latest       INTEGER DEFAULT 1,
    expires_at      DATETIME
);

CREATE TABLE IF NOT EXISTS detections (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id        INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    event_id        INTEGER REFERENCES events(id) ON DELETE SET NULL,
    detector        TEXT NOT NULL,
    detection_type  TEXT NOT NULL,
    classes_json    TEXT NOT NULL,
    top_class       TEXT,
    top_score       REAL,
    total_objects    INTEGER DEFAULT 0,
    is_conflict     INTEGER DEFAULT 0,
    is_disaster     INTEGER DEFAULT 0,
    explanation     TEXT,
    detected_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER REFERENCES events(id) ON DELETE CASCADE,
    detection_id    INTEGER REFERENCES detections(id) ON DELETE SET NULL,
    image_id        INTEGER REFERENCES images(id) ON DELETE SET NULL,
    signal_type     TEXT NOT NULL,
    severity        REAL,
    title           TEXT,
    description     TEXT,
    latitude        REAL,
    longitude       REAL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Add event_id column to unified_articles if missing
-- (handled programmatically in schema_init.py)
"""
