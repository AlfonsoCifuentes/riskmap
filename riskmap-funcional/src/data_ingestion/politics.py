"""V-Dem (Varieties of Democracy) and Freedom House indicators ingestion.

Downloads latest CSVs and stores key democratic indicators per country-year in
`country_politics` table for downstream analysis.
Sources:
 • V-Dem: https://www.v-dem.net/
 • Freedom House: https://freedomhouse.org/explore-data
"""

import csv
import io
import zipfile
import requests
import sqlite3
from typing import List, Dict
from utils.config import config, logger

VDEM_ZIP_URL = "https://www.v-dem.net/media/publications/vdem_2024_csv.zip"  # fictitious placeholder; actual link may differ
FH_CSV_URL = "https://freedomhouse.org/sites/default/files/2023-03/freedom_in_the_world_2023.csv"  # example link


def _download_csv_from_zip(url: str, inner_name: str) -> io.StringIO:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(resp.content))
    with z.open(inner_name) as f:
        return io.StringIO(f.read().decode("utf-8"))


def fetch_vdem() -> List[Dict]:
    try:
        csv_io = _download_csv_from_zip(VDEM_ZIP_URL, "V-Dem-CY-Full+Others-v14.csv")
        reader = csv.DictReader(csv_io)
        rows = []
        for r in reader:
            iso3 = r["country_text_id"]
            year = int(r["year"])
            if iso3 and year >= 1900:
                rows.append({
                    "iso3": iso3,
                    "year": year,
                    "polyarchy": float(r.get("v2x_polyarchy", "")) if r.get("v2x_polyarchy") else None,
                    "lib_dem": float(r.get("v2x_libdem", "")) if r.get("v2x_libdem") else None,
                })
        return rows
    except Exception as exc:
        logger.error(f"[V-Dem] error: {exc}")
        return []


def fetch_freedom_house() -> List[Dict]:
    try:
        resp = requests.get(FH_CSV_URL, timeout=60)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = []
        for r in reader:
            iso3 = r.get("ISO3") or r.get("iso_code")
            year = int(r["Year"]) if r.get("Year") else None
            if iso3 and year:
                rows.append({
                    "iso3": iso3,
                    "year": year,
                    "fh_status": r.get("Status"),
                    "fh_total": float(r.get("Total Score", 0) or 0)
                })
        return rows
    except Exception as exc:
        logger.error(f"[FreedomHouse] error: {exc}")
        return []


def store_politics(vdem_rows: List[Dict], fh_rows: List[Dict]):
    conn = sqlite3.connect(config.database.path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS country_politics (
            iso3 TEXT,
            year INTEGER,
            polyarchy REAL,
            lib_dem REAL,
            fh_status TEXT,
            fh_total REAL,
            PRIMARY KEY(iso3, year)
        )
        """
    )
    for row in vdem_rows:
        cur.execute(
            "INSERT OR IGNORE INTO country_politics (iso3, year, polyarchy, lib_dem) VALUES (?,?,?,?)",
            (row["iso3"], row["year"], row["polyarchy"], row["lib_dem"])
        )
    for row in fh_rows:
        cur.execute(
            "UPDATE country_politics SET fh_status=?, fh_total=? WHERE iso3=? AND year=?",
            (row["fh_status"], row["fh_total"], row["iso3"], row["year"])
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    vdem = fetch_vdem()
    fh = fetch_freedom_house()
    store_politics(vdem, fh)
    logger.info(f"[Politics] Stored {len(vdem)} V-Dem rows and {len(fh)} FreedomHouse rows")
