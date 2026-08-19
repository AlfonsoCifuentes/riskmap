"""Visual Intelligence — Experimental (spec §89, addendum).

Environmental visual signals from a small set of curated PUBLIC cameras. This is
explicitly EXPERIMENTAL and NOT part of the critical pipeline: a single camera
never confirms an event; a visual signal only gains confidence through temporal
persistence and cross-source corroboration.

Hard ethical boundaries (spec §89.7 / docs/ethics.md) — NOT implemented here and
must never be added: face recognition, identity/person tracking, licence-plate
recognition, biometric or sensitive-trait inference, "suspicious person"
classification. Detections are limited to environmental phenomena.

Pure logic + a data registry; frame capture / CV inference plug in as workers.
"""
from __future__ import annotations

import json
import os

REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "cameras", "registry.json",
)

# Detections we allow (environmental only).
ALLOWED_DETECTIONS = {
    "smoke", "fire", "flood", "high_water", "road_obstruction", "debris",
    "ash_plume", "snow_obstruction", "low_visibility", "high_crowd_density",
}
# Explicitly forbidden — referenced by tests to lock the boundary.
FORBIDDEN_DETECTIONS = {
    "face_recognition", "identity", "person_tracking", "license_plate",
    "biometric", "ethnicity", "suspicious_person", "political_affiliation",
}

HEALTH_STATES = ("ONLINE", "DEGRADED", "OFFLINE", "BLOCKED", "UNKNOWN")


def load_registry() -> list[dict]:
    if not os.path.isfile(REGISTRY_PATH):
        return []
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        data: list[dict] = json.load(f).get("cameras", [])
        return data


def health_state(*, http_ok: bool, content_is_image: bool,
                 consecutive_failures: int, last_success_age_s: float | None,
                 sampling_interval_s: int) -> str:
    """Derive a camera health state. HTTP 200 alone is NOT healthy (spec §92)."""
    if not http_ok:
        return "OFFLINE" if consecutive_failures >= 3 else "DEGRADED"
    if not content_is_image:
        return "BLOCKED"
    # Even with 200 + image, stale captures are DEGRADED, not ONLINE.
    if last_success_age_s is not None and last_success_age_s > 5 * sampling_interval_s:
        return "DEGRADED"
    return "ONLINE"


def next_sampling_interval(*, base_interval_s: int, anomaly_active: bool,
                           persisting: bool) -> int:
    """Adaptive sampling (spec §89.5): slow by default, speed up on anomaly."""
    if anomaly_active and persisting:
        return max(10, base_interval_s // 6)
    if anomaly_active:
        return max(15, base_interval_s // 4)
    return base_interval_s


def temporal_confirmation(confidences: list[float], *, threshold: float = 0.7,
                          min_persistent: int = 3) -> dict:
    """A single frame is not enough (spec §89.8). Confirm only if the signal
    persists across consecutive frames above threshold."""
    streak = 0
    best = 0
    for c in confidences:
        if c >= threshold:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    confirmed = best >= min_persistent
    return {
        "confirmed": confirmed,
        "max_streak": best,
        "state": "persistent_candidate" if confirmed else "transient_or_noise",
    }


def corroboration(*, visual_confidence: float, firms_hotspot_nearby: bool,
                  news_event_nearby: bool, official_alert: bool) -> dict:
    """Cross-source corroboration (spec §89.9). Keeps visual confidence and
    event confidence separate — a camera alone never confirms an event."""
    cross = 0.0
    sources = []
    if firms_hotspot_nearby:
        cross += 0.35
        sources.append("FIRMS")
    if news_event_nearby:
        cross += 0.30
        sources.append("news")
    if official_alert:
        cross += 0.35
        sources.append("official")
    cross = min(1.0, cross)
    return {
        "visual_confidence": round(visual_confidence, 3),
        "cross_source_confidence": round(cross, 3),
        "corroborating_sources": sources,
        # Event confidence blends the two but a lone camera stays a candidate.
        "event_confidence": round(min(0.95, 0.4 * visual_confidence + 0.6 * cross), 3)
        if sources else round(0.3 * visual_confidence, 3),
        "status": "corroborated" if sources else "candidate_visual_signal",
    }
