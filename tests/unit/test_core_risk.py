"""Tests for src.core.risk — risk != confidence (spec §4.7/§166)."""
from src.core import risk


def test_risk_and_confidence_are_independent():
    # High severity but a single uncorroborated source: high risk, LOW confidence.
    a = risk.assess(severity=0.9, exposure=0.7, vulnerability=0.6,
                    independent_source_count=1)
    assert a.risk_level in ("high", "critical")
    assert a.confidence < 40  # single source => low confidence

    # Same incident, five sources + official: confidence rises, risk ~unchanged.
    b = risk.assess(severity=0.9, exposure=0.7, vulnerability=0.6,
                    independent_source_count=5, has_official_source=True,
                    geo_confidence=0.9)
    assert b.confidence > a.confidence
    assert abs(b.risk_score - a.risk_score) < 1.0


def test_minor_incident_not_critical():
    a = risk.assess(severity=0.1, exposure=0.1, vulnerability=0.1)
    assert a.risk_level == "low"


def test_versioned():
    a = risk.assess(severity=0.5)
    assert a.risk_engine_version == risk.RISK_ENGINE_VERSION


def test_scores_bounded():
    a = risk.assess(severity=1.0, exposure=1.0, vulnerability=1.0,
                    independent_source_count=99, has_official_source=True,
                    geo_confidence=1.0, model_agreement=1.0)
    assert 0 <= a.risk_score <= 100
    assert 0 <= a.confidence <= 100


def test_five_copies_not_five_independent_sources_effect():
    # Confidence should reflect independent_source_count, which the caller
    # computes from distinct domains (see dedup). Here 1 vs 5.
    one = risk.assess(severity=0.6, independent_source_count=1)
    five = risk.assess(severity=0.6, independent_source_count=5)
    assert five.confidence > one.confidence


def test_recency_decay_lowers_confidence():
    fresh = risk.assess(severity=0.6, independent_source_count=3, recency_hours=1)
    old = risk.assess(severity=0.6, independent_source_count=3, recency_hours=240)
    assert old.confidence < fresh.confidence


def test_explanation_is_structured_factors():
    a = risk.assess(severity=0.8, exposure=0.6, independent_source_count=3,
                    has_official_source=True)
    assert isinstance(a.factors, list)
    names = {f["factor"] for f in a.factors}
    assert "severity" in names and "official_corroboration" in names
    # No free-form model reasoning, only structured {factor, contribution, detail}.
    for f in a.factors:
        assert set(f.keys()) == {"factor", "contribution", "detail"}
