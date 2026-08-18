"""Bridge legacy enrichment signals into the v2 geo + risk model.

Pure functions so they can be unit-tested without the DB. `enrich.py` calls
these to populate the new columns (geo_method/geo_confidence/geo_precision_m/
geo_is_fallback, risk_engine_version, event_confidence) without a large rewrite.
"""
from __future__ import annotations

from src.core import geo, risk


def derive_geo(*, method: str, has_city: bool, has_country: bool,
               latitude, longitude, source_count: int = 1) -> dict:
    """Map an inferred location into honest geo fields.

    precision tier: city if a city was identified, else country (coarse).
    Returns {} when coordinates are missing/invalid (caller stores nothing —
    no invented point)."""
    precision = geo.choose_precision(
        has_point=False, has_city=has_city, has_region=False,
        has_country=has_country or has_city)
    if precision is None or latitude is None or longitude is None:
        return {}
    result = geo.resolve(precision=precision, latitude=latitude,
                         longitude=longitude, method=method,
                         source_count=source_count)
    if result is None:
        return {}
    return {
        "geo_method": result.geo_method,
        "geo_precision": result.geo_precision,
        "geo_precision_m": result.geo_precision_m,
        "geo_confidence": result.geo_confidence,
        "geo_is_fallback": result.geo_is_fallback,
    }


def derive_risk(*, keyword_risk_0_1: float, geo_confidence: float = 0.5,
                independent_source_count: int = 1,
                has_official_source: bool = False,
                recency_hours: float = 0.0) -> dict:
    """Turn the legacy keyword severity signal into a v2 assessment.

    keyword_risk_0_1 is treated as a *severity* signal (not a probability, not a
    confidence). Confidence is computed separately from evidence signals."""
    a = risk.assess(
        severity=keyword_risk_0_1,
        geo_confidence=geo_confidence,
        independent_source_count=independent_source_count,
        has_official_source=has_official_source,
        recency_hours=recency_hours,
    )
    return {
        "risk_score": a.risk_score,
        "risk_level": a.risk_level,
        "event_confidence": a.confidence,
        "risk_engine_version": a.risk_engine_version,
        "severity_normalized": round(a.severity * 100, 1),
    }
