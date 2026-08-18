# ADR-008 — One dispatcher for the serverless function budget

- **Status:** Accepted
- **Context:** Vercel Hobby (the €0 plan) caps a deployment at **12 Serverless
  Functions**. The project was already at 12; each new endpoint file made the
  deployment exceed the cap and fail (build succeeded, deploy rejected), so
  production silently stayed on an old commit.
- **Decision:** Consolidate v2 endpoints (map/events, replay, data-quality,
  pipeline-runs, pipeline-status, cv-metrics, forecast, report, cameras) into a
  single dispatcher `api/v1.py`, routed by a `?route=` query param injected via
  `vercel.json` rewrites (with a path fallback). Dropped `index` and standalone
  `pipeline-status` functions.
- **Consequence:** 11 functions total, room to spare; all v2 capabilities live on
  the €0 plan. Adding an endpoint = a new route in the dispatcher + one rewrite,
  not a new function.
