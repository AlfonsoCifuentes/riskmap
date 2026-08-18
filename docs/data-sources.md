# Data sources & licensing

RiskMap stores **extracts + links + attribution**, never full-article
republication. Verify current terms before adding a source.

| Source | Purpose | Auth | Cost | Notes |
|---|---|---|---|---|
| RSS (Reuters, BBC, AJ, Guardian, GDACS, ReliefWeb, …) | News/event backbone | none | free | respect each outlet's terms |
| GDELT DOC API | Event coverage | none | free | flaky; resilient fetch + retry |
| GDACS | Disaster alerts | none | free | official hazard signals |
| USGS | Earthquakes | none | free | official feed |
| NASA FIRMS | Fire hotspots | free MAP_KEY | free | required key; else DEGRADED |
| Copernicus Data Space | Sentinel-1/-2 EO | free OAuth | free tier | Process API; else DEGRADED |
| Groq | LLM enrichment | free key | free tier | model registry + local fallback |
| Public cameras | Visual Intelligence (experimental) | varies | free | verify license per camera; environmental only |

## CV datasets (Replay/Benchmark only)

| Dataset | Task | Use |
|---|---|---|
| xView | overhead object detection | benchmark reference |
| xBD (xView2) | building damage | benchmark reference |
| SpaceNet | building footprints | benchmark reference |

These are **published-baseline references** used to demonstrate the evaluation
harness — not live detections and not RiskMap-trained state-of-the-art claims.

## Retention & cost

Raw article bodies are not kept indefinitely; imagery binaries live outside
Postgres; daily API/EO limits and kill switches are configurable in `.env`.
