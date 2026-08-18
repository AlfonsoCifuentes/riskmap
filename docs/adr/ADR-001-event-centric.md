# ADR-001 — Event-centric model

- **Status:** Accepted
- **Context:** The legacy system treated every article as an independent "risk",
  so N reports of one incident became N map points, inflating the heatmap into a
  media-attention map.
- **Decision:** Model *articles as evidence* and *events as incidents*. Fuse
  evidence into events via dedup (canonical URL / title hash / Jaccard) plus a
  spatiotemporal window; count independent domains, not copies.
- **Consequence:** One incident → one event with `source_count` and higher
  confidence. Enables an evidence graph and "why this risk".
