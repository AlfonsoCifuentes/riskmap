# ADR-005 — Risk is not confidence

- **Status:** Accepted
- **Context:** The legacy "risk score" was a keyword sum presented as if it were a
  probability, conflating how bad an incident is with how sure we are.
- **Decision:** Risk Engine v2 (`src/core/risk.py`) computes **risk** from
  severity/exposure/vulnerability and **confidence** separately from evidence
  signals (independent sources, official corroboration, geo quality, recency).
  Both are versioned (`risk_engine_version`); "why this risk" exposes structured
  factors, never the LLM's chain-of-thought.
- **Consequence:** UI can show `Risk 82/HIGH` and `Confidence 61/MEDIUM`
  independently; a single uncorroborated report is high-risk / low-confidence.
