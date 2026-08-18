# Threat model

All external content (articles, feeds, HTML, images, URLs) is **untrusted input**.

## Threats & mitigations

| Threat | Mitigation | Where |
|---|---|---|
| SQL injection | Parameterized queries + identifier allowlist regex | `api/_db.py` |
| Verbose error leakage | Generic message + correlation id; detail logged server-side | `api/_db.py::error_from_exc` |
| SSRF (fetching article URLs) | `is_safe_url` (reject private/loopback/link-local/metadata), redirect re-validation, https-only; fetch moved out of the request path to the worker | `api/_og_image.py` |
| TLS downgrade | Verified TLS everywhere; removed all `verify=False`/`CERT_NONE`/global unverified context | `_og_image.py`, `external_feeds.py`, `RISKMAP.py` |
| Prompt injection via news content | LLM inputs are delimited data, never instructions; outputs validated before use; a model registry avoids arbitrary model calls | `src/pipeline/enrich.py`, `src/ai/model_registry.py` |
| Secret exposure | Secrets never committed; `.env.example` sanitized; git history purged; gitleaks in CI + pre-commit | `.gitleaks.toml`, `docs/adr/ADR-007` |
| XSS from feed HTML | HTML stripped/entity-decoded before serving | `api/_db.py::strip_html` |
| Unbounded downloads | Byte caps + timeouts on outbound fetches | `api/_og_image.py` |
| Abusive alerts | Dedupe fingerprint + cooldown | `src/core/alerts.py` |

## Residual risk

History purge reduces exposure of previously-committed keys but is **not**
revocation — rotation remains recommended (ADR-007). SSRF DNS-rebinding is
mitigated by resolve-then-check but not fully eliminated; the fetch runs only in
the worker, not the public request path.
