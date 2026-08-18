# RiskMap — Multimodal Risk Intelligence

[![CI](https://github.com/AlfonsoCifuentes/riskmap/actions/workflows/ci.yml/badge.svg)](https://github.com/AlfonsoCifuentes/riskmap/actions/workflows/ci.yml)
[![Security](https://github.com/AlfonsoCifuentes/riskmap/actions/workflows/security.yml/badge.svg)](https://github.com/AlfonsoCifuentes/riskmap/actions/workflows/security.yml)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)

An **event-centric** platform that ingests heterogeneous open sources, deduplicates
and **fuses evidence into events**, geolocates them **with explicit uncertainty**,
scores **risk separately from confidence**, and exposes everything through a map,
dashboards, a deterministic **Replay Mode**, and reproducible reports.

Built to be **honest and verifiable**, not to sprinkle "AI / satellite / real-time"
on a demo. Every capability has code + data + an API + tests + a failure state +
documented limitations. Runs at a target cost of **€0/month**.

**Live demo:** https://riskmap-ai.vercel.app · **Live status:** [`/api/status`](https://riskmap-ai.vercel.app/api/status)

---

## What it actually does (with proof)

| Capability | Status | Proof |
|---|---|---|
| News/event ingestion (RSS · GDELT · GDACS) | LIVE | `/api/status` freshness, `/api/pipeline-runs` |
| Event fusion (evidence → events) | LIVE | `src/core/events.py`, `/api/v1/map/events` |
| Geolocation with uncertainty | LIVE | `src/core/geo.py` (`geo_precision`, `geo_confidence`) |
| Risk ≠ confidence (versioned engine) | LIVE | `src/core/risk.py`, "why this risk" factors |
| Relevance filter (no off-topic leaks) | LIVE | `src/core/relevance.py` |
| Data-quality scorecard | LIVE | `/api/data-quality` |
| System Observatory / pipeline runs | LIVE | `/api/pipeline-runs` |
| Deterministic Replay Mode (4 scenarios) | REPLAY | `/api/replay` |
| Satellite EO (Sentinel-2 Process API, FIRMS) | LIVE / DEGRADED | needs free CDSE/FIRMS keys, else graceful degrade |
| CV benchmarks (xView/xBD/SpaceNet) | BENCHMARK | `/api/cv-metrics` (published-baseline provenance) |
| AOI planner + capability guardrails | LIVE | rejects 10 m/px "tank detection" |
| Escalation forecasting (baseline) | BETA | `/api/forecast` (probability + baseline + Brier) |
| Alerts (dedupe/cooldown) + Safety Brief | BETA | `src/core/alerts.py`, `src/core/safety_brief.py` |
| Visual Intelligence (public cameras) | EXPERIMENTAL | `/api/cameras` (environmental only; no biometrics) |

Status labels are meaningful: `LIVE / REPLAY / BENCHMARK / BETA / EXPERIMENTAL / DEGRADED`.
**Nothing labelled LIVE is stale, heuristic, or replay.**

---

## Architecture

```
Sources (RSS · GDELT · GDACS · USGS · FIRMS · Copernicus)
   ↓ ingest            (GitHub Actions, scheduled)
raw articles
   ↓ relevance filter  (word-boundary + negative lexicon)
   ↓ dedup             (canonical URL · title hash · Jaccard · syndication)
   ↓ enrich            (classification · translation · geo · risk)
events  ← fusion       (semantic + spatiotemporal)
   ↓ risk engine v2    (severity/exposure/vulnerability vs confidence)
Neon Postgres
   ↓
Vercel serverless API  → map (GeoJSON) · dashboards · replay · forecast · reports
```

See [`docs/architecture.md`](docs/architecture.md), [`docs/pipeline.md`](docs/pipeline.md),
[`docs/data-model.md`](docs/data-model.md).

## Stack (all free tier)

- **Frontend/API:** Vercel Hobby (Python serverless) — kept ≤ 12 functions.
- **Database:** Neon Postgres (free).
- **Jobs:** GitHub Actions (ingest/enrich; imagery/CV).
- **AI:** Groq free tier via a **model registry** (`src/ai/model_registry.py`)
  with a local heuristic fallback → pipeline `DEGRADED`, never `FAILED`.
- **EO:** Copernicus Data Space (Sentinel-1/-2), NASA FIRMS — free keys.

## Data sources & licensing

See [`docs/data-sources.md`](docs/data-sources.md). RiskMap stores extracts +
links + attribution, never full-article republication.

## Live vs Replay

- **LIVE** reads current data from Neon; `/api/status` reports `data_age_seconds`
  and a freshness level (`healthy/warning/degraded/stale/offline`).
- **Replay Mode** (`/api/replay`) runs curated scenarios (wildfire/flood/
  earthquake/conflict) through the *real* pipeline with zero external deps, so the
  demo always works. Replay output is unambiguously flagged `REPLAY`.

## Tests

```bash
pip install -r requirements/dev.txt
pytest tests/unit            # 100+ fast unit tests, no DB required
ruff check api src/core tests/unit
```

Security regression tests include the exact SQL-injection payload that once hit
production, SSRF guards, and the relevance filter's off-topic cases.

## Local development

```bash
git clone https://github.com/AlfonsoCifuentes/riskmap
cd riskmap
cp .env.example .env          # fill DATABASE_URL; AI/EO keys optional
pip install -r requirements/pipeline.txt
python -m src.database.schema_init      # idempotent schema + v2 migration
python -m src.pipeline.ingest           # needs DATABASE_URL
python -m src.pipeline.enrich
```

Replay Mode and the unit tests need **no secrets**.

## Cost architecture (€0 target, €10 hard max)

Free tiers only; no paid providers, no persistent GPU, no always-on compute.
Heavy work is selective/scheduled/local/replay. See [`docs/adr/ADR-003`](docs/adr)
and the kill switches / daily limits in `.env.example`.

## Security

TLS verification enforced everywhere; SSRF guard on outbound fetches (moved out
of the request path); parameterized SQL with identifier allowlists; secrets kept
out of the repo (gitleaks in CI). See [`docs/threat-model.md`](docs/threat-model.md).

## Ethics

No face recognition, identity/person tracking, licence-plate reading, or
sensitive-trait inference — including in the experimental camera module. RiskMap
is **not an emergency authority**. See [`docs/ethics.md`](docs/ethics.md).

## Limitations (honest)

- News coverage is biased; the map can reflect media attention, which is why we
  separate risk from confidence and show geolocation uncertainty.
- Sentinel-2 (10 m/px) cannot detect individual vehicles; high-resolution object
  detection is demonstrated in **Replay/Benchmark** mode on public datasets.
- Forecasts are probabilistic early-warning estimates with baselines, not
  certainties.
- Some optional integrations (Copernicus, cameras, email) are `DEGRADED` until
  their free keys are configured.

## Provenance

This codebase was substantially rebuilt in a documented, append-only audit +
implementation pass — see `RISKMAP_MASTER_AUDIT_CLAUDE_IMPLEMENTATION_SPEC.md`
(`# Agent Independent Audit Addendum`, `# Implementation Log`).
