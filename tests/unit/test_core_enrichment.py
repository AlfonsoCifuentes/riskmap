"""Tests for src.core.enrichment — legacy signals -> v2 geo/risk fields."""
from src.core import enrichment


def test_derive_geo_city_precision():
    g = enrichment.derive_geo(method="ai_llm", has_city=True, has_country=True,
                              latitude=33.89, longitude=35.5)
    assert g["geo_precision"] == "city"
    assert g["geo_is_fallback"] is False
    assert 0 < g["geo_confidence"] <= 1
    assert g["geo_method"] == "ai_llm"


def test_derive_geo_country_is_fallback():
    g = enrichment.derive_geo(method="dictionary", has_city=False,
                              has_country=True, latitude=48.38, longitude=31.17)
    assert g["geo_precision"] == "country"
    assert g["geo_is_fallback"] is True


def test_derive_geo_no_coords_returns_empty():
    assert enrichment.derive_geo(method="none", has_city=False,
                                 has_country=False, latitude=None,
                                 longitude=None) == {}


def test_derive_risk_separates_score_and_confidence():
    r = enrichment.derive_risk(keyword_risk_0_1=0.9, geo_confidence=0.9,
                               independent_source_count=5,
                               has_official_source=True)
    assert 0 <= r["risk_score"] <= 100
    assert 0 <= r["event_confidence"] <= 100
    assert r["risk_engine_version"]
    assert r["severity_normalized"] == 90.0


def test_severity_scale_contract_0_1_not_0_100():
    """derive_risk expects a 0..1 severity. Feeding a 0..100 value saturates the
    engine (every event -> critical) — the live event path must normalise first.
    Regression for the pipeline scale bug (spec next-steps #1)."""
    from src.core.enrichment import derive_risk
    good = derive_risk(keyword_risk_0_1=0.6)      # correct: 0..1 severity
    saturated = derive_risk(keyword_risk_0_1=60)  # wrong scale: clamps to 1.0
    assert good["risk_level"] != "critical"
    assert good["severity_normalized"] == 60.0
    assert saturated["severity_normalized"] == 100.0  # proves saturation
    # normalising 0..100 -> 0..1 reproduces the correct result
    assert derive_risk(keyword_risk_0_1=60/100.0)["risk_level"] == good["risk_level"]
