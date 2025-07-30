"""EM-DAT historical disaster ingestion.

Downloads the public EM-DAT CSV (compressed) and stores disasters of the last
100 years into `historical_events` table with proper lat/lon when available.
Source: https://public.emdat.be/
"""

import gzip
import csv
import io
import requests
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from utils.config import config, logger
from utils.geo import country_code_to_latlon

EMDAT_URL = "https://public.emdat.be/download/DisasterData.csv.gz"


def fetch_emdat_disasters() -> List[Dict[str, Any]]:
    try:
        r = requests.get(EMDAT_URL, timeout=60)
        r.raise_for_status()
        gz = gzip.GzipFile(fileobj=io.BytesIO(r.content))
        reader = csv.DictReader(io.TextIOWrapper(gz, encoding="utf-8"))
        events: List[Dict[str, Any]] = []
        for row in reader:
            try:
                year = int(row["Year"])
                if year < datetime.utcnow().year - 100:
                    continue
                country = row["ISO"] or ""
                latlon = country_code_to_latlon(country) if country else None
                events.append({
                    "title": f"{row['Disaster Type']} in {row['Country']}",
                    "description": row.get("Disaster Subtype", "") + ": " + row.get("Total Deaths", ""),
                    "published_at": f"{year}-01-01",
                    "source": "EM-DAT",
                    "latlon": latlon,
                    "type": row["Disaster Type"].lower().replace(" ", "_"),
                    "fatalities": int(row["Total Deaths"] or 0)
                })
            except Exception:
                continue
        return events
    except Exception as exc:
        logger.error(f"[EMDAT] Error fetching disasters: {exc}")
        return []


def store_emdat(events: List[Dict[str, Any]]):
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
                ev["latlon"][0] if ev["latlon"] else None,
                ev["latlon"][1] if ev["latlon"] else None,
                ev["type"], ev["fatalities"]
            )
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    data = fetch_emdat_disasters()
    store_emdat(data)
    logger.info(f"[EM-DAT] Stored {len(data)} disasters (100y)")
