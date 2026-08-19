"""Alert rules with dedupe + cooldown (spec §18 / §103, addendum).

Decides whether an event state-change warrants a notification, and suppresses
spam via a fingerprint (event + state + threshold bucket) and a cooldown window.
Pure logic — delivery channels (web-push/email) plug in later; this is the
gate that keeps a portfolio from emailing itself thousands of times.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

DEFAULT_COOLDOWN = timedelta(hours=6)


def matches_subscription(event: dict, sub: dict) -> bool:
    """Does an event satisfy a subscription's filters?

    sub: {categories?, min_risk?, min_confidence?, max_distance_km?, distance_km?,
          official_only?}
    """
    cats = sub.get("categories")
    if cats and event.get("category") not in cats:
        return False
    if event.get("risk_score", 0) < sub.get("min_risk", 0):
        return False
    if event.get("confidence", 0) < sub.get("min_confidence", 0):
        return False
    if sub.get("official_only") and not event.get("has_official_source"):
        return False
    max_d = sub.get("max_distance_km")
    if max_d is not None and sub.get("distance_km") is not None:
        if sub["distance_km"] > max_d:
            return False
    return True


def _risk_bucket(risk: float) -> str:
    if risk >= 80:
        return "critical"
    if risk >= 60:
        return "high"
    if risk >= 35:
        return "medium"
    return "low"


def fingerprint(event_id: object, state: str, risk: float) -> str:
    """Stable id for (event, material-state, risk-bucket) to dedupe alerts."""
    raw = f"{event_id}|{state}|{_risk_bucket(risk)}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def should_alert(event: dict, sub: dict, *, last_sent_at: datetime | None = None,
                 now: datetime | None = None,
                 cooldown: timedelta = DEFAULT_COOLDOWN,
                 seen_fingerprints: set | None = None) -> tuple[bool, str, str]:
    """Return (send, reason, fingerprint).

    Blocks when: subscription doesn't match, same fingerprint already sent, or
    inside the cooldown window.
    """
    now = now or datetime.utcnow()
    fp = fingerprint(event.get("id"), event.get("state", "update"),
                     event.get("risk_score", 0))

    if not matches_subscription(event, sub):
        return False, "does not match subscription", fp
    if seen_fingerprints is not None and fp in seen_fingerprints:
        return False, "duplicate (same event/state/bucket)", fp
    if last_sent_at is not None and (now - last_sent_at) < cooldown:
        return False, "within cooldown window", fp
    return True, "material change matches subscription", fp
