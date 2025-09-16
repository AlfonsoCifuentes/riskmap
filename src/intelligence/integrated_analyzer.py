#!/usr/bin/env python3
"""
Sistema Integrado de Análisis Geopolítico
Combina análisis de noticias, IA (Groq), feeds externos (ACLED/GDELT/GPR) 
y genera GeoJSON optimizado para consultas satelitales de Sentinel Hub
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np
from collections import defaultdict
import math

from .external_feeds import ExternalIntelligenceFeeds

logger = logging.getLogger(__name__)

class IntegratedGeopoliticalAnalyzer:
    """
    Analizador integrado que combina múltiples fuentes de inteligencia
    """
    
    def __init__(self, db_path: str, groq_client=None):
        self.db_path = db_path
        self.groq_client = groq_client
        self.external_feeds = ExternalIntelligenceFeeds(db_path)
        
        # Pesos para diferentes fuentes de datos
        self.source_weights = {
            'news_analysis': 0.4,      # Nuestro análisis de noticias
            'acled_events': 0.3,       # Eventos de conflicto ACLED
            'gdelt_events': 0.2,       # Eventos GDELT
            'gpr_index': 0.1          # Índice GPR global
        }
        
        # Umbrales de riesgo
        self.risk_thresholds = {
            'very_high': 0.8,
            'high': 0.6,
            'medium': 0.4,
            'low': 0.2
        }
    
    def generate_comprehensive_geojson(self, timeframe_days: int = 7, 
                                     include_predictions: bool = True) -> Dict:
        """
        Generar GeoJSON comprehensivo integrando todas las fuentes
        """
        try:
            logger.info(f"🌍 Generando GeoJSON integrado para los últimos {timeframe_days} días...")
            
            # 1. Obtener datos de todas las fuentes
            news_conflicts = self._get_news_based_conflicts(timeframe_days)
            acled_conflicts = self._get_acled_conflicts(timeframe_days)
            gdelt_conflicts = self._get_gdelt_conflicts(timeframe_days)
            gpr_context = self._get_gpr_context()
            
            # 2. Fusionar y consolidar por ubicación
            consolidated_zones = self._consolidate_conflict_zones(
                news_conflicts, acled_conflicts, gdelt_conflicts, gpr_context
            )
            
            # 3. Aplicar análisis de IA para enriquecer
            if self.groq_client:
                consolidated_zones = self._enrich_with_ai_analysis(consolidated_zones)
            
            # 4. Generar predicciones si se solicita
            if include_predictions:
                predicted_zones = self._generate_risk_predictions(consolidated_zones)
                consolidated_zones.extend(predicted_zones)
            
            # 5. Crear features GeoJSON optimizadas para Sentinel Hub
            features = self._create_sentinel_optimized_features(consolidated_zones)
            
            # 6. Crear metadatos para Sentinel Hub
            metadata = self._create_sentinel_metadata(features, timeframe_days)
            
            geojson = {
                "type": "FeatureCollection",
                "metadata": metadata,
                "features": features,
                "sentinel_hub": {
                    "recommended_collections": [
                        "sentinel-2-l2a",  # Imágenes ópticas alta resolución
                        "sentinel-1-grd",  # Radar para detectar cambios
                        "landsat-ot-l2"    # Imágenes históricas
                    ],
                    "priority_zones": [f for f in features if f['properties']['risk_score'] > 0.7],
                    "monitoring_frequency": "daily" if any(f['properties']['risk_score'] > 0.8 for f in features) else "weekly"
                }
            }
            
            logger.info(f"✅ GeoJSON generado: {len(features)} zonas, {len(geojson['sentinel_hub']['priority_zones'])} prioritarias")
            
            return geojson
            
        except Exception as e:
            logger.error(f"❌ Error generando GeoJSON integrado: {e}")
            return self._generate_fallback_geojson()
    
    def _get_news_based_conflicts(self, days: int) -> List[Dict]:
        """Obtener conflictos basados en nuestro análisis de noticias"""
        conflicts = []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        id, title, country, region,
                        risk_level, risk_score,
                        sentiment_score,
                        created_at, source, url, image_url
                    FROM articles 
                    WHERE created_at >= ? 
                    AND (
                        risk_level IN ('high', 'medium') 
                        OR risk_score > 0.5
                        OR sentiment_score < -0.3
                    )
                    ORDER BY risk_score DESC
                """, (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))
                
                for row in cursor.fetchall():
                    conflicts.append({
                        'source': 'news_analysis',
                        'article_id': row[0],
                        'title': row[1],
                        'location': row[2] or row[3] or 'Unknown',
                        'country': row[2],
                        'region': row[3],
                        'latitude': 0.0,  # Placeholder - será enriquecido por geocoding
                        'longitude': 0.0,  # Placeholder - será enriquecido por geocoding
                        'risk_level': row[4],
                        'risk_score': float(row[5]) if row[5] else 0.0,
                        'conflict_probability': float(row[5]) if row[5] else 0.0,
                        'sentiment_score': float(row[6]) if row[6] else 0.0,
                        'published_date': row[7],
                        'source_name': row[8],
                        'url': row[9],
                        'image_url': row[10],
                        'analysis_type': 'nlp_bert',
                        'confidence': 0.8,
                        'weight': self.source_weights['news_analysis']
                    })
        
        except Exception as e:
            logger.error(f"Error obteniendo conflictos de noticias: {e}")
        
        return conflicts
    
    def _get_acled_conflicts(self, days: int) -> List[Dict]:
        """Obtener conflictos de ACLED"""
        conflicts = []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar si existe la tabla ACLED
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='acled_events'")
                if not cursor.fetchone():
                    logger.info("ℹ️ Tabla ACLED no existe, saltando...")
                    return conflicts
                
                cursor.execute("""
                    SELECT 
                        location, country, region,
                        latitude, longitude, event_type, sub_event_type,
                        fatalities, event_date, actor1, actor2, notes,
                        COUNT(*) as event_count
                    FROM acled_events 
                    WHERE event_date >= ? 
                    AND latitude IS NOT NULL AND longitude IS NOT NULL
                    AND event_type IN ('Violence against civilians', 'Battles', 'Explosions/Remote violence', 'Riots', 'Strategic developments')
                    GROUP BY location, country, latitude, longitude
                    ORDER BY event_count DESC, fatalities DESC
                """, (cutoff_date.strftime('%Y-%m-%d'),))
                
                for row in cursor.fetchall():
                    # Calcular score de riesgo basado en fatalidades y tipo de evento
                    fatalities = row[7] or 0
                    event_count = row[12]
                    
                    # Ponderación por tipo de evento
                    event_severity = {
                        'Violence against civilians': 1.0,
                        'Battles': 0.9,
                        'Explosions/Remote violence': 0.8,
                        'Riots': 0.6,
                        'Strategic developments': 0.4
                    }.get(row[5], 0.5)
                    
                    risk_score = min(1.0, (fatalities * 0.1 + event_count * 0.2 + event_severity) / 3)
                    
                    conflicts.append({
                        'source': 'acled_events',
                        'location': row[0],
                        'country': row[1],
                        'region': row[2],
                        'latitude': float(row[3]),
                        'longitude': float(row[4]),
                        'event_type': row[5],
                        'sub_event_type': row[6],
                        'fatalities': fatalities,
                        'event_count': event_count,
                        'latest_event_date': row[8],
                        'actors': f"{row[9]} vs {row[10]}" if row[9] and row[10] else (row[9] or row[10] or 'Unknown'),
                        'notes': row[11],
                        'risk_score': risk_score,
                        'weight': self.source_weights['acled_events']
                    })
        
        except Exception as e:
            logger.error(f"Error obteniendo conflictos ACLED: {e}")
        
        return conflicts
    
    def _get_gdelt_conflicts(self, days: int) -> List[Dict]:
        """Obtener conflictos de GDELT"""
        conflicts = []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sqldate_cutoff = int(cutoff_date.strftime('%Y%m%d'))
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar si existe la tabla GDELT
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gdelt_events'")
                if not cursor.fetchone():
                    logger.info("ℹ️ Tabla GDELT no existe, saltando...")
                    return conflicts
                
                cursor.execute("""
                    SELECT 
                        actiongeo_fullname as location,
                        actiongeo_countrycode as country,
                        actiongeo_lat as latitude, actiongeo_long as longitude,
                        AVG(avgtone) as avg_tone,
                        AVG(goldsteinscale) as avg_goldstein,
                        COUNT(*) as event_count,
                        MIN(avgtone) as min_tone,
                        GROUP_CONCAT(DISTINCT actor1name) as actors1,
                        GROUP_CONCAT(DISTINCT actor2name) as actors2,
                        eventcode, eventrootcode
                    FROM gdelt_events 
                    WHERE sqldate >= ? 
                    AND actiongeo_lat IS NOT NULL AND actiongeo_long IS NOT NULL
                    AND eventrootcode IN ('14', '15', '16', '17', '18', '19', '20')  -- Códigos de conflicto
                    AND avgtone < 0  -- Solo eventos con tono negativo
                    GROUP BY actiongeo_fullname, actiongeo_countrycode, actiongeo_lat, actiongeo_long
                    HAVING event_count >= 3  -- Mínimo 3 eventos
                    ORDER BY event_count DESC, avg_tone ASC
                """, (sqldate_cutoff,))
                
                for row in cursor.fetchall():
                    # Calcular score de riesgo basado en tono y escala Goldstein
                    avg_tone = row[4] or 0
                    avg_goldstein = row[5] or 0
                    event_count = row[6]
                    min_tone = row[7] or 0
                    
                    # Normalizar score (tono muy negativo = alto riesgo)
                    tone_risk = min(1.0, abs(min_tone) / 20.0)  # -20 = máximo riesgo
                    goldstein_risk = max(0, (avg_goldstein + 10) / 20.0)  # -10 a +10 normalizado
                    volume_risk = min(1.0, event_count / 50.0)  # 50+ eventos = máximo riesgo
                    
                    risk_score = (tone_risk * 0.5 + goldstein_risk * 0.3 + volume_risk * 0.2)
                    
                    conflicts.append({
                        'source': 'gdelt_events',
                        'location': row[0] or 'Unknown Location',
                        'country': row[1],
                        'latitude': float(row[2]),
                        'longitude': float(row[3]),
                        'avg_tone': round(avg_tone, 2),
                        'avg_goldstein': round(avg_goldstein, 2),
                        'event_count': event_count,
                        'min_tone': round(min_tone, 2),
                        'actors': f"{row[8]} vs {row[9]}" if row[8] and row[9] else (row[8] or row[9] or 'Multiple actors'),
                        'event_codes': f"{row[10]}/{row[11]}",
                        'risk_score': risk_score,
                        'weight': self.source_weights['gdelt_events']
                    })
        
        except Exception as e:
            logger.error(f"Error obteniendo conflictos GDELT: {e}")
        
        return conflicts
    
    def _get_gpr_context(self) -> Dict:
        """Obtener contexto del índice GPR global"""
        context = {
            'current_gpr': 0,
            'trend': 'stable',
            'risk_level': 'medium'
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar si existe la tabla GPR
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gpr_index'")
                if not cursor.fetchone():
                    logger.info("ℹ️ Tabla GPR no existe, usando valores por defecto...")
                    return context
                
                # Obtener los últimos valores de GPR
                cursor.execute("""
                    SELECT gpr, date 
                    FROM gpr_index 
                    ORDER BY date DESC 
                    LIMIT 3
                """)
                
                recent_values = cursor.fetchall()
                
                if recent_values:
                    current_gpr = recent_values[0][0]
                    context['current_gpr'] = round(current_gpr, 2)
                    
                    # Determinar tendencia
                    if len(recent_values) >= 2:
                        prev_gpr = recent_values[1][0]
                        if current_gpr > prev_gpr * 1.1:
                            context['trend'] = 'increasing'
                        elif current_gpr < prev_gpr * 0.9:
                            context['trend'] = 'decreasing'
                        else:
                            context['trend'] = 'stable'
                    
                    # Determinar nivel de riesgo global
                    if current_gpr > 200:
                        context['risk_level'] = 'very_high'
                    elif current_gpr > 150:
                        context['risk_level'] = 'high'
                    elif current_gpr > 100:
                        context['risk_level'] = 'medium'
                    else:
                        context['risk_level'] = 'low'
        
        except Exception as e:
            logger.error(f"Error obteniendo contexto GPR: {e}")
        
        return context
    
    def _consolidate_conflict_zones(self, news_conflicts: List, acled_conflicts: List, 
                                   gdelt_conflicts: List, gpr_context: Dict) -> List[Dict]:
        """Consolidar zonas de conflicto de múltiples fuentes"""
        
        # Agrupar por proximidad geográfica (radio de ~50km)
        PROXIMITY_THRESHOLD = 0.5  # grados (aprox 50km)
        
        consolidated = []
        processed_coords = set()
        
        # Combinar todas las fuentes
        all_conflicts = news_conflicts + acled_conflicts + gdelt_conflicts
        
        # Ordenar por score de riesgo descendente
        all_conflicts.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        
        for conflict in all_conflicts:
            lat, lng = conflict['latitude'], conflict['longitude']
            coord_key = f"{lat:.2f},{lng:.2f}"
            
            # Buscar zona existente cerca
            existing_zone = None
            for zone in consolidated:
                zone_lat, zone_lng = zone['latitude'], zone['longitude']
                distance = math.sqrt((lat - zone_lat)**2 + (lng - zone_lng)**2)
                
                if distance <= PROXIMITY_THRESHOLD:
                    existing_zone = zone
                    break
            
            if existing_zone:
                # Fusionar con zona existente
                self._merge_conflict_data(existing_zone, conflict)
            else:
                # Crear nueva zona
                new_zone = self._create_conflict_zone(conflict, gpr_context)
                consolidated.append(new_zone)
                processed_coords.add(coord_key)
        
        # Calcular scores finales y ordenar
        for zone in consolidated:
            zone['final_risk_score'] = self._calculate_final_risk_score(zone, gpr_context)
        
        consolidated.sort(key=lambda x: x['final_risk_score'], reverse=True)
        
        logger.info(f"📊 Consolidadas {len(consolidated)} zonas de {len(all_conflicts)} eventos")
        
        return consolidated
    
    def _merge_conflict_data(self, existing_zone: Dict, new_conflict: Dict):
        """Fusionar datos de conflicto en zona existente"""
        
        # Agregar fuente si no existe
        if new_conflict['source'] not in existing_zone['sources']:
            existing_zone['sources'].append(new_conflict['source'])
        
        # Acumular eventos y scores
        existing_zone['total_events'] += new_conflict.get('event_count', 1)
        existing_zone['source_scores'][new_conflict['source']] = new_conflict.get('risk_score', 0)
        
        # Combinar actores únicos
        if 'actors' in new_conflict:
            if new_conflict['actors'] not in existing_zone['actors']:
                existing_zone['actors'].append(new_conflict['actors'])
        
        # Agregar tipos de evento únicos
        if 'event_type' in new_conflict:
            if new_conflict['event_type'] not in existing_zone['event_types']:
                existing_zone['event_types'].append(new_conflict['event_type'])
        
        # Acumular fatalidades si existen
        if 'fatalities' in new_conflict:
            existing_zone['total_fatalities'] += new_conflict['fatalities']
        
        # Actualizar fecha más reciente
        if 'published_date' in new_conflict or 'latest_event_date' in new_conflict:
            event_date = new_conflict.get('published_date') or new_conflict.get('latest_event_date')
            if event_date and event_date > existing_zone['latest_event_date']:
                existing_zone['latest_event_date'] = event_date
        
        # Agregar artículos de noticias
        if new_conflict['source'] == 'news_analysis' and 'article_id' in new_conflict:
            existing_zone['news_articles'].append({
                'id': new_conflict['article_id'],
                'title': new_conflict['title'],
                'url': new_conflict.get('url'),
                'image_url': new_conflict.get('image_url')
            })
    
    def _create_conflict_zone(self, conflict: Dict, gpr_context: Dict) -> Dict:
        """Crear nueva zona de conflicto"""
        
        zone = {
            'location': conflict['location'],
            'country': conflict.get('country'),
            'region': conflict.get('region'),
            'latitude': conflict['latitude'],
            'longitude': conflict['longitude'],
            'sources': [conflict['source']],
            'source_scores': {conflict['source']: conflict.get('risk_score', 0)},
            'total_events': conflict.get('event_count', 1),
            'total_fatalities': conflict.get('fatalities', 0),
            'actors': [conflict.get('actors', 'Unknown')] if conflict.get('actors') else [],
            'event_types': [conflict.get('event_type', 'Conflict')] if conflict.get('event_type') else [],
            'latest_event_date': conflict.get('published_date') or conflict.get('latest_event_date') or datetime.now().isoformat(),
            'news_articles': [],
            'gpr_context': gpr_context
        }
        
        # Agregar artículos de noticias si corresponde
        if conflict['source'] == 'news_analysis' and 'article_id' in conflict:
            zone['news_articles'].append({
                'id': conflict['article_id'],
                'title': conflict['title'],
                'url': conflict.get('url'),
                'image_url': conflict.get('image_url')
            })
        
        return zone
    
    def _calculate_final_risk_score(self, zone: Dict, gpr_context: Dict) -> float:
        """Calcular score final de riesgo combinando todas las fuentes"""
        
        # Score base ponderado por fuentes
        weighted_score = 0
        total_weight = 0
        
        for source, score in zone['source_scores'].items():
            weight = self.source_weights.get(source, 0.1)
            weighted_score += score * weight
            total_weight += weight
        
        base_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Factores de amplificación
        
        # 1. Múltiples fuentes (más confiable)
        multi_source_bonus = min(0.2, len(zone['sources']) * 0.05)
        
        # 2. Volumen de eventos
        volume_factor = min(0.3, zone['total_events'] / 20.0)
        
        # 3. Fatalidades
        fatality_factor = min(0.2, zone['total_fatalities'] / 50.0)
        
        # 4. Contexto GPR global
        gpr_factor = 0
        if gpr_context['risk_level'] == 'very_high':
            gpr_factor = 0.15
        elif gpr_context['risk_level'] == 'high':
            gpr_factor = 0.1
        elif gpr_context['risk_level'] == 'medium':
            gpr_factor = 0.05
        
        # 5. Recencia de eventos
        recency_factor = 0
        try:
            latest_date = datetime.fromisoformat(zone['latest_event_date'].replace('Z', '+00:00'))
            days_ago = (datetime.now() - latest_date.replace(tzinfo=None)).days
            recency_factor = max(0, 0.1 - (days_ago * 0.01))
        except:
            pass
        
        # Score final
        final_score = min(1.0, base_score + multi_source_bonus + volume_factor + 
                         fatality_factor + gpr_factor + recency_factor)
        
        return round(final_score, 3)
    
    def _enrich_with_ai_analysis(self, zones: List[Dict]) -> List[Dict]:
        """Enriquecer zonas con análisis de IA usando Groq"""
        
        if not self.groq_client:
            logger.info("ℹ️ Cliente Groq no disponible, saltando enriquecimiento IA")
            return zones
        
        try:
            # Procesar zonas de alto riesgo con IA
            high_risk_zones = [z for z in zones if z.get('final_risk_score', 0) > 0.6]
            
            for zone in high_risk_zones[:10]:  # Limitar a 10 para no saturar API
                try:
                    ai_context = self._generate_zone_context(zone)
                    ai_analysis = self._get_groq_zone_analysis(ai_context)
                    
                    if ai_analysis:
                        zone['ai_analysis'] = ai_analysis
                        
                        # Ajustar score basado en análisis IA
                        if 'risk_assessment' in ai_analysis:
                            ai_risk = ai_analysis['risk_assessment'].lower()
                            if 'critical' in ai_risk or 'very high' in ai_risk:
                                zone['final_risk_score'] = min(1.0, zone['final_risk_score'] + 0.1)
                            elif 'escalating' in ai_risk:
                                zone['final_risk_score'] = min(1.0, zone['final_risk_score'] + 0.05)
                    
                except Exception as e:
                    logger.warning(f"Error en análisis IA para zona {zone['location']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error en enriquecimiento IA: {e}")
        
        return zones
    
    def _generate_zone_context(self, zone: Dict) -> str:
        """Generar contexto de zona para análisis IA"""
        
        context_parts = [
            f"Zona de conflicto: {zone['location']}"
        ]
        
        if zone.get('country'):
            context_parts.append(f"País: {zone['country']}")
        
        context_parts.append(f"Fuentes de datos: {', '.join(zone['sources'])}")
        context_parts.append(f"Total de eventos: {zone['total_events']}")
        
        if zone['total_fatalities'] > 0:
            context_parts.append(f"Fatalidades reportadas: {zone['total_fatalities']}")
        
        if zone['actors']:
            context_parts.append(f"Actores involucrados: {', '.join(zone['actors'][:3])}")
        
        if zone['event_types']:
            context_parts.append(f"Tipos de eventos: {', '.join(zone['event_types'][:3])}")
        
        context_parts.append(f"Score de riesgo actual: {zone['final_risk_score']}")
        
        # Agregar títulos de noticias si existen
        if zone['news_articles']:
            news_titles = [article['title'] for article in zone['news_articles'][:3]]
            context_parts.append(f"Titulares recientes: {'; '.join(news_titles)}")
        
        return '. '.join(context_parts)
    
    def _get_groq_zone_analysis(self, context: str) -> Optional[Dict]:
        """Obtener análisis de zona usando Groq"""
        
        try:
            prompt = f"""
            Analiza esta zona de conflicto geopolítico y proporciona una evaluación estructurada:

            {context}

            Proporciona tu análisis en el siguiente formato JSON:
            {{
                "risk_assessment": "low/medium/high/critical",
                "escalation_probability": "low/medium/high",
                "key_factors": ["factor1", "factor2", "factor3"],
                "trend_analysis": "improving/stable/deteriorating",
                "satellite_monitoring_priority": "low/medium/high",
                "recommended_monitoring_frequency": "weekly/daily/hourly"
            }}
            
            Responde solo con JSON válido, sin explicaciones adicionales.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                max_tokens=200,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Intentar parsear JSON
            if ai_response.startswith('{') and ai_response.endswith('}'):
                return json.loads(ai_response)
            else:
                logger.warning(f"Respuesta IA no es JSON válido: {ai_response}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo análisis Groq: {e}")
            return None
    
    def _generate_risk_predictions(self, current_zones: List[Dict]) -> List[Dict]:
        """Generar predicciones de riesgo basadas en tendencias"""
        
        predictions = []
        
        try:
            # Identificar zonas con tendencias ascendentes
            for zone in current_zones:
                if zone['final_risk_score'] > 0.4 and len(zone['sources']) >= 2:
                    
                    # Crear zona de predicción para área circundante
                    prediction = {
                        'location': f"Área de influencia - {zone['location']}",
                        'country': zone['country'],
                        'region': zone['region'],
                        'latitude': zone['latitude'] + 0.1,  # Offset ligeramente
                        'longitude': zone['longitude'] + 0.1,
                        'sources': ['risk_prediction'],
                        'source_scores': {'risk_prediction': zone['final_risk_score'] * 0.7},
                        'total_events': 0,
                        'total_fatalities': 0,
                        'actors': ['Predictive modeling'],
                        'event_types': ['Risk spillover'],
                        'latest_event_date': datetime.now().isoformat(),
                        'news_articles': [],
                        'is_prediction': True,
                        'prediction_confidence': min(0.8, zone['final_risk_score']),
                        'base_zone': zone['location'],
                        'final_risk_score': round(zone['final_risk_score'] * 0.6, 3)
                    }
                    
                    predictions.append(prediction)
        
        except Exception as e:
            logger.error(f"Error generando predicciones: {e}")
        
        return predictions[:5]  # Máximo 5 predicciones
    
    def _create_sentinel_optimized_features(self, zones: List[Dict]) -> List[Dict]:
        """Crear features GeoJSON optimizadas para Sentinel Hub"""
        
        features = []
        
        for zone in zones:
            try:
                # Determinar prioridad para Sentinel Hub
                priority = self._calculate_sentinel_priority(zone)
                
                # Crear bounding box para la zona (aprox 10km radio)
                bbox_size = 0.1  # grados
                
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [zone['longitude'], zone['latitude']]
                    },
                    "properties": {
                        # Propiedades básicas
                        "id": f"conflict_zone_{len(features) + 1}",
                        "name": zone['location'],
                        "country": zone.get('country'),
                        "region": zone.get('region'),
                        
                        # Métricas de riesgo
                        "risk_score": zone['final_risk_score'],
                        "risk_level": self._categorize_risk_level(zone['final_risk_score']),
                        "confidence": zone.get('prediction_confidence', 0.9),
                        
                        # Datos de eventos
                        "total_events": zone['total_events'],
                        "fatalities": zone['total_fatalities'],
                        "data_sources": zone['sources'],
                        "actors": zone['actors'][:3],  # Limitar a 3 actores principales
                        "event_types": zone['event_types'][:3],
                        
                        # Fechas
                        "latest_event": zone['latest_event_date'],
                        "data_updated": datetime.now().isoformat(),
                        
                        # Para Sentinel Hub
                        "sentinel_priority": priority,
                        "monitoring_frequency": self._get_monitoring_frequency(zone),
                        "bbox": [
                            zone['longitude'] - bbox_size/2,
                            zone['latitude'] - bbox_size/2,
                            zone['longitude'] + bbox_size/2,
                            zone['latitude'] + bbox_size/2
                        ],
                        "recommended_resolution": self._get_recommended_resolution(zone),
                        "cloud_cover_max": 20 if zone['final_risk_score'] > 0.7 else 50,
                        
                        # Metadatos adicionales
                        "is_prediction": zone.get('is_prediction', False),
                        "prediction_base": zone.get('base_zone'),
                        "ai_enhanced": 'ai_analysis' in zone,
                        "news_articles_count": len(zone.get('news_articles', [])),
                        
                        # Para integración con dashboard
                        "dashboard_visible": True,
                        "marker_size": "large" if zone['final_risk_score'] > 0.7 else "medium",
                        "marker_color": self._get_marker_color(zone['final_risk_score'])
                    }
                }
                
                # Agregar análisis IA si existe
                if 'ai_analysis' in zone:
                    feature['properties']['ai_risk_assessment'] = zone['ai_analysis'].get('risk_assessment')
                    feature['properties']['ai_escalation_probability'] = zone['ai_analysis'].get('escalation_probability')
                    feature['properties']['ai_trend'] = zone['ai_analysis'].get('trend_analysis')
                
                features.append(feature)
                
            except Exception as e:
                logger.error(f"Error creando feature para zona {zone.get('location', 'unknown')}: {e}")
                continue
        
        return features
    
    def _calculate_sentinel_priority(self, zone: Dict) -> str:
        """Calcular prioridad para monitoreo satelital"""
        score = zone['final_risk_score']
        
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _categorize_risk_level(self, score: float) -> str:
        """Categorizar nivel de riesgo"""
        if score >= self.risk_thresholds['very_high']:
            return "very_high"
        elif score >= self.risk_thresholds['high']:
            return "high"
        elif score >= self.risk_thresholds['medium']:
            return "medium"
        else:
            return "low"
    
    def _get_monitoring_frequency(self, zone: Dict) -> str:
        """Determinar frecuencia de monitoreo recomendada"""
        score = zone['final_risk_score']
        
        if score >= 0.8:
            return "daily"
        elif score >= 0.6:
            return "weekly"
        else:
            return "monthly"
    
    def _get_recommended_resolution(self, zone: Dict) -> str:
        """Determinar resolución recomendada para imágenes satelitales"""
        if zone['final_risk_score'] >= 0.7:
            return "10m"  # Alta resolución para zonas críticas
        else:
            return "20m"  # Resolución estándar
    
    def _get_marker_color(self, score: float) -> str:
        """Obtener color de marcador para dashboard"""
        if score >= 0.8:
            return "#ff0000"  # Rojo crítico
        elif score >= 0.6:
            return "#ff6600"  # Naranja alto
        elif score >= 0.4:
            return "#ffcc00"  # Amarillo medio
        else:
            return "#00cc00"  # Verde bajo
    
    def _create_sentinel_metadata(self, features: List[Dict], timeframe_days: int) -> Dict:
        """Crear metadatos para Sentinel Hub"""
        
        total_zones = len(features)
        priority_zones = len([f for f in features if f['properties']['sentinel_priority'] in ['critical', 'high']])
        
        return {
            "generated_by": "RiskMap Integrated Geopolitical Analyzer",
            "generated_at": datetime.now().isoformat(),
            "version": "2.0",
            
            # Estadísticas del dataset
            "total_zones": total_zones,
            "priority_zones": priority_zones,
            "data_timeframe_days": timeframe_days,
            "data_sources": ["news_analysis", "acled", "gdelt", "gpr", "ai_analysis"],
            
            # Para Sentinel Hub
            "crs": "EPSG:4326",
            "bbox_global": self._calculate_global_bbox(features),
            "recommended_collections": [
                "sentinel-2-l2a",
                "sentinel-1-grd", 
                "landsat-ot-l2"
            ],
            
            # Configuración de monitoreo
            "monitoring_strategy": {
                "critical_zones_frequency": "daily",
                "high_zones_frequency": "weekly", 
                "medium_zones_frequency": "monthly",
                "cloud_cover_threshold": 20
            },
            
            # Para consultas automatizadas
            "auto_query": {
                "enabled": True,
                "min_risk_score": 0.6,
                "max_cloud_cover": 30,
                "preferred_months": list(range(1, 13))  # Todo el año
            }
        }
    
    def _calculate_global_bbox(self, features: List[Dict]) -> List[float]:
        """Calcular bounding box global de todas las features"""
        if not features:
            return [-180, -90, 180, 90]
        
        lngs = [f['geometry']['coordinates'][0] for f in features]
        lats = [f['geometry']['coordinates'][1] for f in features]
        
        return [min(lngs), min(lats), max(lngs), max(lats)]
    
    def _generate_fallback_geojson(self) -> Dict:
        """Generar GeoJSON de fallback en caso de error"""
        
        return {
            "type": "FeatureCollection",
            "metadata": {
                "generated_by": "RiskMap Fallback Generator",
                "generated_at": datetime.now().isoformat(),
                "status": "fallback",
                "total_zones": 3
            },
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [30.0, 50.0]},
                    "properties": {
                        "name": "Europa Oriental",
                        "risk_score": 0.8,
                        "risk_level": "high",
                        "sentinel_priority": "high"
                    }
                },
                {
                    "type": "Feature", 
                    "geometry": {"type": "Point", "coordinates": [45.0, 30.0]},
                    "properties": {
                        "name": "Medio Oriente",
                        "risk_score": 0.7,
                        "risk_level": "high",
                        "sentinel_priority": "high"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [115.0, 15.0]},
                    "properties": {
                        "name": "Mar del Sur de China",
                        "risk_score": 0.6,
                        "risk_level": "medium", 
                        "sentinel_priority": "medium"
                    }
                }
            ],
            "sentinel_hub": {
                "recommended_collections": ["sentinel-2-l2a"],
                "priority_zones": 2,
                "monitoring_frequency": "weekly"
            }
        }
