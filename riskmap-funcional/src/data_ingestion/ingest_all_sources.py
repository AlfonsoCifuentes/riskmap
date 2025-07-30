"""
Script de ingesta automática de fuentes OSINT y desastres naturales para Riskmap.
Descarga datos de GDELT, USGS, EMSC, GDACS y los almacena en la base de datos.
Puede ejecutarse periódicamente para mantener el sistema actualizado.
"""

from .real_sources import (
    fetch_gdelt_events, fetch_usgs_earthquakes, fetch_emsc_earthquakes,
    fetch_gdacs_events, fetch_copernicus_alerts, fetch_healthmap_alerts, store_events
)
from utils.config import logger

def run_all_sources_ingest():
    """Ejecuta ingesta de todas las fuentes reales"""
    logger.info("Iniciando ingesta de fuentes reales...")
    # GDELT
    gdelt_events = fetch_gdelt_events(days=1)
    store_events(gdelt_events, table="events")
    logger.info(f"GDELT: {len(gdelt_events)} eventos almacenados.")
    # USGS
    usgs_events = fetch_usgs_earthquakes(hours=24)
    store_events(usgs_events, table="events")
    logger.info(f"USGS: {len(usgs_events)} terremotos almacenados.")
    # EMSC
    emsc_events = fetch_emsc_earthquakes()
    store_events(emsc_events, table="events")
    logger.info(f"EMSC: {len(emsc_events)} terremotos almacenados.")
    # GDACS
    gdacs_events = fetch_gdacs_events()
    store_events(gdacs_events, table="events")
    logger.info(f"GDACS: {len(gdacs_events)} desastres almacenados.")
    # Copernicus EMS Alerts
    copernicus_events = fetch_copernicus_alerts()
    store_events(copernicus_events, table="events")
    logger.info(f"Copernicus EMS: {len(copernicus_events)} alertas almacenadas.")
    # HealthMap Alerts
    health_events = fetch_healthmap_alerts()
    store_events(health_events, table="events")
    logger.info(f"HealthMap: {len(health_events)} eventos de salud almacenados.")
    logger.info("Ingesta completada.")

if __name__ == "__main__":
    run_all_sources_ingest()
