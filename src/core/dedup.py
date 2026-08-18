"""Deduplication & syndication detection (spec §4.1 / §163 / §164, addendum B11).

An article is *evidence*; an event is the real-world incident. Ten papers
covering one airstrike must collapse to one event with source_count=10, not ten
"risks" inflating the heatmap. This module provides the layered dedup signals:

    1. canonical URL          (strip trackers, normalise)
    2. normalised-title hash   (exact/near-exact republication)
    3. token Jaccard similarity (semantic-ish, no embeddings needed)

plus independence estimation (distinct registrable domains) so five copies of
one wire story count as one independent source, not five.

Pure stdlib. Embedding-based similarity can be layered on later; this gives a
solid, testable baseline that runs anywhere.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Query params that are tracking noise, not content identity.
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "at_medium", "at_campaign", "fbclid", "gclid", "igshid", "mc_cid",
    "mc_eid", "ref", "ref_src", "spm", "cmpid", "ncid", "smid",
}

_WS_RE = re.compile(r"\s+")
_NONWORD_RE = re.compile(r"[^\w\s]", re.UNICODE)
# Very common headline stopwords across ES/EN — enough for title matching.
_STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "with",
    "el", "la", "los", "las", "un", "una", "de", "del", "y", "o", "en",
    "por", "para", "con", "se", "que",
}


def canonical_url(url: str) -> str:
    """Normalise a URL for identity comparison: lowercase host, drop default
    ports, strip tracking params, drop fragment, remove trailing slash."""
    if not url:
        return ""
    try:
        p = urlparse(url.strip())
    except ValueError:
        return url.strip()
    # Normalise scheme to https so http/https point at the same identity.
    scheme = "https"
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    netloc = host
    if p.port and p.port not in (80, 443):
        netloc = f"{host}:{p.port}"
    query = urlencode([
        (k, v) for k, v in parse_qsl(p.query, keep_blank_values=False)
        if k.lower() not in _TRACKING_PARAMS
    ])
    path = p.path.rstrip("/") or "/"
    return urlunparse((scheme, netloc, path, "", query, ""))


def registrable_domain(url: str) -> str:
    """Best-effort registrable domain (last two labels). Good enough to tell
    reuters.com from bbc.co.uk-ish cases for independence counting."""
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    # Handle common two-label public suffixes (co.uk, com.au, ...).
    if parts[-2] in {"co", "com", "org", "gov", "net", "ac"} and len(parts) >= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, drop stopwords."""
    if not title:
        return ""
    t = _NONWORD_RE.sub(" ", title.lower())
    t = _WS_RE.sub(" ", t).strip()
    tokens = [w for w in t.split(" ") if w and w not in _STOPWORDS]
    return " ".join(tokens)


def title_hash(title: str) -> str:
    norm = normalize_title(title)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest() if norm else ""


def token_set(text: str) -> set[str]:
    return set(normalize_title(text).split(" ")) - {""}


def jaccard(a: str, b: str) -> float:
    """Token Jaccard similarity of two titles/snippets (0..1)."""
    sa, sb = token_set(a), token_set(b)
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def is_duplicate(a: dict, b: dict, *, sim_threshold: float = 0.72) -> bool:
    """Decide whether two article-like dicts refer to the same report.

    Layers: identical canonical URL, identical normalised-title hash, or high
    title Jaccard similarity. Callers add a spatiotemporal window on top for
    *event* matching (see events.py)."""
    ua, ub = canonical_url(a.get("url", "")), canonical_url(b.get("url", ""))
    if ua and ua == ub:
        return True
    ha, hb = title_hash(a.get("title", "")), title_hash(b.get("title", ""))
    if ha and ha == hb:
        return True
    return jaccard(a.get("title", ""), b.get("title", "")) >= sim_threshold


def independent_source_count(articles: list[dict]) -> int:
    """Number of *distinct registrable domains* — five copies of one wire story
    on the same domain count once (spec §164)."""
    domains = {registrable_domain(a.get("url", "")) for a in articles if a.get("url")}
    domains.discard("")
    return len(domains)
