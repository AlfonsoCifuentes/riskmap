"""Tests for the AOI planner + capability guardrails (spec §172/§173)."""
from src.core import aoi_planner as ap


def test_low_risk_no_request():
    p = ap.plan(hazard="wildfire", risk_level="medium")
    assert p.should_request is False
    assert p.priority == "none"


def test_wildfire_uses_sentinel2():
    p = ap.plan(hazard="wildfire", risk_level="high")
    assert p.should_request and p.sensor == "sentinel-2" and p.supported


def test_flood_with_cloud_prefers_sentinel1():
    p = ap.plan(hazard="flood", risk_level="critical", cloud_cover=80)
    assert p.sensor == "sentinel-1"
    p2 = ap.plan(hazard="flood", risk_level="critical", cloud_cover=5)
    assert p2.sensor == "sentinel-2"


def test_conflict_context_only_not_vehicle_detection():
    p = ap.plan(hazard="armed_conflict", risk_level="critical")
    assert p.should_request and "UNSUPPORTED" in p.reason or "context" in p.reason


def test_capability_check_rejects_tank_on_sentinel2():
    ok, reason = ap.capability_check("tank", "sentinel-2")
    assert ok is False and "UNSUPPORTED" in reason


def test_capability_check_allows_flood_extent():
    ok, _ = ap.capability_check("flood_extent", "sentinel-2")
    assert ok is True


def test_capability_check_rejects_individual_vehicle():
    ok, _ = ap.capability_check("individual_vehicle", "sentinel-1")
    assert ok is False
