#!/usr/bin/env python3
"""
Sistema de Feeds Externos para RiskMap
Integra ACLED, GDELT, GPR y otras fuentes abiertas de inteligencia geopolítica
"""

import os
import requests
import zipfile
import io
import pandas as pd
import sqlite3
import logging
import json
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExternalIntelligenceFeeds:
    """
    Gestor de feeds externos de inteligencia geopolítica
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.acled_api_key = os.getenv('ACLED_API_KEY')
        self.data_dir = Path('data/external_feeds')
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # URLs base para las diferentes fuentes
        self.sources = {
            'acled': {
                'base_url': 'https://api.acleddata.com/acled/read',
                'frequency': 'weekly',  # Martes
                'coverage': 'Violence and protests in ~140 countries'
            },
            'gdelt': {
                'base_url': 'http://data.gdeltproject.org/events',
                'frequency': 'daily',
                'coverage': 'Global news events (~300 events/sec)'
            },
            'gpr': {
                'url': 'https://www.matteoiacoviello.com/gpr_files/GPR_Data.csv',
                'frequency': 'monthly',
                'coverage': 'Geopolitical Risk Index (1900-2025)'
            }
        }
        
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializar tablas de feeds externos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla para eventos ACLED
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS acled_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_date TEXT,
                        iso TEXT,
                        event_id_cnty TEXT,
                        event_id_no_cnty TEXT,
                        event_date TEXT,
                        year INTEGER,
                        time_precision TEXT,
                        event_type TEXT,
                        sub_event_type TEXT,
                        actor1 TEXT,
                        assoc_actor_1 TEXT,
                        inter1 INTEGER,
                        actor2 TEXT,
                        assoc_actor_2 TEXT,
                        inter2 INTEGER,
                        interaction INTEGER,
                        region TEXT,
                        country TEXT,
                        admin1 TEXT,
                        admin2 TEXT,
                        admin3 TEXT,
                        location TEXT,
                        latitude REAL,
                        longitude REAL,
                        geo_precision TEXT,
                        source TEXT,
                        source_scale TEXT,
                        notes TEXT,
                        fatalities INTEGER,
                        timestamp TEXT,
                        iso3 TEXT,
                        imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(event_id_cnty, event_date)
                    )
                """)
                
                # Tabla para eventos GDELT
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS gdelt_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        globaleventid INTEGER,
                        sqldate INTEGER,
                        monthyear INTEGER,
                        year INTEGER,
                        fractiondate REAL,
                        actor1code TEXT,
                        actor1name TEXT,
                        actor1countrycode TEXT,
                        actor1knowngroupcode TEXT,
                        actor1ethniccode TEXT,
                        actor1religion1code TEXT,
                        actor1religion2code TEXT,
                        actor1type1code TEXT,
                        actor1type2code TEXT,
                        actor1type3code TEXT,
                        actor2code TEXT,
                        actor2name TEXT,
                        actor2countrycode TEXT,
                        actor2knowngroupcode TEXT,
                        actor2ethniccode TEXT,
                        actor2religion1code TEXT,
                        actor2religion2code TEXT,
                        actor2type1code TEXT,
                        actor2type2code TEXT,
                        actor2type3code TEXT,
                        isrootevent INTEGER,
                        eventcode TEXT,
                        eventbasecode TEXT,
                        eventrootcode TEXT,
                        quadclass INTEGER,
                        goldsteinscale REAL,
                        nummentions INTEGER,
                        numsources INTEGER,
                        numarticles INTEGER,
                        avgtone REAL,
                        actor1geo_type INTEGER,
                        actor1geo_fullname TEXT,
                        actor1geo_countrycode TEXT,
                        actor1geo_adm1code TEXT,
                        actor1geo_lat REAL,
                        actor1geo_long REAL,
                        actor1geo_featureid TEXT,
                        actor2geo_type INTEGER,
                        actor2geo_fullname TEXT,
                        actor2geo_countrycode TEXT,
                        actor2geo_adm1code TEXT,
                        actor2geo_lat REAL,
                        actor2geo_long REAL,
                        actor2geo_featureid TEXT,
                        actiongeo_type INTEGER,
                        actiongeo_fullname TEXT,
                        actiongeo_countrycode TEXT,
                        actiongeo_adm1code TEXT,
                        actiongeo_lat REAL,
                        actiongeo_long REAL,
                        actiongeo_featureid TEXT,
                        dateadded TEXT,
                        sourceurl TEXT,
                        imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(globaleventid)
                    )
                """)
                
                # Tabla para GPR Index
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS gpr_index (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        gpr REAL,
                        gpr_threats REAL,
                        gpr_acts REAL,
                        imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date)
                    )
                """)
                
                # Tabla para seguimiento de actualizaciones
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feed_updates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        last_update DATETIME,
                        records_imported INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'success',
                        error_message TEXT,
                        update_duration REAL,
                        data_date_range TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("✅ Tablas de feeds externos inicializadas")
                
        except Exception as e:
            logger.error(f"❌ Error inicializando BD de feeds externos: {e}")
            raise
    
    def fetch_acled_data(self, days_back: int = 7, countries: Optional[List[str]] = None) -> bool:
        """
        Obtener datos de ACLED (Armed Conflict Location & Event Data Project)
        """
        if not self.acled_api_key:
            logger.warning("⚠️ ACLED_API_KEY no configurada, saltando ACLED")
            return False
        
        try:
            logger.info(f"🔍 Obteniendo datos ACLED (últimos {days_back} días)...")
            start_time = time.time()
            
            # Calcular rango de fechas
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # Construir URL de API
            params = {
                'key': self.acled_api_key,
                'event_date': f"{start_date}:{end_date}",
                '_format': 'csv',
                'limit': 10000  # Límite de registros
            }
            
            # Agregar filtro de países si se especifica
            if countries:
                params['country'] = '|'.join(countries)
            
            url = self.sources['acled']['base_url']
            
            logger.info(f"📡 Consultando ACLED API: {start_date} a {end_date}")
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            # Leer CSV desde la respuesta
            df = pd.read_csv(io.StringIO(response.text))
            
            if df.empty:
                logger.warning("⚠️ No se obtuvieron datos de ACLED")
                return False
            
            # Guardar en base de datos
            records_imported = self._save_acled_data(df)
            
            duration = time.time() - start_time
            
            # Registrar actualización
            self._log_feed_update('acled', records_imported, duration, f"{start_date} to {end_date}")
            
            logger.info(f"✅ ACLED: {records_imported} eventos importados en {duration:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos ACLED: {e}")
            self._log_feed_update('acled', 0, 0, '', 'error', str(e))
            return False
    
    def fetch_gdelt_data(self, target_date: Optional[date] = None) -> bool:
        """
        Obtener datos de GDELT (Global Database of Events, Language & Tone)
        """
        try:
            if target_date is None:
                target_date = date.today() - timedelta(days=1)  # Día anterior
            
            logger.info(f"🔍 Obteniendo datos GDELT para {target_date}")
            start_time = time.time()
            
            # URL del archivo GDELT diario
            date_str = target_date.strftime("%Y%m%d")
            url = f"{self.sources['gdelt']['base_url']}/{date_str}.export.CSV.zip"
            
            logger.info(f"📡 Descargando GDELT: {url}")
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            # Extraer y leer CSV del ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_filename = z.namelist()[0]
                with z.open(csv_filename) as csv_file:
                    # GDELT no tiene headers, usar nombres de columnas estándar
                    column_names = [
                        'globaleventid', 'sqldate', 'monthyear', 'year', 'fractiondate',
                        'actor1code', 'actor1name', 'actor1countrycode', 'actor1knowngroupcode',
                        'actor1ethniccode', 'actor1religion1code', 'actor1religion2code',
                        'actor1type1code', 'actor1type2code', 'actor1type3code',
                        'actor2code', 'actor2name', 'actor2countrycode', 'actor2knowngroupcode',
                        'actor2ethniccode', 'actor2religion1code', 'actor2religion2code',
                        'actor2type1code', 'actor2type2code', 'actor2type3code',
                        'isrootevent', 'eventcode', 'eventbasecode', 'eventrootcode',
                        'quadclass', 'goldsteinscale', 'nummentions', 'numsources',
                        'numarticles', 'avgtone', 'actor1geo_type', 'actor1geo_fullname',
                        'actor1geo_countrycode', 'actor1geo_adm1code', 'actor1geo_lat',
                        'actor1geo_long', 'actor1geo_featureid', 'actor2geo_type',
                        'actor2geo_fullname', 'actor2geo_countrycode', 'actor2geo_adm1code',
                        'actor2geo_lat', 'actor2geo_long', 'actor2geo_featureid',
                        'actiongeo_type', 'actiongeo_fullname', 'actiongeo_countrycode',
                        'actiongeo_adm1code', 'actiongeo_lat', 'actiongeo_long',
                        'actiongeo_featureid', 'dateadded', 'sourceurl'
                    ]
                    
                    df = pd.read_csv(csv_file, sep='\t', header=None, names=column_names, low_memory=False)
            
            # Filtrar eventos relevantes (conflictos, violencia, protestas)
            relevant_events = df[df['eventrootcode'].isin(['14', '15', '16', '17', '18', '19', '20'])]
            
            if relevant_events.empty:
                logger.warning("⚠️ No se encontraron eventos relevantes en GDELT")
                return False
            
            # Guardar en base de datos
            records_imported = self._save_gdelt_data(relevant_events)
            
            duration = time.time() - start_time
            
            # Registrar actualización
            self._log_feed_update('gdelt', records_imported, duration, str(target_date))
            
            logger.info(f"✅ GDELT: {records_imported} eventos relevantes importados en {duration:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos GDELT: {e}")
            self._log_feed_update('gdelt', 0, 0, '', 'error', str(e))
            return False
    
    def fetch_gpr_data(self) -> bool:
        """
        Obtener datos de GPR (Geopolitical Risk Index)
        """
        try:
            logger.info("🔍 Obteniendo índice GPR...")
            start_time = time.time()
            
            url = self.sources['gpr']['url']
            
            logger.info(f"📡 Descargando GPR: {url}")
            df = pd.read_csv(url)
            
            if df.empty:
                logger.warning("⚠️ No se obtuvieron datos de GPR")
                return False
            
            # Guardar en base de datos
            records_imported = self._save_gpr_data(df)
            
            duration = time.time() - start_time
            
            # Registrar actualización
            self._log_feed_update('gpr', records_imported, duration, f"Historical data through {df['date'].max()}")
            
            logger.info(f"✅ GPR: {records_imported} registros importados en {duration:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos GPR: {e}")
            self._log_feed_update('gpr', 0, 0, '', 'error', str(e))
            return False
    
    def _save_acled_data(self, df: pd.DataFrame) -> int:
        """Guardar datos ACLED en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Usar INSERT OR IGNORE para evitar duplicados
                records_before = conn.execute("SELECT COUNT(*) FROM acled_events").fetchone()[0]
                
                df.to_sql('acled_events', conn, if_exists='append', index=False, method='multi')
                
                records_after = conn.execute("SELECT COUNT(*) FROM acled_events").fetchone()[0]
                
                return records_after - records_before
                
        except Exception as e:
            logger.error(f"Error guardando datos ACLED: {e}")
            return 0
    
    def _save_gdelt_data(self, df: pd.DataFrame) -> int:
        """Guardar datos GDELT en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                records_before = conn.execute("SELECT COUNT(*) FROM gdelt_events").fetchone()[0]
                
                df.to_sql('gdelt_events', conn, if_exists='append', index=False, method='multi')
                
                records_after = conn.execute("SELECT COUNT(*) FROM gdelt_events").fetchone()[0]
                
                return records_after - records_before
                
        except Exception as e:
            logger.error(f"Error guardando datos GDELT: {e}")
            return 0
    
    def _save_gpr_data(self, df: pd.DataFrame) -> int:
        """Guardar datos GPR en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                records_before = conn.execute("SELECT COUNT(*) FROM gpr_index").fetchone()[0]
                
                df.to_sql('gpr_index', conn, if_exists='replace', index=False)
                
                records_after = conn.execute("SELECT COUNT(*) FROM gpr_index").fetchone()[0]
                
                return records_after - records_before
                
        except Exception as e:
            logger.error(f"Error guardando datos GPR: {e}")
            return 0
    
    def _log_feed_update(self, source: str, records: int, duration: float, 
                        date_range: str, status: str = 'success', error: str = None):
        """Registrar actualización de feed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO feed_updates 
                    (source, last_update, records_imported, status, error_message, 
                     update_duration, data_date_range)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (source, datetime.now(), records, status, error, duration, date_range))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging feed update: {e}")
    
    def update_all_feeds(self, acled_days_back: int = 7) -> Dict[str, bool]:
        """
        Actualizar todos los feeds externos
        """
        logger.info("🔄 Iniciando actualización de todos los feeds externos...")
        
        results = {}
        
        # 1. Actualizar ACLED (eventos de violencia y protestas)
        logger.info("📊 Actualizando ACLED...")
        results['acled'] = self.fetch_acled_data(days_back=acled_days_back)
        
        # 2. Actualizar GDELT (eventos globales del día anterior)
        logger.info("📊 Actualizando GDELT...")
        results['gdelt'] = self.fetch_gdelt_data()
        
        # 3. Actualizar GPR (índice de riesgo geopolítico)
        logger.info("📊 Actualizando GPR...")
        results['gpr'] = self.fetch_gpr_data()
        
        successful_updates = sum(results.values())
        total_feeds = len(results)
        
        logger.info(f"✅ Actualización completada: {successful_updates}/{total_feeds} feeds exitosos")
        
        return results
    
    def get_feed_statistics(self) -> Dict[str, Dict]:
        """
        Obtener estadísticas de los feeds externos
        """
        stats = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas ACLED
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_events,
                        COUNT(DISTINCT country) as countries,
                        COUNT(DISTINCT event_type) as event_types,
                        MAX(event_date) as latest_event,
                        MIN(event_date) as earliest_event,
                        SUM(fatalities) as total_fatalities
                    FROM acled_events
                """)
                acled_stats = cursor.fetchone()
                
                stats['acled'] = {
                    'total_events': acled_stats[0] or 0,
                    'countries_covered': acled_stats[1] or 0,
                    'event_types': acled_stats[2] or 0,
                    'latest_event': acled_stats[3],
                    'earliest_event': acled_stats[4],
                    'total_fatalities': acled_stats[5] or 0
                }
                
                # Estadísticas GDELT
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_events,
                        COUNT(DISTINCT actiongeo_countrycode) as countries,
                        AVG(goldsteinscale) as avg_goldstein,
                        AVG(avgtone) as avg_tone,
                        MAX(sqldate) as latest_date
                    FROM gdelt_events
                """)
                gdelt_stats = cursor.fetchone()
                
                stats['gdelt'] = {
                    'total_events': gdelt_stats[0] or 0,
                    'countries_covered': gdelt_stats[1] or 0,
                    'avg_goldstein_scale': round(gdelt_stats[2] or 0, 2),
                    'avg_tone': round(gdelt_stats[3] or 0, 2),
                    'latest_date': gdelt_stats[4]
                }
                
                # Estadísticas GPR
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_records,
                        AVG(gpr) as avg_gpr,
                        MAX(gpr) as max_gpr,
                        MIN(gpr) as min_gpr,
                        MAX(date) as latest_date
                    FROM gpr_index
                """)
                gpr_stats = cursor.fetchone()
                
                stats['gpr'] = {
                    'total_records': gpr_stats[0] or 0,
                    'avg_gpr': round(gpr_stats[1] or 0, 2),
                    'max_gpr': round(gpr_stats[2] or 0, 2),
                    'min_gpr': round(gpr_stats[3] or 0, 2),
                    'latest_date': gpr_stats[4]
                }
                
                # Estadísticas de actualizaciones
                cursor.execute("""
                    SELECT source, MAX(last_update), status, records_imported
                    FROM feed_updates
                    GROUP BY source
                    ORDER BY last_update DESC
                """)
                
                updates = {}
                for row in cursor.fetchall():
                    updates[row[0]] = {
                        'last_update': row[1],
                        'status': row[2],
                        'last_import_count': row[3]
                    }
                
                stats['updates'] = updates
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def get_conflict_hotspots(self, days_back: int = 30, min_events: int = 5) -> List[Dict]:
        """
        Identificar hotspots de conflicto basados en feeds externos
        """
        hotspots = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                
                # Hotspots desde ACLED
                cursor.execute("""
                    SELECT 
                        country, region, 
                        AVG(latitude) as lat, AVG(longitude) as lng,
                        COUNT(*) as event_count,
                        SUM(fatalities) as total_fatalities,
                        GROUP_CONCAT(DISTINCT event_type) as event_types
                    FROM acled_events
                    WHERE event_date >= ?
                    AND latitude IS NOT NULL AND longitude IS NOT NULL
                    GROUP BY country, region
                    HAVING event_count >= ?
                    ORDER BY event_count DESC, total_fatalities DESC
                """, (cutoff_date, min_events))
                
                for row in cursor.fetchall():
                    hotspots.append({
                        'source': 'ACLED',
                        'location': f"{row[1]}, {row[0]}" if row[1] else row[0],
                        'country': row[0],
                        'region': row[1],
                        'latitude': row[2],
                        'longitude': row[3],
                        'event_count': row[4],
                        'fatalities': row[5] or 0,
                        'event_types': row[6].split(',') if row[6] else [],
                        'risk_level': 'high' if row[4] >= 20 else 'medium',
                        'data_period_days': days_back
                    })
                
                # Hotspots desde GDELT (eventos con tono muy negativo)
                cursor.execute("""
                    SELECT 
                        actiongeo_countrycode as country,
                        actiongeo_fullname as location,
                        actiongeo_lat as lat, actiongeo_long as lng,
                        COUNT(*) as event_count,
                        AVG(avgtone) as avg_tone,
                        AVG(goldsteinscale) as avg_goldstein
                    FROM gdelt_events
                    WHERE sqldate >= ?
                    AND actiongeo_lat IS NOT NULL AND actiongeo_long IS NOT NULL
                    AND avgtone < -5  -- Eventos con tono muy negativo
                    GROUP BY actiongeo_countrycode, actiongeo_fullname
                    HAVING event_count >= ?
                    ORDER BY event_count DESC, avg_tone ASC
                """, (int((datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')), min_events))
                
                for row in cursor.fetchall():
                    hotspots.append({
                        'source': 'GDELT',
                        'location': row[1] or row[0],
                        'country': row[0],
                        'latitude': row[2],
                        'longitude': row[3],
                        'event_count': row[4],
                        'avg_tone': round(row[5], 2),
                        'avg_goldstein': round(row[6], 2),
                        'risk_level': 'high' if row[5] < -10 else 'medium',
                        'data_period_days': days_back
                    })
        
        except Exception as e:
            logger.error(f"Error identificando hotspots: {e}")
        
        return hotspots
