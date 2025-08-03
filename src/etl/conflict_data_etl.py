"""
ETL de Conflictos Geopolíticos
Implementación del pipeline ETL basado en los conceptos del notebook chatGPT_talks_1.ipynb

Este módulo implementa:
- Extracción de datos de múltiples fuentes (ACLED, UCDP, GDELT, Kaggle, HuggingFace)
- Transformación y normalización de datos
- Carga en base de datos SQLite
- Detección de eventos críticos
- Sistema de alertas automáticas
"""

import os
import json
import sqlite3
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from pathlib import Path
import hashlib
import time
from dataclasses import dataclass

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ETLConfig:
    """Configuración del pipeline ETL"""
    sources: List[str]
    date_range: Dict[str, str]
    regions: List[str] = None
    conflict_types: List[str] = None
    enable_alerts: bool = True
    alert_threshold: int = 50
    batch_size: int = 100
    max_retries: int = 3
    
class ConflictDataETL:
    """
    Pipeline ETL para datos de conflictos geopolíticos
    Basado en el diseño del notebook chatGPT_talks_1.ipynb
    """
    
    def __init__(self, db_path: str = None, config: ETLConfig = None):
        self.db_path = db_path or os.getenv('DATABASE_PATH', './data/geopolitical_intel.db')
        self.config = config or ETLConfig(
            sources=['acled', 'gdelt'],
            date_range={
                'start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d')
            }
        )
        
        # Credenciales desde variables de entorno
        self.acled_api_key = os.getenv('ACLED_API_KEY')
        self.planet_api_key = os.getenv('PLANET_API_KEY')
        
        # Datasets disponibles basados en el notebook
        self.datasets_catalog = {
            "primary_sources": {
                "acled": {
                    "name": "ACLED - Armed Conflict Location & Event Data Project",
                    "url": "https://api.acleddata.com/acled/read",
                    "type": "api",
                    "requires_key": True,
                    "description": "Eventos de conflictos armados, violencia y protestas georreferenciados"
                },
                "ucdp": {
                    "name": "UCDP - Uppsala Conflict Data Program", 
                    "url": "https://ucdp.uu.se/downloads/ged/ged231-csv.zip",
                    "type": "download",
                    "requires_key": False,
                    "description": "Datos de conflictos armados y muertes relacionadas con batallas"
                },
                "gdelt": {
                    "name": "GDELT - Global Database of Events, Language, and Tone",
                    "url": "http://api.gdeltproject.org/api/v2/doc/doc",
                    "type": "api", 
                    "requires_key": False,
                    "description": "Base de datos global de eventos en tiempo real"
                }
            },
            "specific_conflicts": {
                "ukraine_russia": [
                    "https://www.kaggle.com/datasets/hskhawaja/russia-ukraine-conflict",
                    "https://www.kaggle.com/datasets/tariqsays/russiaukraine-conflict-twitter-dataset"
                ],
                "middle_east": [
                    "https://huggingface.co/datasets/enkryptai/deepseek-geopolitical-bias-dataset"
                ],
                "drc_m23": [
                    "https://acleddata.com/api",
                    "https://ucdp.uu.se/country/180"
                ],
                "india_pakistan": [
                    "https://www.kaggle.com/datasets/aarchikunchal/indiapakistan-conflict-escalation-dataset"
                ]
            }
        }
        
        self.statistics = {
            'extracted_records': 0,
            'transformed_records': 0,
            'loaded_records': 0,
            'critical_events': [],
            'errors': []
        }
        
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Crear tablas necesarias para el ETL"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla principal de eventos de conflicto
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conflict_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT UNIQUE,
                        event_date DATE,
                        country TEXT,
                        region TEXT,
                        latitude REAL,
                        longitude REAL,
                        event_type TEXT,
                        sub_event_type TEXT,
                        actor1 TEXT,
                        actor2 TEXT,
                        fatalities INTEGER DEFAULT 0,
                        source_url TEXT,
                        article_text TEXT,
                        data_source TEXT,
                        is_critical BOOLEAN DEFAULT 0,
                        severity_score REAL DEFAULT 0.0,
                        confidence_score REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla de eventos críticos para alertas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS critical_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT,
                        alert_type TEXT,
                        severity TEXT,
                        fatalities INTEGER,
                        description TEXT,
                        location TEXT,
                        detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        notified BOOLEAN DEFAULT 0,
                        FOREIGN KEY (event_id) REFERENCES conflict_events (event_id)
                    )
                """)
                
                # Tabla de estadísticas ETL
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS etl_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id TEXT UNIQUE,
                        config_json TEXT,
                        status TEXT,
                        extracted_count INTEGER DEFAULT 0,
                        transformed_count INTEGER DEFAULT 0,
                        loaded_count INTEGER DEFAULT 0,
                        critical_events_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        started_at DATETIME,
                        completed_at DATETIME,
                        error_message TEXT
                    )
                """)
                
                # Índices para optimizar consultas
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_events_date ON conflict_events (event_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_events_country ON conflict_events (country)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_events_critical ON conflict_events (is_critical)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_critical_events_severity ON critical_events (severity)")
                
                conn.commit()
                logger.info("✅ Tablas ETL creadas/verificadas correctamente")
                
        except Exception as e:
            logger.error(f"Error creando tablas ETL: {e}")
            raise
    
    def get_datasets_catalog(self) -> Dict:
        """Obtener catálogo de datasets disponibles"""
        return self.datasets_catalog
    
    def fetch_acled_data(self) -> pd.DataFrame:
        """
        Extraer datos de ACLED API
        Basado en el ejemplo del notebook
        """
        if not self.acled_api_key:
            logger.warning("⚠️ ACLED API key no configurada")
            return pd.DataFrame()
        
        try:
            logger.info("🔄 Extrayendo datos de ACLED...")
            
            url = "https://api.acleddata.com/acled/read"
            params = {
                'key': self.acled_api_key,
                'event_date': f"{self.config.date_range['start']}|{self.config.date_range['end']}",
                'format': 'json',
                'limit': 1000
            }
            
            # Añadir filtros por región si están especificados
            if self.config.regions:
                params['region'] = '|'.join(self.config.regions)
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            df = pd.DataFrame(data.get('data', []))
            
            if not df.empty:
                # Normalizar columnas según esquema del notebook
                df = self._normalize_acled_data(df)
                logger.info(f"✅ ACLED: {len(df)} registros extraídos")
            else:
                logger.warning("⚠️ ACLED: No se encontraron datos")
            
            self.statistics['extracted_records'] += len(df)
            return df
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos de ACLED: {e}")
            self.statistics['errors'].append(f"ACLED extraction error: {str(e)}")
            return pd.DataFrame()
    
    def fetch_gdelt_data(self) -> pd.DataFrame:
        """
        Extraer datos de GDELT API
        Basado en el ejemplo del notebook
        """
        try:
            logger.info("🔄 Extrayendo datos de GDELT...")
            
            # Query para conflictos según notebook
            query = "conflict OR war OR protest OR violence OR attack"
            url = "http://api.gdeltproject.org/api/v2/doc/doc"
            params = {
                'query': query,
                'format': 'json',
                'startdatetime': self.config.date_range['start'].replace('-', '') + '000000',
                'enddatetime': self.config.date_range['end'].replace('-', '') + '235959',
                'maxrecords': 500
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            if articles:
                df = pd.DataFrame(articles)
                df = self._normalize_gdelt_data(df)
                logger.info(f"✅ GDELT: {len(df)} registros extraídos")
            else:
                df = pd.DataFrame()
                logger.warning("⚠️ GDELT: No se encontraron datos")
            
            self.statistics['extracted_records'] += len(df)
            return df
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos de GDELT: {e}")
            self.statistics['errors'].append(f"GDELT extraction error: {str(e)}")
            return pd.DataFrame()
    
    def _normalize_acled_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar datos de ACLED al esquema unificado"""
        try:
            normalized_df = pd.DataFrame()
            
            # Mapeo de columnas ACLED al esquema unificado
            if not df.empty:
                normalized_df['event_id'] = df.get('data_date', '') + '_acled_' + df.get('event_id', '').astype(str)
                normalized_df['event_date'] = pd.to_datetime(df.get('event_date', ''), errors='coerce')
                normalized_df['country'] = df.get('country', '')
                normalized_df['region'] = df.get('region', '')
                normalized_df['latitude'] = pd.to_numeric(df.get('latitude', 0), errors='coerce')
                normalized_df['longitude'] = pd.to_numeric(df.get('longitude', 0), errors='coerce')
                normalized_df['event_type'] = df.get('event_type', '')
                normalized_df['sub_event_type'] = df.get('sub_event_type', '')
                normalized_df['actor1'] = df.get('actor1', '')
                normalized_df['actor2'] = df.get('actor2', '')
                normalized_df['fatalities'] = pd.to_numeric(df.get('fatalities', 0), errors='coerce').fillna(0)
                normalized_df['source_url'] = df.get('source', '')
                normalized_df['article_text'] = df.get('notes', '')
                normalized_df['data_source'] = 'acled'
                
                # Calcular criticidad según umbral del notebook
                normalized_df['is_critical'] = normalized_df['fatalities'] >= self.config.alert_threshold
                normalized_df['severity_score'] = self._calculate_severity_score(normalized_df)
                normalized_df['confidence_score'] = 0.9  # ACLED tiene alta confiabilidad
            
            return normalized_df
            
        except Exception as e:
            logger.error(f"Error normalizando datos ACLED: {e}")
            return pd.DataFrame()
    
    def _normalize_gdelt_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar datos de GDELT al esquema unificado"""
        try:
            normalized_df = pd.DataFrame()
            
            if not df.empty:
                # Generar IDs únicos para GDELT
                normalized_df['event_id'] = 'gdelt_' + pd.Series(range(len(df))).astype(str) + '_' + df.get('url', '').apply(lambda x: hashlib.md5(str(x).encode()).hexdigest()[:8])
                normalized_df['event_date'] = pd.to_datetime(df.get('seendate', ''), errors='coerce')
                normalized_df['country'] = df.get('domain', '').str.split('.').str[-1].str.upper()  # Extraer país del dominio
                normalized_df['region'] = ''  # GDELT no proporciona región directamente
                normalized_df['latitude'] = 0.0  # GDELT no proporciona coords en esta API
                normalized_df['longitude'] = 0.0
                normalized_df['event_type'] = 'Media Report'
                normalized_df['sub_event_type'] = df.get('sourcecollection', '')
                normalized_df['actor1'] = ''
                normalized_df['actor2'] = ''
                normalized_df['fatalities'] = 0  # GDELT no proporciona fatalidades directamente
                normalized_df['source_url'] = df.get('url', '')
                normalized_df['article_text'] = df.get('title', '') + ' ' + df.get('socialimage', '')
                normalized_df['data_source'] = 'gdelt'
                
                # Para GDELT, usar tono como proxy de criticidad
                tone = pd.to_numeric(df.get('tone', 0), errors='coerce').fillna(0)
                normalized_df['is_critical'] = tone < -5  # Tono muy negativo
                normalized_df['severity_score'] = abs(tone) / 10  # Normalizar tono a 0-1
                normalized_df['confidence_score'] = 0.6  # GDELT tiene confiabilidad media
            
            return normalized_df
            
        except Exception as e:
            logger.error(f"Error normalizando datos GDELT: {e}")
            return pd.DataFrame()
    
    def _calculate_severity_score(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcular score de severidad basado en fatalidades y tipo de evento
        Implementa la lógica del notebook para clasificación de eventos
        """
        try:
            severity = pd.Series(0.0, index=df.index)
            
            # Score basado en fatalidades (logarítmico para suavizar)
            fatalities = df.get('fatalities', 0)
            severity += (fatalities.apply(lambda x: min(1.0, (x / 100) ** 0.5)) if len(fatalities) > 0 else 0)
            
            # Score basado en tipo de evento
            event_type = df.get('event_type', '')
            high_severity_types = ['Violence against civilians', 'Battles', 'Explosions/Remote violence']
            medium_severity_types = ['Riots', 'Protests']
            
            for i, et in enumerate(event_type):
                if et in high_severity_types:
                    severity.iloc[i] += 0.3
                elif et in medium_severity_types:
                    severity.iloc[i] += 0.1
            
            return severity.clip(0, 1)  # Normalizar entre 0 y 1
            
        except Exception as e:
            logger.error(f"Error calculando severity score: {e}")
            return pd.Series(0.0, index=df.index)
    
    def transform_data(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Transformar y consolidar datos de múltiples fuentes
        Implementa el paso Transform del pipeline ETL del notebook
        """
        try:
            logger.info("🔄 Transformando datos...")
            
            if not dataframes or all(df.empty for df in dataframes):
                logger.warning("⚠️ No hay datos para transformar")
                return pd.DataFrame()
            
            # Concatenar todos los dataframes
            combined_df = pd.concat([df for df in dataframes if not df.empty], ignore_index=True)
            
            if combined_df.empty:
                logger.warning("⚠️ DataFrame combinado está vacío")
                return combined_df
            
            # Limpieza y validación según notebook
            original_count = len(combined_df)
            
            # 1. Eliminar duplicados por event_id
            combined_df = combined_df.drop_duplicates(subset=['event_id'], keep='first')
            logger.info(f"🧹 Duplicados eliminados: {original_count - len(combined_df)}")
            
            # 2. Validar fechas
            combined_df = combined_df.dropna(subset=['event_date'])
            combined_df = combined_df[combined_df['event_date'] >= pd.Timestamp('2020-01-01')]
            
            # 3. Validar coordenadas geográficas
            valid_coords = (
                (combined_df['latitude'].between(-90, 90)) & 
                (combined_df['longitude'].between(-180, 180))
            )
            combined_df = combined_df[valid_coords | ((combined_df['latitude'] == 0) & (combined_df['longitude'] == 0))]
            
            # 4. Limpiar texto
            text_columns = ['country', 'region', 'event_type', 'sub_event_type', 'actor1', 'actor2']
            for col in text_columns:
                if col in combined_df.columns:
                    combined_df[col] = combined_df[col].astype(str).str.strip()
            
            # 5. Normalizar nombres de países
            combined_df['country'] = self._normalize_country_names(combined_df['country'])
            
            # 6. Calcular métricas adicionales
            combined_df['processing_date'] = datetime.now()
            combined_df['data_quality_score'] = self._calculate_data_quality_score(combined_df)
            
            self.statistics['transformed_records'] = len(combined_df)
            logger.info(f"✅ Transformación completada: {len(combined_df)} registros válidos")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"❌ Error en transformación de datos: {e}")
            self.statistics['errors'].append(f"Transform error: {str(e)}")
            return pd.DataFrame()
    
    def _normalize_country_names(self, countries: pd.Series) -> pd.Series:
        """Normalizar nombres de países a formato estándar"""
        country_mapping = {
            'United States of America': 'United States',
            'USA': 'United States',
            'US': 'United States',
            'UK': 'United Kingdom',
            'DRC': 'Democratic Republic of Congo',
            'DR Congo': 'Democratic Republic of Congo',
            'Congo DRC': 'Democratic Republic of Congo',
            'Russia': 'Russian Federation',
            'Syria': 'Syrian Arab Republic',
            'Iran': 'Islamic Republic of Iran',
            'North Korea': 'Democratic People\'s Republic of Korea',
            'South Korea': 'Republic of Korea'
        }
        
        return countries.replace(country_mapping)
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """Calcular score de calidad de datos"""
        try:
            quality_score = pd.Series(1.0, index=df.index)
            
            # Penalizar por campos faltantes
            required_fields = ['event_date', 'country', 'event_type']
            for field in required_fields:
                if field in df.columns:
                    missing_mask = df[field].isna() | (df[field] == '')
                    quality_score[missing_mask] -= 0.2
            
            # Bonificar por coordenadas válidas
            has_coords = (df['latitude'] != 0) | (df['longitude'] != 0)
            quality_score[has_coords] += 0.1
            
            # Bonificar por texto descriptivo
            has_text = df['article_text'].str.len() > 50
            quality_score[has_text] += 0.1
            
            return quality_score.clip(0, 1)
            
        except Exception as e:
            logger.error(f"Error calculando calidad de datos: {e}")
            return pd.Series(0.5, index=df.index)
    
    def load_data(self, df: pd.DataFrame) -> bool:
        """
        Cargar datos transformados en la base de datos
        Implementa el paso Load del pipeline ETL del notebook
        """
        try:
            if df.empty:
                logger.warning("⚠️ No hay datos para cargar")
                return True
            
            logger.info(f"🔄 Cargando {len(df)} registros en la base de datos...")
            
            with sqlite3.connect(self.db_path) as conn:
                # Preparar datos para inserción
                df_to_load = df.copy()
                df_to_load['created_at'] = datetime.now()
                df_to_load['updated_at'] = datetime.now()
                
                # Insertar o actualizar registros
                df_to_load.to_sql('conflict_events', conn, if_exists='append', index=False, method='multi')
                
                self.statistics['loaded_records'] = len(df)
                logger.info(f"✅ {len(df)} registros cargados exitosamente")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error cargando datos: {e}")
            self.statistics['errors'].append(f"Load error: {str(e)}")
            return False
    
    def detect_critical_events(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detectar eventos críticos para alertas
        Implementa la lógica de detección del notebook
        """
        try:
            logger.info("🔍 Detectando eventos críticos...")
            
            critical_events = []
            
            if df.empty:
                return critical_events
            
            # Filtrar eventos críticos según criterios del notebook
            critical_mask = (
                (df['is_critical'] == True) |
                (df['fatalities'] >= self.config.alert_threshold) |
                (df['severity_score'] >= 0.7)
            )
            
            critical_df = df[critical_mask]
            
            for _, event in critical_df.iterrows():
                severity = 'high'
                if event['fatalities'] >= 100:
                    severity = 'critical'
                elif event['fatalities'] >= self.config.alert_threshold:
                    severity = 'high'
                elif event['severity_score'] >= 0.7:
                    severity = 'medium'
                
                critical_event = {
                    'event_id': event['event_id'],
                    'alert_type': 'high_fatality' if event['fatalities'] >= self.config.alert_threshold else 'high_severity',
                    'severity': severity,
                    'fatalities': int(event['fatalities']),
                    'description': f"{event['event_type']} - {event['sub_event_type']}",
                    'location': f"{event['country']}, {event['region']}".strip(', '),
                    'detected_at': datetime.now().isoformat(),
                    'coordinates': [float(event['latitude']), float(event['longitude'])] if event['latitude'] != 0 or event['longitude'] != 0 else None,
                    'data_source': event['data_source'],
                    'confidence': float(event['confidence_score'])
                }
                
                critical_events.append(critical_event)
            
            # Guardar eventos críticos en la base de datos
            if critical_events:
                self._save_critical_events(critical_events)
            
            self.statistics['critical_events'] = critical_events
            logger.info(f"🚨 {len(critical_events)} eventos críticos detectados")
            
            return critical_events
            
        except Exception as e:
            logger.error(f"❌ Error detectando eventos críticos: {e}")
            self.statistics['errors'].append(f"Critical events detection error: {str(e)}")
            return []
    
    def _save_critical_events(self, critical_events: List[Dict]):
        """Guardar eventos críticos en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for event in critical_events:
                    cursor.execute("""
                        INSERT OR REPLACE INTO critical_events 
                        (event_id, alert_type, severity, fatalities, description, location, detected_at, notified)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event['event_id'],
                        event['alert_type'], 
                        event['severity'],
                        event['fatalities'],
                        event['description'],
                        event['location'],
                        event['detected_at'],
                        0  # not notified yet
                    ))
                
                conn.commit()
                logger.info(f"💾 {len(critical_events)} eventos críticos guardados")
                
        except Exception as e:
            logger.error(f"Error guardando eventos críticos: {e}")
    
    def run_full_pipeline(self, run_id: str = None) -> Dict[str, Any]:
        """
        Ejecutar el pipeline ETL completo
        Implementa el flujo completo del notebook: Extract -> Transform -> Load -> Detect
        """
        run_id = run_id or f"etl_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"🚀 Iniciando pipeline ETL: {run_id}")
            start_time = datetime.now()
            
            # Guardar configuración del run
            self._save_etl_run(run_id, 'running', start_time)
            
            # Reset statistics
            self.statistics = {
                'extracted_records': 0,
                'transformed_records': 0,
                'loaded_records': 0,
                'critical_events': [],
                'errors': []
            }
            
            # EXTRACT PHASE
            logger.info("📥 FASE 1: EXTRACCIÓN DE DATOS")
            extracted_dataframes = []
            
            if 'acled' in self.config.sources:
                acled_data = self.fetch_acled_data()
                if not acled_data.empty:
                    extracted_dataframes.append(acled_data)
            
            if 'gdelt' in self.config.sources:
                gdelt_data = self.fetch_gdelt_data()
                if not gdelt_data.empty:
                    extracted_dataframes.append(gdelt_data)
            
            if not extracted_dataframes:
                raise Exception("No se pudieron extraer datos de ninguna fuente")
            
            # TRANSFORM PHASE
            logger.info("🔄 FASE 2: TRANSFORMACIÓN DE DATOS")
            transformed_data = self.transform_data(extracted_dataframes)
            
            if transformed_data.empty:
                raise Exception("No hay datos después de la transformación")
            
            # LOAD PHASE
            logger.info("💾 FASE 3: CARGA DE DATOS")
            load_success = self.load_data(transformed_data)
            
            if not load_success:
                raise Exception("Error en la carga de datos")
            
            # DETECT CRITICAL EVENTS
            logger.info("🚨 FASE 4: DETECCIÓN DE EVENTOS CRÍTICOS")
            critical_events = self.detect_critical_events(transformed_data)
            
            # Finalizar run
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results = {
                'run_id': run_id,
                'status': 'completed',
                'duration_seconds': duration,
                'extracted_records': self.statistics['extracted_records'],
                'transformed_records': self.statistics['transformed_records'], 
                'loaded_records': self.statistics['loaded_records'],
                'critical_events_count': len(critical_events),
                'critical_events': critical_events,
                'errors': self.statistics['errors'],
                'started_at': start_time.isoformat(),
                'completed_at': end_time.isoformat()
            }
            
            # Actualizar registro del run
            self._update_etl_run(run_id, 'completed', results, end_time)
            
            logger.info(f"✅ Pipeline ETL completado exitosamente: {run_id}")
            logger.info(f"📊 Estadísticas: {self.statistics['extracted_records']} extraídos → {self.statistics['transformed_records']} transformados → {self.statistics['loaded_records']} cargados")
            logger.info(f"🚨 Eventos críticos detectados: {len(critical_events)}")
            
            return results
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error en pipeline ETL: {error_msg}")
            
            results = {
                'run_id': run_id,
                'status': 'failed',
                'error': error_msg,
                'statistics': self.statistics,
                'started_at': start_time.isoformat(),
                'failed_at': datetime.now().isoformat()
            }
            
            # Actualizar registro del run
            self._update_etl_run(run_id, 'failed', results, datetime.now(), error_msg)
            
            return results
    
    def _save_etl_run(self, run_id: str, status: str, start_time: datetime):
        """Guardar información inicial del run ETL"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO etl_runs (run_id, config_json, status, started_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    run_id,
                    json.dumps(self.config.__dict__),
                    status,
                    start_time
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error guardando run ETL: {e}")
    
    def _update_etl_run(self, run_id: str, status: str, results: Dict, end_time: datetime, error_msg: str = None):
        """Actualizar información del run ETL al completar"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE etl_runs SET 
                        status = ?, 
                        extracted_count = ?, 
                        transformed_count = ?, 
                        loaded_count = ?,
                        critical_events_count = ?,
                        error_count = ?,
                        completed_at = ?,
                        error_message = ?
                    WHERE run_id = ?
                """, (
                    status,
                    results.get('extracted_records', 0),
                    results.get('transformed_records', 0),
                    results.get('loaded_records', 0),
                    results.get('critical_events_count', 0),
                    len(results.get('errors', [])),
                    end_time,
                    error_msg,
                    run_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error actualizando run ETL: {e}")
    
    def get_etl_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas generales del ETL"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas de runs
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_runs,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_runs,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
                        SUM(loaded_count) as total_records_loaded,
                        SUM(critical_events_count) as total_critical_events,
                        MAX(started_at) as last_run_date
                    FROM etl_runs
                """)
                run_stats = cursor.fetchone()
                
                # Estadísticas de eventos por país
                cursor.execute("""
                    SELECT country, COUNT(*) as event_count
                    FROM conflict_events 
                    WHERE event_date >= date('now', '-30 days')
                    GROUP BY country 
                    ORDER BY event_count DESC 
                    LIMIT 10
                """)
                country_stats = cursor.fetchall()
                
                # Eventos críticos recientes
                cursor.execute("""
                    SELECT severity, COUNT(*) as count
                    FROM critical_events 
                    WHERE detected_at >= datetime('now', '-7 days')
                    GROUP BY severity
                """)
                critical_stats = cursor.fetchall()
                
                return {
                    'etl_runs': {
                        'total': run_stats[0] or 0,
                        'successful': run_stats[1] or 0,
                        'failed': run_stats[2] or 0,
                        'success_rate': ((run_stats[1] or 0) / max((run_stats[0] or 0), 1)) * 100,
                        'total_records_processed': run_stats[3] or 0,
                        'total_critical_events': run_stats[4] or 0,
                        'last_run': run_stats[5]
                    },
                    'country_distribution': [
                        {'country': row[0], 'events': row[1]} 
                        for row in country_stats
                    ],
                    'critical_events_by_severity': [
                        {'severity': row[0], 'count': row[1]} 
                        for row in critical_stats
                    ],
                    'data_sources': list(self.config.sources),
                    'alert_threshold': self.config.alert_threshold
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas ETL: {e}")
            return {}
    
    def get_recent_critical_events(self, limit: int = 20) -> List[Dict]:
        """Obtener eventos críticos recientes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ce.*, ev.event_date, ev.country, ev.region, ev.latitude, ev.longitude, ev.data_source
                    FROM critical_events ce
                    LEFT JOIN conflict_events ev ON ce.event_id = ev.event_id
                    ORDER BY ce.detected_at DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                events = []
                for row in rows:
                    event_dict = dict(zip(columns, row))
                    events.append(event_dict)
                
                return events
                
        except Exception as e:
            logger.error(f"Error obteniendo eventos críticos: {e}")
            return []

# Función de utilidad para crear una instancia ETL configurada
def create_etl_instance(
    sources: List[str] = None,
    days_back: int = 7, 
    alert_threshold: int = 50,
    db_path: str = None
) -> ConflictDataETL:
    """
    Crear una instancia ETL configurada
    
    Args:
        sources: Lista de fuentes de datos ['acled', 'gdelt', 'ucdp']
        days_back: Número de días hacia atrás para extraer datos
        alert_threshold: Umbral de fatalidades para alertas
        db_path: Ruta de la base de datos
    """
    config = ETLConfig(
        sources=sources or ['acled', 'gdelt'],
        date_range={
            'start': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d'),
            'end': datetime.now().strftime('%Y-%m-%d')
        },
        alert_threshold=alert_threshold
    )
    
    return ConflictDataETL(db_path=db_path, config=config)

if __name__ == "__main__":
    # Ejemplo de uso
    etl = create_etl_instance(
        sources=['acled', 'gdelt'],
        days_back=7,
        alert_threshold=50
    )
    
    # Ejecutar pipeline completo
    results = etl.run_full_pipeline()
    
    print("🎉 Resultados del ETL:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
