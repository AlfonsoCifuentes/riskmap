# ADR-003 — Free-first infrastructure (€0 target)

- **Status:** Accepted
- **Context:** RiskMap is a portfolio project with a non-negotiable budget:
  target €0/month, hard max €10/month.
- **Decision:** Free tiers only — Vercel Hobby, Neon free, GitHub Actions, Groq
  free tier, Copernicus/FIRMS free keys. No paid providers, no persistent GPU, no
  always-on compute. Expensive work becomes selective/scheduled/local/replay.
  Missing optional keys degrade a capability (`DEGRADED`) instead of failing.
- **Consequence:** Every capability is demonstrable at €0. Heavy CV is Replay/
  Benchmark; EO is selective and gated by the AOI planner; daily limits + kill
  switches live in `.env`.
