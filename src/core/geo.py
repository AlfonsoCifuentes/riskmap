"""Geolocation with explicit uncertainty (spec §4.8 / §99, addendum).

The legacy pipeline mapped a country to its capital and dropped a precise point
on the map — false precision that turns the heatmap into a "media attention map"
(spec §4.8). This module never claims more precision than the evidence supports.
Every resolved location carries:

    latitude, longitude   -- representative point (centroid of the area)
    geo_method            -- how it was derived
    geo_precision_m       -- radius of the uncertainty area, in metres
    geo_confidence        -- 0..1 confidence in the placement
    geo_is_fallback       -- True when we only know a coarse area

Precision tiers (spec §99):
    exact   -> point            (explicit coordinates in the source)
    city    -> uncertainty circle
    region  -> coarse polygon / large circle
    country -> country-level geometry

Pure stdlib. A gazetteer can be injected; nothing here hardcodes capitals as if
they were the incident location.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

# Representative uncertainty radius (metres) per precision tier. These are the
# radius of the circle we are willing to claim — NOT a pretend-exact point.
PRECISION_RADIUS_M = {
    "exact": 500,
    "city": 15_000,
    "region": 120_000,
    "country": 600_000,
}

# Base confidence per tier before evidence adjustments.
_TIER_BASE_CONFIDENCE = {
    "exact": 0.95,
    "city": 0.75,
    "region": 0.55,
    "country": 0.35,
}

_VALID_TIERS = tuple(PRECISION_RADIUS_M.keys())


@dataclass(frozen=True)
class GeoResult:
    latitude: float
    longitude: float
    geo_method: str
    geo_precision: str          # exact | city | region | country
    geo_precision_m: float
    geo_confidence: float
    geo_is_fallback: bool

    def as_dict(self) -> dict:
        return asdict(self)


def _valid_latlon(lat, lon) -> bool:
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return False
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def resolve(
    *,
    precision: str,
    latitude,
    longitude,
    method: str,
    source_count: int = 1,
    has_official_source: bool = False,
    coordinates_explicit: bool = False,
) -> GeoResult | None:
    """Build a GeoResult with an honest confidence + uncertainty radius.

    Returns None if the coordinates are invalid — the caller must then either
    fall back to a coarser tier or drop the point (never invent one).

    Confidence starts from the tier base and is nudged by corroboration:
      + explicit coordinates in the source
      + multiple independent sources
      + an official source agrees
    and is capped to [0.05, 0.99].
    """
    if precision not in _VALID_TIERS:
        raise ValueError(f"invalid precision tier: {precision!r}")
    if not _valid_latlon(latitude, longitude):
        return None

    conf = _TIER_BASE_CONFIDENCE[precision]
    if coordinates_explicit:
        conf += 0.05
    if source_count >= 3:
        conf += 0.08
    elif source_count == 2:
        conf += 0.04
    if has_official_source:
        conf += 0.07
    conf = max(0.05, min(0.99, conf))

    return GeoResult(
        latitude=float(latitude),
        longitude=float(longitude),
        geo_method=method,
        geo_precision=precision,
        geo_precision_m=float(PRECISION_RADIUS_M[precision]),
        geo_confidence=round(conf, 3),
        # Anything coarser than a city point is a fallback area, not a place.
        geo_is_fallback=precision in ("region", "country"),
    )


def to_geometry(result: GeoResult) -> dict:
    """GeoJSON-ish geometry honouring the uncertainty tier.

    exact/city -> Point (the UI draws an uncertainty circle from geo_precision_m).
    region/country -> the same point but flagged as an area centroid; the UI
    should render a circle/polygon of geo_precision_m, never a pin implying a
    known spot.
    """
    return {
        "type": "Point",
        "coordinates": [result.longitude, result.latitude],
        "uncertainty_radius_m": result.geo_precision_m,
        "is_area_centroid": result.geo_is_fallback,
    }


def choose_precision(*, has_point: bool, has_city: bool, has_region: bool,
                     has_country: bool) -> str | None:
    """Pick the finest precision tier the available evidence justifies."""
    if has_point:
        return "exact"
    if has_city:
        return "city"
    if has_region:
        return "region"
    if has_country:
        return "country"
    return None
