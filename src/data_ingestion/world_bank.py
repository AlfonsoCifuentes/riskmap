"""World Bank data ingestion for economic indicators.
Fetches GDP (current US$), GDP per capita, Population and Unemployment rate for all available countries.
Stores in SQLite table `country_indicators` with ISO3 code and year.
World Bank API docs: https://data.worldbank.org/developers
"""

import requests
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import time
import itertools

from utils.config import config, logger

INDICATORS = {
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "NY.GDP.PCAP.CD": "gdp_per_capita_usd",
    "SP.POP.TOTL": "population_total",
    "SL.UEM.TOTL.ZS": "unemployment_percent"
}

API_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&per_page=60"


def fetch_indicator(indicator: str, iso3: str) -> List[Dict[str, Any]]:
    """Fetch time-series list of dicts for a single country/indicator."""
    try:
        resp = requests.get(API_URL.format(country=iso3, indicator=indicator), timeout=20)
        if resp.status_code != 200:
            return []
        raw = resp.json()
        if len(raw) < 2:
            return []
        return [r for r in raw[1] if r["value"] is not None]
    except Exception:
        return []


def fetch_all_countries() -> List[str]:
    """Return list of ISO3 codes from World Bank API"""
    resp = requests.get("https://api.worldbank.org/v2/country?format=json&per_page=400", timeout=20)
    raw = resp.json()
    return [c["id"] for c in raw[1]]


def store_indicator_rows(rows: List[Dict[str, Any]], indicator_code: str):
    if not rows:
        return
    conn = sqlite3.connect(config.database.path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS country_indicators (
            country_iso TEXT,
            year INTEGER,
            indicator TEXT,
            value REAL,
            PRIMARY KEY(country_iso, year, indicator)
        )
        """
    )
    for r in rows:
        cur.execute(
            """INSERT OR REPLACE INTO country_indicators (country_iso, year, indicator, value)
            VALUES (?,?,?,?)""",
            (r["countryiso3code"], int(r["date"]), indicator_code, float(r["value"]))
        )
    conn.commit()
    conn.close()


def ingest_world_bank():
    countries = fetch_all_countries()
    logger.info(f"[WorldBank] Ingesting indicators for {len(countries)} countries …")
    for iso3 in countries:
        for ind, mapped in INDICATORS.items():
            rows = fetch_indicator(ind, iso3)
            store_indicator_rows(rows, mapped)
            time.sleep(0.1)  # be gentle with API
    logger.info("[WorldBank] Ingestion completed.")


if __name__ == "__main__":
    ingest_world_bank()
