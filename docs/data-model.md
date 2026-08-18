# Data model

Canonical tables (see `src/database/schema.py` + `src/database/migrations_v2.py`).

## unified_articles (evidence)
Core fields plus v2 additions:
`geo_method, geo_precision, geo_precision_m, geo_confidence, geo_is_fallback,
risk_engine_version, event_confidence, source_domain,
title_original, summary_original, language_original` (originals preserved —
translation never overwrites), `event_id` (link to fused event).

## events (incidents)
`event_type, subtype, title, severity` plus v2:
`risk_score, risk_level, confidence_score, severity_normalized, exposure,
vulnerability, geo_* , risk_engine_version, source_count,
independent_source_count, status (lifecycle), first_seen_at, last_evidence_at,
risk_factors_json`.

## event_locations
`event_id, latitude, longitude, name, precision_km` — one event may have several.

## event_evidence (evidence graph)
`event_id, evidence_type, article_id, source, source_url, source_domain,
published_at, trust_weight, payload_json`.

## Observability
- `pipeline_runs` — one row per stage run (stage, status, items_in/out, git_sha).
- `provider_health` — external provider checks.
- `data_quality_snapshots` — quality metrics over time.

Migrations are **additive and idempotent** (`schema_init` runs them every job),
supporting both Postgres (Neon) and SQLite (local/tests).
