"""Tests for src.core.geo — uncertainty-aware geolocation (spec §4.8/§99)."""
from src.core import geo


def test_exact_point_high_confidence_low_radius():
    r = geo.resolve(precision="exact", latitude=31.77, longitude=35.21,
                    method="explicit_coords", coordinates_explicit=True)
    assert r is not None
    assert r.geo_precision == "exact"
    assert r.geo_precision_m == geo.PRECISION_RADIUS_M["exact"]
    assert r.geo_confidence >= 0.9
    assert r.geo_is_fallback is False


def test_country_only_is_fallback_low_confidence():
    r = geo.resolve(precision="country", latitude=48.38, longitude=31.17,
                    method="country_centroid")
    assert r.geo_is_fallback is True
    assert r.geo_precision_m == geo.PRECISION_RADIUS_M["country"]
    assert r.geo_confidence < 0.5  # no false precision


def test_corroboration_raises_confidence():
    base = geo.resolve(precision="city", latitude=1, longitude=1,
                       method="geocoder", source_count=1)
    corrob = geo.resolve(precision="city", latitude=1, longitude=1,
                         method="geocoder", source_count=5,
                         has_official_source=True)
    assert corrob.geo_confidence > base.geo_confidence


def test_invalid_coords_returns_none():
    assert geo.resolve(precision="city", latitude=999, longitude=0,
                       method="x") is None
    assert geo.resolve(precision="city", latitude=None, longitude=None,
                       method="x") is None


def test_invalid_tier_raises():
    import pytest
    with pytest.raises(ValueError):
        geo.resolve(precision="street", latitude=0, longitude=0, method="x")


def test_choose_precision_prefers_finest():
    assert geo.choose_precision(has_point=True, has_city=True,
                                has_region=True, has_country=True) == "exact"
    assert geo.choose_precision(has_point=False, has_city=False,
                                has_region=False, has_country=True) == "country"
    assert geo.choose_precision(has_point=False, has_city=False,
                                has_region=False, has_country=False) is None


def test_geometry_flags_area_centroid():
    r = geo.resolve(precision="region", latitude=10, longitude=10, method="x")
    g = geo.to_geometry(r)
    assert g["type"] == "Point"
    assert g["is_area_centroid"] is True
    assert g["uncertainty_radius_m"] == geo.PRECISION_RADIUS_M["region"]
