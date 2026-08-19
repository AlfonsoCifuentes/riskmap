"""
Riskmap A.I. Free Image Acquisition Pipeline
==========================================
Acquires imagery from free sources for active AOIs / events:
  - Copernicus Browser (Sentinel-2) — 10m resolution, 5-day revisit
  - USGS EarthExplorer (Landsat 8/9) — 30m, 16-day revisit
  - NASA FIRMS (fire/hotspots) — near real-time
  - NASA GIBS (MODIS/VIIRS tiles) — daily global
  - GDACS (disaster alerts + maps)

Stores compressed WebP images in the DB (only when signals detected).

Usage:
    python -m src.pipeline.acquire_images
"""

import os
import sys
import io
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [IMAGERY] %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Image compression helper
# ---------------------------------------------------------------------------

def compress_to_webp(image_bytes: bytes, max_size_px: int = 512, quality: int = 60) -> bytes:
    """Compress an image to WebP, resize if larger than max_size_px."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        # Resize if too large
        w, h = img.size
        if max(w, h) > max_size_px:
            ratio = max_size_px / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='WEBP', quality=quality)
        return buf.getvalue()
    except ImportError:
        logger.warning("Pillow not installed — storing raw image")
        return image_bytes


# ---------------------------------------------------------------------------
# 1. NASA FIRMS (Fire Information for Resource Management System)
# ---------------------------------------------------------------------------

def fetch_firms_hotspots(lat: float, lon: float, radius_km: float = 50) -> List[Dict]:
    """Fetch recent fire hotspots from NASA FIRMS.

    The FIRMS area API requires a free MAP_KEY (see
    https://firms.modaps.eosdis.nasa.gov/api/map_key/). Contract (addendum B7):
        /api/area/csv/[MAP_KEY]/[SOURCE]/[west,south,east,north]/[DAY_RANGE]
    Without the key we return [] and stay DEGRADED — never a fake/empty-success.
    """
    map_key = os.getenv('NASA_FIRMS_MAP_KEY', '').strip()
    if not map_key:
        logger.info("⏭ NASA_FIRMS_MAP_KEY not set — FIRMS hotspots DEGRADED (skipped)")
        return []
    try:
        # bbox order is west,south,east,north (minLon,minLat,maxLon,maxLat).
        url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
            f"{map_key}/VIIRS_SNPP_NRT/{lon-1},{lat-1},{lon+1},{lat+1}/1"
        )
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            logger.warning(f"FIRMS HTTP {resp.status_code}")
            return []

        lines = resp.text.strip().split('\n')
        if len(lines) < 2:
            return []

        headers = lines[0].split(',')
        hotspots = []
        for line in lines[1:]:
            vals = line.split(',')
            if len(vals) >= len(headers):
                row = dict(zip(headers, vals))
                hotspots.append({
                    'latitude': float(row.get('latitude', 0)),
                    'longitude': float(row.get('longitude', 0)),
                    'brightness': float(row.get('bright_ti4', 0)),
                    'confidence': row.get('confidence', 'nominal'),
                    'acq_date': row.get('acq_date', ''),
                    'source': 'FIRMS_VIIRS',
                })
        return hotspots
    except Exception as e:
        logger.warning(f"FIRMS fetch failed: {e}")
        return []


# ---------------------------------------------------------------------------
# 2. NASA GIBS (Global Imagery Browse Services) — MODIS/VIIRS tiles
# ---------------------------------------------------------------------------

def fetch_gibs_tile(lat: float, lon: float, layer: str = "VIIRS_SNPP_CorrectedReflectance_TrueColor",
                    date: str = None) -> Optional[bytes]:
    """Fetch a GIBS tile (WMTS) for the given location."""
    if date is None:
        date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

    # Convert lat/lon to tile coordinates (zoom level 6 for overview)
    import math
    zoom = 6
    n = 2 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(math.radians(lat)) +
                1.0 / math.cos(math.radians(lat))) / math.pi) / 2.0 * n)

    url = (
        f"https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/"
        f"{layer}/default/{date}/250m/{zoom}/{ytile}/{xtile}.jpg"
    )

    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            return resp.content
    except Exception as e:
        logger.debug(f"GIBS tile failed: {e}")
    return None


# ---------------------------------------------------------------------------
# 3. GDACS (Global Disaster Alerts Coordination System)
# ---------------------------------------------------------------------------

def fetch_gdacs_alerts() -> List[Dict]:
    """Fetch current disaster alerts from GDACS RSS/GeoJSON."""
    try:
        resp = requests.get(
            "https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP",
            timeout=20,
            headers={'Accept': 'application/json'},
        )
        if resp.status_code != 200:
            return []

        data = resp.json()
        alerts = []
        for feature in data.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            coords = geom.get('coordinates', [0, 0])

            alerts.append({
                'title': props.get('name', props.get('eventtype', '')),
                'event_type': props.get('eventtype', '').lower(),
                'severity': float(props.get('alertlevel', 0)),
                'latitude': coords[1] if len(coords) >= 2 else 0,
                'longitude': coords[0] if len(coords) >= 2 else 0,
                'date': props.get('fromdate', ''),
                'source': 'GDACS',
                'url': props.get('url', {}).get('report', ''),
            })
        return alerts
    except Exception as e:
        logger.warning(f"GDACS fetch failed: {e}")
        return []


# ---------------------------------------------------------------------------
# 4. Copernicus Open Access Hub (Sentinel-2)
# ---------------------------------------------------------------------------

# Sentinel-2 true-color evalscript (L2A bands B04/B03/B02).
_S2_TRUECOLOR_EVALSCRIPT = """//VERSION=3
function setup() {
  return { input: ["B02", "B03", "B04"], output: { bands: 3 } };
}
function evaluatePixel(s) {
  return [2.5 * s.B04, 2.5 * s.B03, 2.5 * s.B02];
}
"""


def _copernicus_token() -> Optional[str]:
    """Obtain a CDSE OAuth token from client credentials, or None."""
    client_id = os.getenv('COPERNICUS_CLIENT_ID', '')
    client_secret = os.getenv('COPERNICUS_CLIENT_SECRET', '')
    if not client_id or not client_secret:
        return None
    try:
        resp = requests.post(
            'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
            },
            timeout=15,
        )
        return resp.json().get('access_token')
    except Exception as e:
        logger.debug(f"Copernicus token failed: {e}")
        return None


def fetch_sentinel2_preview(lat: float, lon: float,
                            box_deg: float = 0.08,
                            size_px: int = 512,
                            max_cloud: int = 40,
                            days_back: int = 30) -> Optional[bytes]:
    """Fetch a real Sentinel-2 L2A true-color PNG via the CDSE Sentinel Hub
    Process API (addendum B8, spec §6.3).

    Returns PNG bytes, or None (DEGRADED) if credentials are missing or no
    suitable low-cloud scene exists. Never returns synthetic data.

    NOTE on scientific honesty (spec §5.1): Sentinel-2 is 10 m/px — suitable for
    wildfire scars, floods, large-scale change and vegetation, NOT for detecting
    individual vehicles. The AOI planner must not request S2 for such tasks.
    """
    token = _copernicus_token()
    if not token:
        logger.info("⏭ COPERNICUS creds not set — Sentinel-2 DEGRADED (skipped)")
        return None

    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=days_back)
    bbox = [lon - box_deg, lat - box_deg, lon + box_deg, lat + box_deg]
    payload = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": from_date.strftime('%Y-%m-%dT00:00:00Z'),
                        "to": to_date.strftime('%Y-%m-%dT23:59:59Z'),
                    },
                    "maxCloudCoverage": max_cloud,
                    "mosaickingOrder": "leastCC",
                },
            }],
        },
        "output": {
            "width": size_px,
            "height": size_px,
            "responses": [{"identifier": "default",
                           "format": {"type": "image/png"}}],
        },
        "evalscript": _S2_TRUECOLOR_EVALSCRIPT,
    }
    try:
        resp = requests.post(
            'https://sh.dataspace.copernicus.eu/api/v1/process',
            headers={'Authorization': f'Bearer {token}'},
            json=payload,
            timeout=45,
        )
        if resp.status_code != 200:
            logger.warning(f"Sentinel-2 Process API HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        if not resp.content or not resp.headers.get('Content-Type', '').startswith('image/'):
            return None
        return resp.content
    except Exception as e:
        logger.debug(f"Sentinel-2 Process API failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Main acquisition pipeline
# ---------------------------------------------------------------------------

def get_active_aois() -> List[Dict]:
    """Get active Areas of Interest from the database."""
    db = get_db()
    rows = db.execute(
        "SELECT id, name, event_id, bbox_json, priority "
        "FROM aois WHERE active = 1 ORDER BY priority DESC LIMIT 20",
        fetch=True,
    )
    return rows


def get_event_locations() -> List[Dict]:
    """Get locations from recent events (fallback if no AOIs yet)."""
    db = get_db()
    rows = db.execute(
        "SELECT el.latitude, el.longitude, el.name, e.id as event_id, "
        "       e.event_type, e.title, e.last_updated "
        "FROM event_locations el "
        "JOIN events e ON e.id = el.event_id "
        "WHERE COALESCE(e.severity,0) >= 0.3 "
        "ORDER BY e.last_updated DESC NULLS LAST LIMIT 20",
        fetch=True,
    )
    return rows


def store_image(source_type: str, image_bytes: bytes, lat: float, lon: float,
                event_id: int = None, aoi_id: int = None,
                source_url: str = None, metadata: dict = None):
    """Compress and store an image in the database."""
    db = get_db()
    ph = db.placeholder

    compressed = compress_to_webp(image_bytes)
    size_kb = len(compressed) / 1024.0

    # Mark previous images as not-latest for this AOI+source
    if aoi_id:
        db.execute(
            f"UPDATE images SET is_latest = 0 "
            f"WHERE aoi_id = {ph} AND source_type = {ph} AND is_latest = 1",
            (aoi_id, source_type),
        )

    db.execute(
        f"""INSERT INTO images
            (source_type, source_url, aoi_id, event_id,
             latitude, longitude, captured_at,
             image_data, image_format, image_size_kb, metadata_json, is_latest)
            VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},'webp',{ph},{ph},1)""",
        (
            source_type, source_url, aoi_id, event_id,
            lat, lon, datetime.utcnow().isoformat(),
            compressed, size_kb,
            json.dumps(metadata) if metadata else None,
        ),
    )
    logger.info(f"  📸 Stored {source_type} image: {size_kb:.1f} KB at ({lat:.2f}, {lon:.2f})")


def acquire_for_location(lat: float, lon: float, name: str = '',
                         event_id: int = None, aoi_id: int = None):
    """Acquire imagery from all free sources for a single location."""
    acquired = 0

    # 1. NASA GIBS tile
    gibs_data = fetch_gibs_tile(lat, lon)
    if gibs_data:
        store_image('gibs_modis', gibs_data, lat, lon, event_id, aoi_id,
                     metadata={'layer': 'VIIRS_CorrectedReflectance', 'location': name})
        acquired += 1

    # 2. FIRMS hotspots (data only, no image)
    hotspots = fetch_firms_hotspots(lat, lon)
    if hotspots:
        logger.info(f"  🔥 {len(hotspots)} FIRMS hotspots near {name or f'({lat},{lon})'}")
        # Store hotspot data as metadata (no image)
        db = get_db()
        ph = db.placeholder
        db.execute(
            f"""INSERT INTO images
                (source_type, aoi_id, event_id, latitude, longitude,
                 captured_at, metadata_json, is_latest, image_format)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},1,'json')""",
            (
                'firms_hotspot', aoi_id, event_id, lat, lon,
                datetime.utcnow().isoformat(),
                json.dumps({'hotspots': hotspots[:10]}),
            ),
        )
        acquired += 1

    # 3. Sentinel-2 (if credentials available)
    s2_data = fetch_sentinel2_preview(lat, lon)
    if s2_data:
        store_image('sentinel2', s2_data, lat, lon, event_id, aoi_id,
                     metadata={'sensor': 'Sentinel-2', 'location': name})
        acquired += 1

    return acquired


def main():
    logger.info("=" * 60)
    logger.info("Riskmap A.I. Image Acquisition Pipeline")
    logger.info("=" * 60)

    total_acquired = 0

    # 1. Process AOIs
    aois = get_active_aois()
    logger.info(f"Active AOIs: {len(aois)}")
    for aoi in aois:
        try:
            bbox = json.loads(aoi.get('bbox_json', '[]'))
            if len(bbox) == 4:
                lat = (bbox[1] + bbox[3]) / 2
                lon = (bbox[0] + bbox[2]) / 2
                n = acquire_for_location(
                    lat, lon, aoi.get('name', ''),
                    aoi.get('event_id'), aoi['id']
                )
                total_acquired += n
        except Exception as e:
            logger.warning(f"AOI {aoi.get('name')}: {e}")

    # 2. Process event locations (if few AOIs)
    if len(aois) < 5:
        locations = get_event_locations()
        logger.info(f"Event locations: {len(locations)}")
        for loc in locations:
            try:
                n = acquire_for_location(
                    loc['latitude'], loc['longitude'],
                    loc.get('name', ''), loc.get('event_id')
                )
                total_acquired += n
            except Exception as e:
                logger.warning(f"Location {loc.get('name')}: {e}")

    # 3. Fetch GDACS disaster alerts and create events
    gdacs = fetch_gdacs_alerts()
    if gdacs:
        logger.info(f"GDACS alerts: {len(gdacs)}")
        _store_gdacs_as_events(gdacs)

    logger.info(f"✅ Total images acquired: {total_acquired}")


def _store_gdacs_as_events(alerts: List[Dict]):
    """Store GDACS disaster alerts as events."""
    db = get_db()
    ph = db.placeholder

    for alert in alerts[:10]:  # max 10
        try:
            # Check if already exists
            existing = db.execute(
                f"SELECT id FROM events WHERE title = {ph} AND event_type = 'disaster' LIMIT 1",
                (alert['title'],),
                fetch=True,
            )
            if existing:
                continue

            # severity must be stored on the 0..1 scale (schema contract).
            # GDACS scores can arrive on a larger scale; normalise defensively.
            _sev = alert.get('severity', 0.5)
            try:
                _sev = float(_sev)
            except (TypeError, ValueError):
                _sev = 0.5
            if _sev > 1:
                _sev = min(1.0, _sev / 100.0)
            db.execute(
                f"""INSERT INTO events (event_type, subtype, title, severity, started_at, explanation)
                    VALUES ('disaster', {ph}, {ph}, {ph}, {ph}, {ph})""",
                (
                    alert.get('event_type', 'unknown'),
                    alert['title'],
                    _sev,
                    alert.get('date', datetime.utcnow().isoformat()),
                    f"GDACS alert: {alert['title']}",
                ),
            )

            # Get event ID
            event_rows = db.execute(
                "SELECT id FROM events ORDER BY id DESC LIMIT 1", fetch=True
            )
            if event_rows and alert.get('latitude') and alert.get('longitude'):
                event_id = event_rows[0]['id']
                db.execute(
                    f"""INSERT INTO event_locations
                        (event_id, latitude, longitude, name, source)
                        VALUES ({ph},{ph},{ph},{ph},'gdacs')""",
                    (event_id, alert['latitude'], alert['longitude'], alert['title']),
                )
                # Create AOI for this disaster
                bbox = [
                    alert['longitude'] - 0.5, alert['latitude'] - 0.5,
                    alert['longitude'] + 0.5, alert['latitude'] + 0.5,
                ]
                db.execute(
                    f"""INSERT INTO aois (name, event_id, bbox_json, priority, active)
                        VALUES ({ph},{ph},{ph},{ph},1)""",
                    (alert['title'], event_id, json.dumps(bbox), alert.get('severity', 0.5)),
                )

        except Exception as e:
            logger.warning(f"GDACS store error: {e}")


if __name__ == '__main__':
    main()
