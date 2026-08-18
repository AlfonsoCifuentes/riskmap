"""Tests for src.core.events — event fusion (spec §4.9/§98)."""
from datetime import datetime, timedelta

from src.core import events


def _art(url, title, cat, lat, lon, when):
    return {"url": url, "title": title, "category": cat,
            "latitude": lat, "longitude": lon, "published_at": when}


def test_ten_reports_one_incident_fuse_to_one_event():
    t = datetime(2026, 8, 18, 12, 0, 0)
    arts = [
        _art("https://reuters.com/a", "Airstrike hits Beirut suburb", "armed_conflict", 33.89, 35.50, t),
        _art("https://bbc.com/b", "Airstrike strikes Beirut suburb kills many", "armed_conflict", 33.90, 35.49, t + timedelta(hours=1)),
        _art("https://aljazeera.com/c", "Beirut suburb hit by airstrike", "armed_conflict", 33.88, 35.51, t + timedelta(hours=2)),
    ]
    evs = events.fuse(arts)
    assert len(evs) == 1
    assert evs[0]["source_count"] == 3
    assert evs[0]["independent_source_count"] == 3


def test_two_separate_attacks_different_days_stay_separate():
    t = datetime(2026, 8, 18, 12, 0, 0)
    arts = [
        _art("https://reuters.com/a", "Attack in Kharkiv power plant", "armed_conflict", 49.99, 36.23, t),
        _art("https://reuters.com/b", "Second attack in Kharkiv station days later", "armed_conflict", 49.99, 36.23, t + timedelta(days=5)),
    ]
    evs = events.fuse(arts)
    assert len(evs) == 2  # same place, but outside the time window


def test_different_categories_do_not_fuse():
    t = datetime(2026, 8, 18, 12, 0, 0)
    arts = [
        _art("https://a.com/1", "Flooding hits the valley", "flood", 39.47, -0.38, t),
        _art("https://b.com/2", "Protest march in the valley", "civil_unrest", 39.47, -0.38, t),
    ]
    evs = events.fuse(arts)
    assert len(evs) == 2


def test_haversine_reasonable():
    # London -> Paris ~ 340 km
    d = events.haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert 300 < d < 380


def test_representative_is_earliest():
    t = datetime(2026, 8, 18, 12, 0, 0)
    arts = [
        _art("https://a.com/late", "Quake in Turkey Gaziantep", "earthquake", 37.06, 37.38, t + timedelta(hours=3)),
        _art("https://b.com/early", "Quake strikes Turkey Gaziantep", "earthquake", 37.06, 37.38, t),
    ]
    evs = events.fuse(arts)
    assert len(evs) == 1
    assert evs[0]["representative"]["url"] == "https://b.com/early"
