"""
Descarga y almacena datos históricos de conflictos armados (últimos 100 años) usando la base de datos
UCDP (Uppsala Conflict Data Program, https://www.ucdp.uu.se/) y eventos de desastres naturales EM-DAT.
Los datos se guardan en la tabla `historical_events` para análisis y visualización.
"""

import csv
import gzip
import io
import json
import sqlite3
import requests
from datetime import datetime
from typing import List, Dict, Any

from utils.config import config, logger
from utils.geo import country_code_to_latlon

UCDP_CSV_URL = (
    "https://ucdp.uu.se/downloads/ged/ged221-csv.zip"  # GED v22.1 (zip con csv inside)
)

EMDAT_CSV_URL = (
    "https://public.emdat.be/download/DisasterData.csv.gz"  # Requiere registro; ejemplo link genérico
)

def _download_zip_csv(url: str, inner_csv_name: str) -> io.BytesIO:
    """Descarga un zip y devuelve BytesIO del CSV interno elegido"""
    import zipfile
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    with z.open(inner_csv_name) as f:
        return io.BytesIO(f.read())

def fetch_ucdp_conflicts() -> List[Dict[str, Any]]:
    """Descarga el conjunto GED (2010-2022) y devuelve eventos normalizados."""
    try:
        # El zip contiene GED_1989-2022.csv
        csv_bytes = _download_zip_csv(UCDP_CSV_URL, "ged221.csv")
        reader = csv.DictReader(io.TextIOWrapper(csv_bytes, encoding="utf-8", newline=""))
        events = []
        for row in reader:
            try:
                year = int(row["year"])
                if year < datetime.utcnow().year - 100:
                    continue  # limitar a 100 años
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                country = row["country"]
                events.append({
                    "title": f"{row['type_of_violence']} in {country}",
                    "description": row["notes"] or "UCDP event",
                    "published_at": f"{year}-01-01",
                    "source": "UCDP GED",
                    "latlon": [lat, lon],
                    "type": "armed_conflict",
                    "fatalities": int(row["deaths_a"] or 0) + int(row["deaths_b"] or 0) + int(row["deaths_civilians"] or 0)
                })
            except Exception:
                continue
        return events
    except Exception as e:
        logger.error(f"Error fetching UCDP: {e}")
        return []

def store_historical(events: List[Dict[str, Any]]):
    if not events:
        return
    conn = sqlite3.connect(config.database.path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, description TEXT, published_at TEXT, source TEXT,
            lat REAL, lon REAL, type TEXT, fatalities INTEGER
        )
        """
    )
    for ev in events:
        cur.execute(
            """INSERT INTO historical_events
            (title, description, published_at, source, lat, lon, type, fatalities)
            VALUES (?,?,?,?,?,?,?,?)""",
            (
                ev["title"], ev["description"], ev["published_at"], ev["source"],
                ev["latlon"][0] if ev.get("latlon") else None,
                ev["latlon"][1] if ev.get("latlon") else None,
                ev["type"], ev.get("fatalities")
            )
        )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    data = fetch_ucdp_conflicts()
    store_historical(data)
    logger.info(f"Stored {len(data)} historical conflict events (UCDP).")
