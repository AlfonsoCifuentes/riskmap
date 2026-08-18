"""Event fusion — group evidence (articles/signals) into real-world events.

Spec §4.9 / §97 / §98, addendum B11. An event aggregates evidence that refers to
the same incident, matched by:

    semantic duplicate (dedup.is_duplicate)   -- same report / republication
    OR (same category AND spatial proximity AND temporal proximity)

so distinct reports of one incident fuse, while two separate attacks in the same
city on different days stay separate (merge/split correctness).

Pure stdlib; distance via haversine. The pipeline feeds article-like dicts:
    {url, title, category, latitude, longitude, published_at (datetime|None)}
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

from src.core import dedup

# Default fusion window.
DEFAULT_RADIUS_KM = 75.0
DEFAULT_TIME_WINDOW = timedelta(hours=48)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2)
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _same_place(a: dict, b: dict, radius_km: float) -> bool:
    la, lo = a.get("latitude"), a.get("longitude")
    lb, lob = b.get("latitude"), b.get("longitude")
    if None in (la, lo, lb, lob):
        return False
    return haversine_km(la, lo, lb, lob) <= radius_km


def _same_time(a: dict, b: dict, window: timedelta) -> bool:
    ta, tb = a.get("published_at"), b.get("published_at")
    if not isinstance(ta, datetime) or not isinstance(tb, datetime):
        # Without timestamps we don't block fusion, but we don't assert it.
        return True
    return abs(ta - tb) <= window


def same_event(a: dict, b: dict, *, radius_km: float = DEFAULT_RADIUS_KM,
               time_window: timedelta = DEFAULT_TIME_WINDOW) -> bool:
    """True if two evidence items belong to the same event."""
    if dedup.is_duplicate(a, b):
        return True
    if a.get("category") and a.get("category") == b.get("category"):
        if _same_place(a, b, radius_km) and _same_time(a, b, time_window):
            return True
    return False


def fuse(articles: list[dict], *, radius_km: float = DEFAULT_RADIUS_KM,
         time_window: timedelta = DEFAULT_TIME_WINDOW) -> list[dict]:
    """Cluster evidence into events (single-link agglomeration).

    Returns a list of event dicts:
        {
          "evidence": [article, ...],
          "source_count": int,                 # total evidence items
          "independent_source_count": int,     # distinct domains
          "category": str | None,
          "representative": article,           # earliest / most-sourced
        }
    """
    clusters: list[list[dict]] = []
    for art in articles:
        placed = False
        for cluster in clusters:
            if any(same_event(art, member, radius_km=radius_km,
                              time_window=time_window) for member in cluster):
                cluster.append(art)
                placed = True
                break
        if not placed:
            clusters.append([art])

    events = []
    for cluster in clusters:
        rep = _representative(cluster)
        cats = [c.get("category") for c in cluster if c.get("category")]
        events.append({
            "evidence": cluster,
            "source_count": len(cluster),
            "independent_source_count": dedup.independent_source_count(cluster),
            "category": cats[0] if cats else None,
            "representative": rep,
        })
    return events


def _representative(cluster: list[dict]) -> dict:
    """Pick the evidence item that best represents the event: earliest with a
    timestamp, else the first."""
    dated = [c for c in cluster if isinstance(c.get("published_at"), datetime)]
    if dated:
        return min(dated, key=lambda c: c["published_at"])
    return cluster[0]
