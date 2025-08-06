#!/usr/bin/env python3
"""
Sistema de Ingesta GDELT mejorado y robusto
Utiliza la API de GDELT en lugar de archivos CSV
"""

import requests
import sqlite3
import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GDELTIngestor:
    """Sistema robusto de ingesta de datos GDELT"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.api_base = "https://api.gdeltproject.org/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RiskMap-GDELT-Client/1.0'
        })
        
        # Configurar Groq para geolocalización
        load_dotenv()
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_client = None
        
        if self.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
                logger.info("✅ Groq configurado para geolocalización GDELT")
            except Exception as e:
                logger.warning(f"⚠️ Groq no disponible para geolocalización: {e}")
                self.groq_client = None
        
        # Inicializar traductor
        try:
            self.translator = GoogleTranslator(source='auto', target='en')
            logger.info("✅ Traductor GoogleTranslator inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando traductor: {e}")
            self.translator = None
        
        self._initialize_gdelt_table()
    
    def _initialize_gdelt_table(self):
        """Inicializar tabla GDELT optimizada"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Crear tabla GDELT optimizada para conflictos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS gdelt_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        global_event_id TEXT UNIQUE,
                        event_date TEXT,
                        event_type TEXT,
                        event_code TEXT,
                        actor1_name TEXT,
                        actor1_country TEXT,
                        actor2_name TEXT,
                        actor2_country TEXT,
                        action_location TEXT,
                        action_country TEXT,
                        action_latitude REAL,
                        action_longitude REAL,
                        quad_class INTEGER,
                        goldstein_scale REAL,
                        num_mentions INTEGER,
                        avg_tone REAL,
                        source_url TEXT,
                        article_title TEXT,
                        article_content TEXT,
                        article_date TEXT,
                        article_source TEXT,
                        conflict_type TEXT,
                        severity_score REAL,
                        imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_conflict INTEGER DEFAULT 0,
                        UNIQUE(global_event_id, event_date)
                    )
                """)
                
                # Índices para consultas rápidas
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_gdelt_conflict 
                    ON gdelt_events(is_conflict, event_date)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_gdelt_location 
                    ON gdelt_events(action_latitude, action_longitude)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_gdelt_date 
                    ON gdelt_events(event_date)
                """)
                
                conn.commit()
                logger.info("✅ Tabla GDELT inicializada correctamente")
                
        except Exception as e:
            logger.error(f"❌ Error inicializando tabla GDELT: {e}")
            raise
    
    def fetch_conflict_events(self, days_back: int = 7, max_records: int = 1000) -> bool:
        """
        Obtener eventos de conflicto recientes usando la API de GDELT
        """
        try:
            logger.info(f"🔍 Obteniendo eventos GDELT de conflicto (últimos {days_back} días)")
            start_time = time.time()
            
            # Palabras clave de conflicto
            conflict_keywords = [
                "conflict", "war", "battle", "attack", "violence", "military",
                "terrorism", "protest", "riot", "bombing", "shooting", "crisis",
                "siege", "invasion", "occupation", "ceasefire", "peace talks"
            ]
            
            # Usar la API de documentos GDELT
            events_imported = 0
            
            for keyword in conflict_keywords[:5]:  # Limitar para evitar rate limits
                try:
                    events_batch = self._fetch_events_by_keyword(keyword, days_back, max_records // 5)
                    imported_batch = self._save_events_to_db(events_batch, keyword)
                    events_imported += imported_batch
                    
                    # Pausa entre requests para evitar rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error obteniendo eventos para '{keyword}': {e}")
                    continue
            
            duration = time.time() - start_time
            logger.info(f"✅ GDELT: {events_imported} eventos de conflicto importados en {duration:.2f}s")
            
            return events_imported > 0
            
        except Exception as e:
            logger.error(f"❌ Error en ingesta GDELT: {e}")
            return False
    
    def _fetch_events_by_keyword(self, keyword: str, days_back: int, max_records: int) -> List[Dict]:
        """Obtener eventos por palabra clave usando la API GDELT"""
        try:
            # Calcular rango de fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Parámetros para la API de documentos GDELT
            params = {
                'query': keyword,
                'mode': 'ArtList',
                'maxrecords': min(max_records, 250),  # GDELT API limit
                'format': 'json',
                'startdatetime': start_date.strftime('%Y%m%d%H%M%S'),
                'enddatetime': end_date.strftime('%Y%m%d%H%M%S')
            }
            
            url = f"{self.api_base}/doc/doc"
            
            logger.debug(f"📡 Consultando GDELT API para '{keyword}'")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            events = []
            for article in articles:
                event = self._parse_article_to_event(article, keyword)
                if event:
                    events.append(event)
            
            logger.debug(f"✅ Obtenidos {len(events)} eventos para '{keyword}'")
            return events
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Error en request GDELT para '{keyword}': {e}")
            return []
        except Exception as e:
            logger.warning(f"⚠️ Error procesando respuesta GDELT para '{keyword}': {e}")
            return []
    
    def _parse_article_to_event(self, article: Dict, keyword: str) -> Optional[Dict]:
        """Convertir artículo GDELT a evento estructurado"""
        try:
            # Extraer información del artículo
            title = article.get('title', '')
            url = article.get('url', '')
            date_seen = article.get('seendate', '')
            source_url = article.get('socialurl', article.get('url', ''))
            
            # Generar ID único
            event_id = f"gdelt_{keyword}_{hash(url)}_{date_seen}"
            
            # Determinar tipo de conflicto basado en el título
            conflict_type = self._classify_conflict_type(title, keyword)
            
            # Calcular score de severidad
            severity_score = self._calculate_severity_score(title, keyword)
            
            # Extraer ubicación del título y obtener coordenadas
            location_info = self._extract_and_geolocate(title)
            
            event = {
                'global_event_id': event_id,
                'event_date': date_seen,
                'event_type': conflict_type,
                'event_code': keyword.upper(),
                'actor1_name': article.get('domain', ''),
                'actor1_country': article.get('sourcecountry', ''),
                'actor2_name': '',
                'actor2_country': '',
                'action_location': location_info.get('location', article.get('sourcelang', '')),
                'action_country': location_info.get('country', article.get('sourcecountry', '')),
                'action_latitude': location_info.get('latitude'),
                'action_longitude': location_info.get('longitude'),
                'quad_class': 4,  # Conflict/Violence category
                'goldstein_scale': -severity_score,  # Negative for conflicts
                'num_mentions': 1,
                'avg_tone': -5.0,  # Negative tone for conflicts
                'source_url': source_url,
                'article_title': title,
                'article_content': title,  # GDELT API doesn't provide full content
                'article_date': date_seen,
                'article_source': article.get('domain', ''),
                'conflict_type': conflict_type,
                'severity_score': severity_score,
                'is_conflict': 1
            }
            
            return event
            
        except Exception as e:
            logger.warning(f"⚠️ Error parseando artículo GDELT: {e}")
            return None
    
    def _translate_title(self, title: str) -> str:
        """Traducir título a inglés para mejor procesamiento"""
        try:
            if not self.translator:
                return title
            
            # Detectar si ya está en inglés (patrones básicos)
            if self._is_likely_english(title):
                return title
            
            # Traducir a inglés
            translated = self.translator.translate(title)
            logger.debug(f"🔄 Traducido: '{title[:50]}...' -> '{translated[:50]}...'")
            return translated if translated else title
            
        except Exception as e:
            logger.warning(f"⚠️ Error traduciendo '{title[:30]}...': {e}")
            return title
    
    def _is_likely_english(self, text: str) -> bool:
        """Detectar si el texto probablemente ya está en inglés"""
        # Palabras comunes en inglés
        english_words = {
            'the', 'and', 'in', 'of', 'to', 'a', 'is', 'for', 'on', 'with', 
            'war', 'conflict', 'attack', 'violence', 'crisis', 'protest'
        }
        
        words = text.lower().split()
        english_count = sum(1 for word in words if word in english_words)
        
        # Si más del 20% son palabras en inglés, probablemente ya está en inglés
        return len(words) > 0 and (english_count / len(words)) > 0.2
    
    def _extract_and_geolocate(self, title: str) -> Dict:
        """Extraer ubicación del título y obtener coordenadas usando Groq"""
        try:
            # Traducir título a inglés para mejor procesamiento
            title_en = self._translate_title(title)
            
            # Extraer ubicaciones usando regex
            locations = self._extract_locations_from_text(title_en)
            
            if not locations:
                return {'location': '', 'country': '', 'latitude': None, 'longitude': None}
            
            # Usar la primera ubicación encontrada
            primary_location = locations[0]
            
            # Obtener coordenadas usando Groq si está disponible
            if self.groq_client:
                coords = self._get_coordinates_from_groq(primary_location)
                if coords:
                    return {
                        'location': primary_location,
                        'country': coords.get('country', ''),
                        'latitude': coords.get('latitude'),
                        'longitude': coords.get('longitude')
                    }
            
            # Fallback sin coordenadas
            return {
                'location': primary_location,
                'country': '',
                'latitude': None,
                'longitude': None
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error en geolocalización: {e}")
            return {'location': '', 'country': '', 'latitude': None, 'longitude': None}
    
    def _extract_locations_from_text(self, text: str) -> List[str]:
        """Extraer ubicaciones geográficas del texto usando patrones mejorados"""
        locations = []
        
        # Patrones específicos para ubicaciones comunes en noticias
        patterns = [
            # Ciudad, País format
            r'\b([A-Z][a-zA-Z]+),\s*([A-Z][a-zA-Z]+)\b',
            # "in Location" format  
            r'\bin\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b',
            # "from Location" format
            r'\bfrom\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b',
            # Ubicaciones conocidas (países, capitales, regiones)
            r'\b(Gaza|Israel|Palestine|Ukraine|Russia|Syria|Iraq|Iran|Afghanistan|Yemen|Libya|Sudan|Somalia|Nigeria|Mali|Chad|Turkey|Lebanon|Jordan|Egypt|Morocco|Algeria|Tunisia|Venezuela|Colombia|Mexico|China|India|Pakistan|Bangladesh|Myanmar|Thailand|Philippines|North Korea|South Korea|Taiwan|Japan)\b',
        ]
        
        # Palabras a excluir definitivamente
        exclude_words = self._get_exclude_words()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            locations.extend(self._process_matches(matches, exclude_words))
        
        return self._remove_duplicates(locations)[:2]  # Máximo 2 ubicaciones
    
    def _get_exclude_words(self) -> set:
        """Obtener palabras a excluir de ubicaciones - versión mejorada"""
        return {
            # Artículos y conectores
            'the', 'and', 'or', 'but', 'for', 'with', 'by', 'at', 'on', 'in', 'to', 'from', 'of', 'a', 'an',
            # Tiempo
            'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 
            'september', 'october', 'november', 'december', 'monday', 'tuesday', 'wednesday',
            'thursday', 'friday', 'saturday', 'sunday', 'today', 'yesterday', 'tomorrow',
            # Personas y organizaciones
            'president', 'minister', 'government', 'army', 'military', 'police', 'forces',
            'party', 'group', 'people', 'leader', 'official', 'spokesperson', 'commander',
            # Eventos y conceptos
            'war', 'conflict', 'crisis', 'attack', 'violence', 'protest', 'demonstration',
            'news', 'report', 'statement', 'meeting', 'conference', 'summit', 'talks',
            # Otros
            'this', 'that', 'new', 'old', 'first', 'last', 'next', 'previous', 'current',
            'pride', 'apple', 'germany', 'europe'  # Casos específicos encontrados en datos
        }
    
    def _process_matches(self, matches: List, exclude_words: set) -> List[str]:
        """Procesar matches de regex para extraer ubicaciones válidas"""
        locations = []
        for match in matches:
            if isinstance(match, tuple):
                for location in match:
                    if self._is_valid_location(location, exclude_words):
                        locations.append(location)
            else:
                if self._is_valid_location(match, exclude_words):
                    locations.append(match)
        return locations
    
    def _is_valid_location(self, location: str, exclude_words: set) -> bool:
        """Verificar si una cadena es una ubicación válida"""
        return (location and 
                location.lower() not in exclude_words and 
                len(location) > 2 and
                not location.isdigit())
    
    def _remove_duplicates(self, locations: List[str]) -> List[str]:
        """Remover duplicados manteniendo orden"""
        seen = set()
        unique_locations = []
        for loc in locations:
            if loc not in seen:
                seen.add(loc)
                unique_locations.append(loc)
        return unique_locations
    
    def _get_coordinates_from_groq(self, location: str) -> Optional[Dict]:
        """Obtener coordenadas de una ubicación usando Groq"""
        try:
            if not self.groq_client:
                return None
            
            prompt = f"""
            Para la ubicación "{location}", proporciona SOLO las coordenadas geográficas exactas en formato JSON.
            
            Responde únicamente con un JSON válido en este formato exacto:
            {{
                "latitude": número_decimal,
                "longitude": número_decimal,
                "country": "nombre_del_país",
                "precision": "city|region|country"
            }}
            
            Si no puedes determinar la ubicación exacta, responde con null.
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Modelo actualizado
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Limpiar formato markdown si existe
            if '```json' in response_text:
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                coords_data = json.loads(json_match.group())
                
                if coords_data and 'latitude' in coords_data and 'longitude' in coords_data:
                    return {
                        'latitude': float(coords_data['latitude']),
                        'longitude': float(coords_data['longitude']),
                        'country': coords_data.get('country', ''),
                        'precision': coords_data.get('precision', 'unknown')
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo coordenadas de Groq para '{location}': {e}")
            return None
    
    def _classify_conflict_type(self, title: str, keyword: str) -> str:
        """Clasificar tipo de conflicto basado en el título y keyword"""
        title_lower = title.lower()
        
        # Usar keyword como indicador base
        if keyword in ['war', 'battle', 'military']:
            return 'military_conflict'
        elif keyword in ['protest', 'riot']:
            return 'civil_unrest'
        elif keyword in ['terrorism', 'attack', 'bombing']:
            return 'violence'
        elif keyword in ['crisis', 'emergency']:
            return 'crisis'
        
        # Fallback basado en título
        if any(word in title_lower for word in ['war', 'battle', 'invasion', 'military']):
            return 'military_conflict'
        elif any(word in title_lower for word in ['protest', 'riot', 'demonstration']):
            return 'civil_unrest'
        elif any(word in title_lower for word in ['terrorism', 'attack', 'bombing', 'shooting']):
            return 'violence'
        elif any(word in title_lower for word in ['crisis', 'emergency', 'disaster']):
            return 'crisis'
        else:
            return 'general_conflict'
    
    def _calculate_severity_score(self, title: str, keyword: str) -> float:
        """Calcular score de severidad del conflicto basado en título y keyword"""
        title_lower = title.lower()
        
        # Score base según keyword
        keyword_severity = {
            'war': 4.0,
            'terrorism': 3.5,
            'bombing': 3.5,
            'attack': 3.0,
            'crisis': 2.5,
            'protest': 2.0,
            'conflict': 2.5
        }
        
        score = keyword_severity.get(keyword, 1.0)
        
        # Palabras que aumentan severidad en el título
        high_severity_words = ['war', 'attack', 'bombing', 'killed', 'dead', 'casualties', 'violence']
        medium_severity_words = ['conflict', 'crisis', 'protest', 'military']
        
        for word in high_severity_words:
            if word in title_lower:
                score += 2.0
        
        for word in medium_severity_words:
            if word in title_lower:
                score += 1.0
        
        return min(score, 10.0)  # Max score of 10
    
    def _save_events_to_db(self, events: List[Dict], keyword: str) -> int:
        """Guardar eventos en la base de datos"""
        if not events:
            return 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                imported_count = 0
                for event in events:
                    try:
                        # Usar INSERT OR IGNORE para evitar duplicados
                        cursor.execute("""
                            INSERT OR IGNORE INTO gdelt_events (
                                global_event_id, event_date, event_type, event_code,
                                actor1_name, actor1_country, actor2_name, actor2_country,
                                action_location, action_country, action_latitude, action_longitude,
                                quad_class, goldstein_scale, num_mentions, avg_tone,
                                source_url, article_title, article_content, article_date,
                                article_source, conflict_type, severity_score, is_conflict
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            event['global_event_id'], event['event_date'], event['event_type'], event['event_code'],
                            event['actor1_name'], event['actor1_country'], event['actor2_name'], event['actor2_country'],
                            event['action_location'], event['action_country'], event['action_latitude'], event['action_longitude'],
                            event['quad_class'], event['goldstein_scale'], event['num_mentions'], event['avg_tone'],
                            event['source_url'], event['article_title'], event['article_content'], event['article_date'],
                            event['article_source'], event['conflict_type'], event['severity_score'], event['is_conflict']
                        ))
                        
                        if cursor.rowcount > 0:
                            imported_count += 1
                            
                    except sqlite3.IntegrityError:
                        # Evento duplicado, continuar
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️ Error guardando evento individual: {e}")
                        continue
                
                conn.commit()
                logger.debug(f"✅ Guardados {imported_count} eventos para '{keyword}'")
                return imported_count
                
        except Exception as e:
            logger.error(f"❌ Error guardando eventos GDELT: {e}")
            return 0
    
    def get_recent_conflicts(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """Obtener conflictos recientes de la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        global_event_id, event_date, event_type, conflict_type,
                        action_location, action_country, action_latitude, action_longitude,
                        severity_score, article_title, source_url
                    FROM gdelt_events 
                    WHERE is_conflict = 1 
                    AND event_date >= date('now', '-{} days')
                    AND action_latitude IS NOT NULL 
                    AND action_longitude IS NOT NULL
                    ORDER BY severity_score DESC, event_date DESC
                    LIMIT ?
                """.format(days), (limit,))
                
                conflicts = []
                for row in cursor.fetchall():
                    conflicts.append({
                        'event_id': row[0],
                        'date': row[1],
                        'event_type': row[2],
                        'conflict_type': row[3],
                        'location': row[4],
                        'country': row[5],
                        'latitude': row[6],
                        'longitude': row[7],
                        'severity': row[8],
                        'title': row[9],
                        'source_url': row[10]
                    })
                
                return conflicts
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo conflictos GDELT: {e}")
            return []
    
    def update_feeds(self) -> bool:
        """Ejecutar actualización completa de feeds GDELT"""
        try:
            logger.info("🔄 Iniciando actualización de feeds GDELT...")
            
            # Obtener eventos de conflicto de los últimos 3 días
            success = self.fetch_conflict_events(days_back=3, max_records=500)
            
            if success:
                # Verificar cuántos eventos tenemos
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM gdelt_events WHERE is_conflict = 1")
                    total_conflicts = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT COUNT(*) FROM gdelt_events 
                        WHERE is_conflict = 1 AND event_date >= date('now', '-7 days')
                    """)
                    recent_conflicts = cursor.fetchone()[0]
                    
                logger.info(f"📊 GDELT: {total_conflicts} conflictos totales, {recent_conflicts} recientes")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en actualización GDELT: {e}")
            return False

def test_gdelt_ingestor():
    """Función de test para verificar la ingesta GDELT"""
    ingestor = GDELTIngestor('./data/geopolitical_intel.db')
    
    print("🧪 Probando ingesta GDELT...")
    success = ingestor.update_feeds()
    
    if success:
        conflicts = ingestor.get_recent_conflicts(days=7, limit=10)
        print(f"✅ Ingesta exitosa: {len(conflicts)} conflictos recientes encontrados")
        
        for i, conflict in enumerate(conflicts[:5]):
            print(f"  {i+1}. {conflict['country']}: {conflict['title'][:60]}...")
            print(f"     Coords: ({conflict['latitude']:.4f}, {conflict['longitude']:.4f})")
            print(f"     Severidad: {conflict['severity']:.1f}")
    else:
        print("❌ Error en ingesta GDELT")

if __name__ == "__main__":
    test_gdelt_ingestor()
