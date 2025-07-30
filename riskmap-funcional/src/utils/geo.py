"""Utility functions for extracting and converting geographic information."""

from typing import Tuple, Optional
import re

# Minimal centroid dictionary (lat, lon) for quick geocoding
_COUNTRY_CENTROIDS = {
    "US": (38.0, -97.0),
    "RU": (61.5240, 105.3188),
    "CN": (35.8617, 104.1954),
    "UA": (48.3794, 31.1656),
    "PL": (51.9194, 19.1451),
    "DE": (51.1657, 10.4515),
    "FR": (46.2276, 2.2137),
    "GB": (55.3781, -3.4360),
    "ES": (40.4637, -3.7492),
    "IT": (41.8719, 12.5674),
    "TR": (38.9637, 35.2433),
    "SY": (34.8021, 38.9968),
    "IR": (32.4279, 53.6880),
    "IL": (31.0461, 34.8516),
    "PS": (31.9522, 35.2332),
    "EG": (26.8206, 30.8025),
    # ... extend as needed
}

_COUNTRY_REGEX = re.compile(r"\\b(" + "|".join(_COUNTRY_CENTROIDS.keys()) + r")\\b", re.IGNORECASE)


def country_code_to_latlon(code: str) -> Optional[Tuple[float, float]]:
    """Return centroid lat/lon for a 2-letter country code."""
    return _COUNTRY_CENTROIDS.get(code.upper())


def extract_event_location(text: str) -> Optional[Tuple[float, float]]:
    """Very simple heuristic: look for country codes in text and return centroid.
    In production replace with full geoparsing + geocoding (e.g., spaCy, GeoText, Nominatim).
    """
    if not text:
        return None
    match = _COUNTRY_REGEX.search(text.upper())
    if match:
        return _COUNTRY_CENTROIDS.get(match.group(1).upper())
    return None

# --- New utility -------------------------------------------------------------
import math

def latlon_to_iso3(lat: float, lon: float) -> Optional[str]:
    """Return ISO2 code of the nearest centroid (rough heuristic)."""
    closest=None
    min_d=1e9
    for code,(clat,clon) in _COUNTRY_CENTROIDS.items():
        d=math.hypot(lat-clat,lon-clon)
        if d<min_d:
            min_d=d
            closest=code
    return closest
