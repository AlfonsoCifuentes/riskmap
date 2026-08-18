"""Tests for alerts (dedupe/cooldown) and Safety Brief (official vs context)."""
from datetime import datetime, timedelta

from src.core import alerts, safety_brief

# --- alerts ---------------------------------------------------------------

def _event(**kw):
    base = {"id": 1, "category": "wildfire", "risk_score": 82,
            "confidence": 60, "state": "escalating", "has_official_source": True}
    base.update(kw)
    return base


def test_alert_matches_and_fires():
    sub = {"categories": ["wildfire"], "min_risk": 60}
    send, reason, fp = alerts.should_alert(_event(), sub)
    assert send is True and fp


def test_alert_blocked_by_subscription():
    sub = {"categories": ["flood"], "min_risk": 60}
    send, reason, _ = alerts.should_alert(_event(), sub)
    assert send is False and "subscription" in reason


def test_alert_min_risk_gate():
    sub = {"min_risk": 90}
    send, _, _ = alerts.should_alert(_event(risk_score=82), sub)
    assert send is False


def test_alert_cooldown_blocks():
    sub = {"min_risk": 60}
    now = datetime(2026, 8, 18, 12, 0, 0)
    send, reason, _ = alerts.should_alert(
        _event(), sub, last_sent_at=now - timedelta(hours=1), now=now)
    assert send is False and "cooldown" in reason


def test_alert_dedupe_fingerprint():
    sub = {"min_risk": 60}
    _, _, fp = alerts.should_alert(_event(), sub)
    send, reason, _ = alerts.should_alert(_event(), sub, seen_fingerprints={fp})
    assert send is False and "duplicate" in reason


def test_official_only_filter():
    sub = {"official_only": True}
    assert not alerts.matches_subscription(
        _event(has_official_source=False), sub)


# --- safety brief ---------------------------------------------------------

def test_safety_brief_no_official_says_so():
    ev = {"title": "Wildfire — La Palma", "category": "wildfire",
          "risk_level": "high", "confidence": 63,
          "latitude": 28.79, "longitude": -17.88}
    brief = safety_brief.build(ev, user_location=(28.6, -17.9))
    assert brief["official_guidance"] is None
    assert "No official guidance" in brief["official_guidance_note"]
    assert brief["status"]["distance_km"] is not None
    assert "not an emergency authority" in brief["disclaimer"]


def test_safety_brief_keeps_official_separate():
    ev = {"title": "Quake", "category": "earthquake",
          "latitude": 37.06, "longitude": 37.38, "risk_level": "critical"}
    official = [{"authority": "USGS", "url": "https://usgs.gov/x",
                 "text": "M6.8 confirmed", "issued_at": "2026-02-06T01:20:00Z"}]
    brief = safety_brief.build(ev, official_guidance=official)
    assert brief["official_guidance"][0]["authority"] == "USGS"
    assert brief["official_guidance_note"] is None
    # RiskMap context is a distinct section, never merged into official.
    assert isinstance(brief["riskmap_context"], list)
