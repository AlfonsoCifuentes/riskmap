"""
Módulo de ingesta de fuentes OSINT y desastres naturales reales para Riskmap.
Incluye conectores para GDELT, USGS, EMSC, OpenWeather, Global Disaster Alert y base para SentinelHub/NASA.
Todos los datos se almacenan en la base de datos y se normalizan para análisis y visualización.
"""

import os
import requests
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from utils.config import config, logger
from utils.geo import extract_event_location
import sqlite3

# --- GDELT: Eventos geopolíticos globales ---
def fetch_gdelt_events(days: int = 1) -> List[Dict[str, Any]]:
    """
    Descarga eventos recientes de GDELT (https://www.gdeltproject.org/)
    Devuelve una lista de dicts normalizados con campos clave: title, content, url, published_at, source, location, type
    """
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": "conflict OR protest OR war OR military OR explosion OR attack OR disaster",
        "mode": "ArtList",
        "maxrecords": 100,
        "format": "json"
    }
    try:
        r = requests.get(base_url, params=params, timeout=20)
        r.raise_for_status()
        try:
            data = r.json()
        except ValueError as ve:
            logger.warning(f"GDELT returned invalid JSON: {ve}")
            return []
        results = []
        for art in data.get("articles", []):
            results.append({
                "title": art.get("title"),
                "content": art.get("seendate", "") + " " + art.get("sourcecountry", ""),
                "url": art.get("url"),
                "published_at": art.get("seendate"),
                "source": art.get("sourceurl"),
                # Extraer ubicación aproximada del contenido/title vía heurística geo
                "location": extract_event_location(art.get("title","")) or extract_event_location(art.get("content","")),
                "type": art.get("domain", "news")
            })
        return results
    except requests.exceptions.HTTPError as he:
        logger.warning(f"Error fetching GDELT events (HTTP): {he}")
        return []
    except Exception as e:
        logger.error(f"Error fetching GDELT events: {e}")
        return []

# --- USGS: Terremotos globales ---
def fetch_usgs_earthquakes(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Descarga terremotos recientes de USGS (https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson)
    """
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        results = []
        for feat in data.get("features", []):
            prop = feat["properties"]
            geom = feat["geometry"]
            results.append({
                "title": f"Earthquake M{prop['mag']} {prop['place']}",
                "content": prop.get("title", ""),
                "url": prop.get("url", ""),
                "published_at": datetime.utcfromtimestamp(prop["time"] / 1000).isoformat(),
                "source": "USGS",
                "location": geom["coordinates"][1:3],
                "type": "earthquake",
                "magnitude": prop["mag"]
            })
        return results
    except Exception as e:
        logger.error(f"Error fetching USGS earthquakes: {e}")
        return []

# --- EMSC: Terremotos Europa/Mundo ---
def fetch_emsc_earthquakes() -> List[Dict[str, Any]]:
    """
    Descarga terremotos recientes de EMSC (https://www.emsc-csem.org/Earthquake/?view=1)
    """
    url = "https://www.seismicportal.eu/fdsnws/event/1/query?format=geojson&limit=100"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except requests.exceptions.HTTPError as he:
        # Bad requests are logged as warning and skipped
        logger.warning(f"Error fetching EMSC earthquakes (HTTP): {he}")
        return []
    except Exception as e:
        logger.error(f"Error fetching EMSC earthquakes: {e}")
        return []
    try:
        data = r.json()
    except ValueError as ve:
        logger.warning(f"EMSC returned invalid JSON: {ve}")
        return []
        results = []
        for feat in data.get("features", []):
            prop = feat["properties"]
            geom = feat["geometry"]
            results.append({
                "title": f"Earthquake M{prop['mag']} {prop['flynn_region']}",
                "content": prop.get("flynn_region", ""),
                "url": prop.get("url", ""),
                "published_at": prop.get("time", ""),
                "source": "EMSC",
                "location": geom["coordinates"][1:3],
                "type": "earthquake",
                "magnitude": prop["mag"]
            })
        return results
    except Exception as e:
        logger.error(f"Error fetching EMSC earthquakes: {e}")
        return []

# --- OpenWeather: Clima extremo (ejemplo: alertas globales) ---
def fetch_openweather_alerts(lat: float, lon: float) -> List[Dict[str, Any]]:
    """
    Descarga alertas meteorológicas para una ubicación usando API key de OpenWeather desde config o env.
    """
    # Obtener API key
    api_key = config.get('api_keys.openweather') or os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        logger.error("OpenWeather API key not configured.")
        return []
    url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={api_key}&exclude=minutely,hourly,daily"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        results = []
        for alert in data.get("alerts", []):
            results.append({
                "title": alert.get("event", "Weather Alert"),
                "content": alert.get("description", ""),
                "url": "https://openweathermap.org/",
                "published_at": datetime.utcfromtimestamp(alert["start"]).isoformat(),
                "source": "OpenWeather",
                "location": [lat, lon],
                "type": "weather_alert"
            })
        return results
    except Exception as e:
        logger.error(f"Error fetching OpenWeather alerts: {e}")
        return []

# --- Global Disaster Alert (GDACS): Desastres globales ---
def fetch_gdacs_events() -> List[Dict[str, Any]]:
    """
    Descarga eventos recientes de GDACS (https://www.gdacs.org/xml/rss.xml)
    """
    url = "https://www.gdacs.org/xml/rss.xml"
    try:
        import feedparser
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries:
            results.append({
                "title": entry.get("title", "GDACS Event"),
                "content": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "published_at": entry.get("published", ""),
                "source": "GDACS",
                "location": entry.get("gdacs:location", ""),
                "type": entry.get("gdacs:eventtype", "disaster")
            })
        return results
    except Exception as e:
        logger.error(f"Error fetching GDACS events: {e}")
        return []

# --- SentinelHub/NASA: Estructura base para imágenes satelitales ---
def fetch_satellite_image(lat: float, lon: float, date: str) -> str:
    """
    Descarga una imagen satelital de SentinelHub/NASA Worldview para una ubicación y fecha dadas.
    Devuelve la ruta local de la imagen descargada.
    """
    # Ejemplo: NASA Worldview snapshot API (https://wvs.earthdata.nasa.gov/)
    url = f"https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&TIME={date}&BBOX={lat-0.5},{lon-0.5},{lat+0.5},{lon+0.5}&CRS=EPSG:4326&LAYERS=VIIRS_SNPP_CorrectedReflectance_TrueColor&WRAP=DAY&FORMAT=image/jpeg&WIDTH=512&HEIGHT=512"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        img_path = f"data/satellite_{lat}_{lon}_{date}.jpg"
        with open(img_path, "wb") as f:
            f.write(r.content)
        return img_path
    except Exception as e:
        logger.error(f"Error fetching satellite image: {e}")
        return ""

# --- Copernicus Public Alerts: Desastres y emergencias mundiales ---
def fetch_copernicus_alerts() -> List[Dict[str, Any]]:
    """
    Descarga alertas públicas del Servicio de Gestión de Emergencias de Copernicus.
    Fuente: https://emergency.copernicus.eu/mapping
    """
    url = "https://emergency.copernicus.eu/mapping/app/rest/services/Latest_Public_Alerts/MapServer/0/query"
    params = {"where": "1=1", "outFields": "*", "f": "json"}
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        events = []
        for feat in data.get('features', []):
            props = feat.get('attributes', {})
            events.append({
                'title': props.get('AlertName', 'Copernicus Alert'),
                'content': props.get('Description', ''),
                'url': 'https://emergency.copernicus.eu/',
                'published_at': datetime.utcfromtimestamp(props.get('Timestamp', 0) / 1000).isoformat() if props.get('Timestamp') else '',
                'source': 'Copernicus EMS',
                'location': [props.get('Longitude'), props.get('Latitude')],
                'type': props.get('AlertType', '').lower()
            })
        return events
    except Exception as e:
        logger.error(f"Error fetching Copernicus alerts: {e}")
        return []

# --- HealthMap: Alertas de salud y epidemias ---
def fetch_healthmap_alerts(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Descarga eventos de HealthMap (http://api.healthmap.org).
    """
    url = f"http://api.healthmap.org/dataportal/v1/events.json?limit={limit}"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        events = []
        for item in data.get('rows', []):
            events.append({
                'title': item.get('title', 'HealthMap Event'),
                'content': item.get('description', ''),
                'url': item.get('url', ''),
                'published_at': item.get('firstseen_at', ''),
                'source': 'HealthMap',
                'location': [item.get('latitude'), item.get('longitude')],
                'type': item.get('type', '').lower()
            })
        return events
    except Exception as e:
        logger.error(f"Error fetching HealthMap alerts: {e}")
        return []

# --- Cámaras Públicas: Feeds abiertos ---
def fetch_public_camera_feeds() -> List[str]:
    """
    Obtiene la lista de URLs de cámaras públicas definidas en configuración.
    """
    feeds = config.get('data_sources.public_cameras', [])
    valid_feeds = []
    for url in feeds:
        try:
            r = requests.head(url, timeout=10)
            if r.status_code == 200:
                valid_feeds.append(url)
        except Exception:
            continue
    return valid_feeds

# --- Almacenamiento en base de datos (ejemplo para eventos) ---
def store_events(events: List[Dict[str, Any]], table: str = "events"):
    """
    Almacena una lista de eventos normalizados en la base de datos.
    """
    if not events:
        return
    conn = sqlite3.connect(config.database.path)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, content TEXT, url TEXT, published_at TEXT, source TEXT, location TEXT, type TEXT, magnitude REAL
        )
    """)
    for ev in events:
        cursor.execute(f"""
            INSERT INTO {table} (title, content, url, published_at, source, location, type, magnitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ev.get("title"), ev.get("content"), ev.get("url"), ev.get("published_at"),
            ev.get("source"), json.dumps(ev.get("location")), ev.get("type"), ev.get("magnitude")
        ))
    conn.commit()
    conn.close()
