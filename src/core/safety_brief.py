"""Safety Brief generator (spec §19 / §102, addendum).

Builds a per-event brief that SEPARATES official guidance from RiskMap context,
and NEVER fabricates evacuation orders, shelters, road closures or medical
instructions. If no official guidance is available, it says so explicitly rather
than filling the gap with generated text.
"""
from __future__ import annotations


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    import math
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def build(event: dict, *, user_location: tuple | None = None,
          official_guidance: list | None = None) -> dict:
    """Assemble a Safety Brief.

    official_guidance: list of {authority, url, text, issued_at} from real
    sources (civil protection, USGS, GDACS, met agencies). Passed in — never
    invented here.
    """
    distance_km = None
    if user_location and event.get("latitude") is not None:
        distance_km = round(haversine_km(
            user_location[0], user_location[1],
            event["latitude"], event["longitude"]), 1)

    official = official_guidance or []
    status = {
        "event": event.get("title"),
        "category": event.get("category"),
        "risk_score": event.get("risk_score"),
        "risk_level": event.get("risk_level"),
        "confidence": event.get("confidence"),
        "distance_km": distance_km,
        "last_update": event.get("updated_at"),
    }

    return {
        "status": status,
        # Clearly delimited sections (spec §19): official vs our context.
        "official_guidance": (
            [{"authority": g.get("authority"), "url": g.get("url"),
              "text": g.get("text"), "issued_at": g.get("issued_at")}
             for g in official]
            if official else None
        ),
        "official_guidance_note": (
            None if official else
            "No official guidance found. RiskMap does not issue evacuation "
            "orders, shelter locations or medical instructions — consult local "
            "authorities and civil protection."
        ),
        "riskmap_context": _context_lines(event, distance_km),
        "disclaimer": ("RiskMap is not an emergency authority. This is contextual "
                       "situational awareness, not official instruction."),
    }


def _context_lines(event: dict, distance_km) -> list[str]:
    lines = []
    if distance_km is not None:
        lines.append(f"Estimated distance to event: ~{distance_km} km.")
    if event.get("risk_level"):
        lines.append(f"RiskMap risk level: {event['risk_level']} "
                     f"(confidence {event.get('confidence', 'n/a')}).")
    if event.get("source_count"):
        lines.append(f"Corroborated by {event.get('independent_source_count', 1)} "
                     f"independent source(s).")
    if not lines:
        lines.append("Limited structured context available for this event.")
    return lines
