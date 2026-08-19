# Legacy

## `RISKMAP.py` (16,433 lines)

The original monolithic application: a single `RiskMapUnifiedApplication` class
that stood up a Flask server plus two Dash dashboards and ran every pipeline
stage in background threads inside one process.

**It is not part of the production system.** Production is a full rewrite:

| Legacy capability (RISKMAP.py) | v2 replacement |
| --- | --- |
| News ingestion (`_run_continuous_ingestion`) | `src/pipeline/ingest.py` (GitHub Actions, every 2h) |
| NLP enrichment / analysis (`_run_continuous_analysis`) | `src/pipeline/enrich.py` |
| Translation (`_translate_english_articles_direct`) | `enrich.py` (Groq translation) |
| Geocoding (`_get_coordinates_for_location`) | `src/core/geo.py` + AI geo in `enrich.py` |
| AI analysis (`_generate_groq_analysis`, `_call_ai_service`) | `src/ai/model_registry.py` |
| Image scraping (`_scrape_article_image`, `extract_image_from_url`) | `api/_og_image.py` + `src/pipeline/acquire_images.py` (SSRF-guarded, out of the request path) |
| Satellite/EO (`_initialize_satellite_system`) | `src/pipeline/acquire_images.py`, `/api/images`, `/api/image` |
| CCTV (`register_cctv_routes`) | `src/core/cameras.py` + `/api/cameras` (EXPERIMENTAL) |
| Flask routes / REST API (`_setup_flask_routes`) | `api/*` Vercel serverless (dispatcher `api/v1.py`) |
| Historical Dash dashboard | `/api/history` + `public/historical-analysis.html` (Chart.js) |
| Multivariate Dash dashboard | `public/trends-analysis.html`, `public/data-intelligence.html` |

Kept here (not deleted) for reference and because a line-by-line extraction
audit of the full monolith is a standalone task. Nothing in the repo imports it;
`start_riskmap.py` can still launch it locally from this path.
