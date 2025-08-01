"""
Sistema de Etiquetado Automático con GDELT y ACLED
=================================================
Este módulo utiliza bases de datos públicas para crear etiquetas automáticas
y reducir la necesidad de etiquetado manual.
"""

import requests
import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
from concurrent.futures import ThreadPoolExecutor
import zipfile
import io

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeopoliticalAutoLabeler:
    """Sistema de etiquetado automático basado en fuentes externas"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.geolocator = Nominatim(user_agent="geopolitical_analyzer")
        
        # Mapeo de códigos GDELT a nuestras categorías
        self.gdelt_event_mapping = {
            # Conflictos armados
            '18': 'armed_conflict',  # Usar fuerza convencional
            '19': 'armed_conflict',  # Luchar
            '20': 'armed_conflict',  # Usar armas no convencionales
            
            # Tensiones diplomáticas
            '13': 'diplomatic_tension',  # Amenazar
            '14': 'diplomatic_tension',  # Protestar
            '15': 'diplomatic_tension',  # Exigir
            '16': 'diplomatic_tension',  # Desaprobar
            '17': 'diplomatic_tension',  # Rechazar
            
            # Crisis económicas
            '163': 'economic_sanctions',  # Embargo comercial
            '162': 'economic_sanctions',  # Sanciones
            '161': 'economic_sanctions',  # Reducir relaciones
            
            # Actividades diplomáticas positivas
            '01': 'diplomatic_cooperation',  # Hacer declaración pública
            '02': 'diplomatic_cooperation',  # Apelar
            '03': 'diplomatic_cooperation',  # Expresar intención de cooperar
            '04': 'diplomatic_cooperation',  # Consultar
            '05': 'diplomatic_cooperation',  # Compromiso diplomático
            
            # Protestas y manifestaciones
            '145': 'civil_unrest',  # Demostrar o manifestarse
            '1451': 'civil_unrest',  # Demostración por liderazgo político
            '1452': 'civil_unrest',  # Demostración por política
            
            # Terrorismo
            '204': 'terrorism',  # Asesinar
            '203': 'terrorism',  # Amenaza de muerte
            '1383': 'terrorism'   # Amenaza de fuerza
        }
        
        # Mapeo de riesgo basado en tipos de evento
        self.risk_level_mapping = {
            'armed_conflict': 5,
            'terrorism': 5,
            'diplomatic_tension': 4,
            'civil_unrest': 3,
            'economic_sanctions': 3,
            'diplomatic_cooperation': 1
        }
        
        # Regiones de alto riesgo
        self.high_risk_regions = {
            'Ukraine': 5,
            'Russia': 4,
            'Syria': 5,
            'Iraq': 4,
            'Afghanistan': 4,
            'Yemen': 5,
            'Somalia': 4,
            'Sudan': 4,
            'Myanmar': 4,
            'North Korea': 4,
            'Iran': 4,
            'Israel': 3,
            'Palestine': 4,
            'Lebanon': 3,
            'Taiwan': 3,
            'South China Sea': 4,
            'Kashmir': 4
        }
    
    def fetch_gdelt_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Obtener eventos de GDELT para un rango de fechas"""
        events = []
        
        try:
            # GDELT usa formato YYYYMMDD
            start_str = start_date.strftime('%Y%m%d')
            end_str = end_date.strftime('%Y%m%d')
            
            # URL de la API de GDELT
            url = f"https://api.gdeltproject.org/api/v2/doc/doc"
            
            params = {
                'query': 'conflict OR war OR military OR diplomatic OR sanction OR protest',
                'mode': 'artlist',
                'format': 'json',
                'startdatetime': f"{start_str}000000",
                'enddatetime': f"{end_str}235959",
                'maxrecords': 500,
                'sort': 'hybridrel'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'articles' in data:
                for article in data['articles']:
                    event = {
                        'url': article.get('url', ''),
                        'title': article.get('title', ''),
                        'source': article.get('domain', ''),
                        'published_at': self._parse_gdelt_date(article.get('seendate', '')),
                        'tone': float(article.get('tone', 0)),
                        'locations': article.get('locations', []),
                        'persons': article.get('persons', []),
                        'organizations': article.get('organizations', [])
                    }
                    events.append(event)
                    
            logger.info(f"✅ Obtenidos {len(events)} eventos de GDELT")
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de GDELT: {e}")
        
        return events
    
    def fetch_acled_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Obtener eventos de ACLED (Armed Conflict Location & Event Data)"""
        events = []
        
        try:
            # ACLED API - requiere registro gratuito
            # url = "https://api.acleddata.com/acled/read"
            
            # Por ahora, simulamos algunos eventos típicos
            # En producción, sustituir por API real de ACLED
            simulated_events = [
                {
                    'event_type': 'Battles',
                    'sub_event_type': 'Armed clash',
                    'country': 'Ukraine',
                    'location': 'Donetsk',
                    'latitude': 48.0159,
                    'longitude': 37.8031,
                    'event_date': start_date,
                    'fatalities': 15,
                    'notes': 'Armed confrontation between military forces'
                },
                {
                    'event_type': 'Violence against civilians',
                    'sub_event_type': 'Attack',
                    'country': 'Myanmar',
                    'location': 'Yangon',
                    'latitude': 16.8661,
                    'longitude': 96.1951,
                    'event_date': start_date + timedelta(days=1),
                    'fatalities': 8,
                    'notes': 'Military attack on civilian protesters'
                }
            ]
            
            for event in simulated_events:
                processed_event = {
                    'event_type': event['event_type'],
                    'country': event['country'],
                    'location': event['location'],
                    'coordinates': [event['latitude'], event['longitude']],
                    'date': event['event_date'],
                    'severity': min(5, max(1, int(event['fatalities'] / 5) + 1)),
                    'description': event['notes']
                }
                events.append(processed_event)
            
            logger.info(f"✅ Procesados {len(events)} eventos simulados de ACLED")
            
        except Exception as e:
            logger.error(f"❌ Error procesando eventos de ACLED: {e}")
        
        return events
    
    def _parse_gdelt_date(self, date_str: str) -> Optional[datetime]:
        """Parsear fecha de GDELT"""
        try:
            if len(date_str) >= 14:
                return datetime.strptime(date_str[:14], '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
        except:
            pass
        return None
    
    def analyze_text_for_geopolitical_indicators(self, text: str) -> Dict:
        """Analizar texto para indicadores geopolíticos"""
        indicators = {
            'risk_keywords': [],
            'conflict_type': None,
            'intensity_markers': [],
            'location_mentions': [],
            'estimated_risk': 1
        }
        
        text_lower = text.lower()
        
        # Palabras clave de alto riesgo
        high_risk_keywords = [
            'war', 'conflict', 'military', 'attack', 'bombing', 'missile',
            'invasion', 'occupation', 'siege', 'battle', 'combat', 'strike',
            'terrorist', 'explosion', 'casualties', 'killed', 'dead', 'wounded'
        ]
        
        # Palabras clave de riesgo medio
        medium_risk_keywords = [
            'sanction', 'embargo', 'tension', 'dispute', 'crisis', 'protest',
            'demonstration', 'unrest', 'instability', 'threat', 'warning',
            'military exercise', 'deployment', 'buildup'
        ]
        
        # Palabras clave de bajo riesgo (diplomáticas)
        low_risk_keywords = [
            'negotiation', 'agreement', 'cooperation', 'partnership', 'alliance',
            'peace', 'treaty', 'diplomatic', 'dialogue', 'meeting', 'summit'
        ]
        
        # Contar ocurrencias
        high_count = sum(1 for keyword in high_risk_keywords if keyword in text_lower)
        medium_count = sum(1 for keyword in medium_risk_keywords if keyword in text_lower)
        low_count = sum(1 for keyword in low_risk_keywords if keyword in text_lower)
        
        # Determinar nivel de riesgo
        if high_count >= 3:
            indicators['estimated_risk'] = 5
            indicators['conflict_type'] = 'armed_conflict'
        elif high_count >= 1:
            indicators['estimated_risk'] = 4
            indicators['conflict_type'] = 'serious_tension'
        elif medium_count >= 2:
            indicators['estimated_risk'] = 3
            indicators['conflict_type'] = 'political_tension'
        elif medium_count >= 1:
            indicators['estimated_risk'] = 2
            indicators['conflict_type'] = 'diplomatic_issue'
        else:
            indicators['estimated_risk'] = 1
            indicators['conflict_type'] = 'routine_news'
        
        # Ajustar por contexto diplomático positivo
        if low_count > high_count + medium_count:
            indicators['estimated_risk'] = max(1, indicators['estimated_risk'] - 1)
            indicators['conflict_type'] = 'diplomatic_cooperation'
        
        # Extraer menciones de ubicaciones
        location_patterns = [
            r'\b[A-Z][a-z]+ (?:Sea|Ocean|River|Mountains?|Desert)\b',
            r'\b(?:North|South|East|West|Central) [A-Z][a-z]+\b',
            r'\b[A-Z][a-z]+(?:stan|land|burg|grad|istan)\b'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            indicators['location_mentions'].extend(matches)
        
        return indicators
    
    def get_location_risk_factor(self, location: str) -> float:
        """Obtener factor de riesgo basado en la ubicación"""
        location_lower = location.lower()
        
        for region, risk in self.high_risk_regions.items():
            if region.lower() in location_lower:
                return risk / 5.0  # Normalizar a 0-1
        
        return 0.5  # Riesgo neutral por defecto
    
    def auto_label_articles(self, limit: int = 1000) -> int:
        """Etiquetar artículos automáticamente usando múltiples fuentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener artículos sin etiquetar
        cursor.execute('''
            SELECT id, title, content, url, source, published_at
            FROM trained_articles 
            WHERE id NOT IN (SELECT article_id FROM training_labels)
            LIMIT ?
        ''', (limit,))
        
        articles = cursor.fetchall()
        labeled_count = 0
        
        logger.info(f"🏷️ Iniciando etiquetado automático de {len(articles)} artículos...")
        
        for article in articles:
            article_id, title, content, url, source, published_at = article
            
            try:
                # Analizar texto
                text_analysis = self.analyze_text_for_geopolitical_indicators(
                    f"{title} {content}"
                )
                
                # Determinar ubicación
                location = "Unknown"
                for loc_mention in text_analysis['location_mentions']:
                    if loc_mention:
                        location = loc_mention
                        break
                
                # Si no hay ubicación en el texto, intentar extraer del contenido
                if location == "Unknown":
                    location = self._extract_location_from_content(content)
                
                # Calcular nivel de riesgo final
                base_risk = text_analysis['estimated_risk']
                location_factor = self.get_location_risk_factor(location)
                
                # Ajustar riesgo por ubicación
                final_risk = min(5, max(1, int(base_risk * (0.7 + location_factor * 0.6))))
                
                # Determinar tipo de fuente
                source_type = self._classify_source_type(source)
                
                # Insertar etiqueta automática
                cursor.execute('''
                    INSERT INTO training_labels (
                        article_id, manual_risk_level, manual_topic, 
                        manual_location, manual_source_type, labeled_by, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_id, final_risk, text_analysis['conflict_type'],
                    location, source_type, 'auto_labeler',
                    f"Auto-labeled. Keywords: {len(text_analysis['risk_keywords'])}, Location factor: {location_factor:.2f}"
                ))
                
                labeled_count += 1
                
                if labeled_count % 100 == 0:
                    conn.commit()
                    logger.info(f"✅ Procesados {labeled_count} artículos...")
                
            except Exception as e:
                logger.error(f"❌ Error etiquetando artículo {article_id}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Etiquetado automático completado: {labeled_count} artículos")
        return labeled_count
    
    def _extract_location_from_content(self, content: str) -> str:
        """Extraer ubicación del contenido usando patrones geográficos"""
        # Patrones comunes de países y regiones
        country_patterns = [
            r'\bin (\w+(?:\s+\w+)*?),?\s*(?:the|a|an)?\s*(?:country|nation|state|region)',
            r'\b(\w+(?:\s+\w+)*?)\s+(?:government|military|forces|army)',
            r'\b(?:from|in|to|near)\s+(\w+(?:\s+\w+)*?),?\s*(?:where|which|that)',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+(?:capital|city|region|province)'
        ]
        
        for pattern in country_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                location = matches[0].strip()
                # Filtrar palabras comunes que no son ubicaciones
                if location.lower() not in ['the', 'a', 'an', 'this', 'that', 'these', 'those']:
                    return location
        
        return "Unknown"
    
    def _classify_source_type(self, source: str) -> str:
        """Clasificar tipo de fuente de noticias"""
        source_lower = source.lower()
        
        # Medios principales
        mainstream_sources = [
            'reuters', 'bbc', 'cnn', 'ap news', 'associated press',
            'the guardian', 'the times', 'washington post', 'new york times',
            'financial times', 'wall street journal'
        ]
        
        # Think tanks y organizaciones especializadas
        think_tank_sources = [
            'foreign affairs', 'crisis group', 'cfr', 'brookings',
            'chatham house', 'rand', 'csis', 'atlantic council'
        ]
        
        # Fuentes gubernamentales
        government_sources = [
            'gov.', 'military', 'pentagon', 'state department',
            'foreign ministry', 'defense', 'whitehouse'
        ]
        
        # Medios regionales/locales
        regional_sources = [
            'al jazeera', 'rt', 'xinhua', 'tass', 'press tv',
            'times of india', 'south china morning post'
        ]
        
        for mainstream in mainstream_sources:
            if mainstream in source_lower:
                return 'mainstream_media'
        
        for think_tank in think_tank_sources:
            if think_tank in source_lower:
                return 'think_tank'
        
        for gov in government_sources:
            if gov in source_lower:
                return 'government'
        
        for regional in regional_sources:
            if regional in source_lower:
                return 'regional_media'
        
        return 'other'
    
    def create_training_splits(self) -> Dict[str, int]:
        """Crear divisiones de entrenamiento, validación y prueba"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener todos los artículos etiquetados
        cursor.execute('''
            SELECT ta.id, tl.manual_risk_level, tl.manual_topic, 
                   tl.manual_location, tl.manual_source_type
            FROM trained_articles ta
            JOIN training_labels tl ON ta.id = tl.article_id
            WHERE tl.manual_risk_level IS NOT NULL
        ''')
        
        labeled_articles = cursor.fetchall()
        
        # Crear splits estratificados
        np.random.seed(42)
        indices = np.random.permutation(len(labeled_articles))
        
        # 70% entrenamiento, 15% validación, 15% prueba
        train_size = int(0.7 * len(labeled_articles))
        val_size = int(0.15 * len(labeled_articles))
        
        train_indices = indices[:train_size]
        val_indices = indices[train_size:train_size + val_size]
        test_indices = indices[train_size + val_size:]
        
        # Crear tabla de splits si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_splits (
                article_id INTEGER PRIMARY KEY,
                split_type TEXT,
                FOREIGN KEY (article_id) REFERENCES trained_articles (id)
            )
        ''')
        
        # Limpiar splits anteriores
        cursor.execute('DELETE FROM training_splits')
        
        # Insertar nuevos splits
        for idx in train_indices:
            article_id = labeled_articles[idx][0]
            cursor.execute('INSERT INTO training_splits VALUES (?, ?)', (article_id, 'train'))
        
        for idx in val_indices:
            article_id = labeled_articles[idx][0]
            cursor.execute('INSERT INTO training_splits VALUES (?, ?)', (article_id, 'val'))
        
        for idx in test_indices:
            article_id = labeled_articles[idx][0]
            cursor.execute('INSERT INTO training_splits VALUES (?, ?)', (article_id, 'test'))
        
        conn.commit()
        conn.close()
        
        splits_info = {
            'train': len(train_indices),
            'validation': len(val_indices),
            'test': len(test_indices),
            'total': len(labeled_articles)
        }
        
        logger.info(f"✅ Splits de entrenamiento creados: {splits_info}")
        return splits_info
    
    def export_training_data(self) -> Tuple[str, str]:
        """Exportar datos de entrenamiento en formato CSV y JSON"""
        conn = sqlite3.connect(self.db_path)
        
        # Consulta para obtener todos los datos de entrenamiento
        query = '''
            SELECT 
                ta.id, ta.title, ta.content, ta.url, ta.source, ta.published_at,
                ta.image_path, ta.image_description,
                tl.manual_risk_level, tl.manual_topic, tl.manual_location, 
                tl.manual_source_type, tl.notes,
                ts.split_type
            FROM trained_articles ta
            JOIN training_labels tl ON ta.id = tl.article_id
            LEFT JOIN training_splits ts ON ta.id = ts.article_id
            WHERE tl.manual_risk_level IS NOT NULL
            ORDER BY ta.id
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Exportar como CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = f"training_data_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        
        # Exportar como JSON para el modelo
        json_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_samples': len(df),
                'train_samples': len(df[df['split_type'] == 'train']),
                'val_samples': len(df[df['split_type'] == 'val']),
                'test_samples': len(df[df['split_type'] == 'test'])
            },
            'data': df.to_dict('records')
        }
        
        json_path = f"training_data_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Datos de entrenamiento exportados:")
        logger.info(f"  📄 CSV: {csv_path}")
        logger.info(f"  📄 JSON: {json_path}")
        logger.info(f"  📊 Total muestras: {len(df)}")
        
        return csv_path, json_path

def main():
    """Función principal para ejecutar el etiquetado automático"""
    db_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\trained_analysis.db"
    
    # Crear etiquetador automático
    auto_labeler = GeopoliticalAutoLabeler(db_path)
    
    # Ejecutar etiquetado automático
    labeled_count = auto_labeler.auto_label_articles(limit=1500)
    
    # Crear splits de entrenamiento
    splits_info = auto_labeler.create_training_splits()
    
    # Exportar datos de entrenamiento
    csv_path, json_path = auto_labeler.export_training_data()
    
    print(f"\n✅ Etiquetado automático completado!")
    print(f"🏷️ Artículos etiquetados: {labeled_count}")
    print(f"📊 Splits: {splits_info}")
    print(f"📁 Archivos generados: {csv_path}, {json_path}")

if __name__ == "__main__":
    main()
