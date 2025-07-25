"""Energy data ingestion using U.S. EIA open API.

Fetches crude oil production (thousand barrels per day) per country and stores
in `country_energy` for multi-factor geopolitical analysis.
EIA API key required in .env (EIA_API_KEY).
Docs: https://www.eia.gov/opendata/
"""

import os
import requests
import sqlite3
from typing import List, Dict
from datetime import datetime
from utils.config import logger, config

API_KEY = os.getenv("EIA_API_KEY", "")
BASE_URL = "https://api.eia.gov/v2/international/data/?api_key={key}&data=production&frequency=annual&type=oil&facets=series-id:&sort=desc&offset=0&length=5000".format(key=API_KEY)


def fetch_oil_production() -> List[Dict]:
    if not API_KEY:
        logger.warning("[EIA] Missing EIA_API_KEY env var, skipping energy ingestion")
        return []
    try:
        r = requests.get(BASE_URL, timeout=30)
        r.raise_for_status()
        data = r.json().get("response", {}).get("data", [])
        records = []
        for d in data:
            iso3 = d.get("iso3166")
            if not iso3 or d.get("value") is None:
                continue
            records.append({
                "iso3": iso3,
                "year": int(d["period"]),
                "oil_production_kbd": float(d["value"])
            })
        return records
    except Exception as exc:
        logger.error(f"[EIA] Error fetching energy data: {exc}")
        return []


def store_energy(records: List[Dict]):
    if not records:
        return
    conn = sqlite3.connect(config.database.path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS country_energy (
            iso3 TEXT,
            year INTEGER,
            oil_production_kbd REAL,
            PRIMARY KEY(iso3, year)
        )"""
    )
    for rec in records:
        cur.execute(
            """INSERT OR REPLACE INTO country_energy (iso3, year, oil_production_kbd)
            VALUES (?,?,?)""",
            (rec["iso3"], rec["year"], rec["oil_production_kbd"])
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    recs = fetch_oil_production()
    store_energy(recs)
    logger.info(f"[EIA] Stored {len(recs)} energy records.")
