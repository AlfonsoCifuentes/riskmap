#!/usr/bin/env python3
"""
Analizador de conflictos usando los datasets UCDP y GDELT
"""

import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ConflictAnalyzer:
    def __init__(self, db_path=None):
        """Inicializar el analizador de conflictos"""
        self.db_path = db_path or Path(__file__).parent / 'data' / 'geopolitical_intel.db'
        self.datasets_path = Path(__file__).parent / 'datasets'
        
        # Cargar datasets
        self.load_datasets()
    
    def load_datasets(self):
        """Cargar todos los datasets de conflictos"""
        try:
            # UCDP Georeferenced Events
            self.ged_events = pd.read_csv(self.datasets_path / 'GEDEvent_v25_1.csv')
            logger.info(f"Cargados {len(self.ged_events)} eventos GED")
            
            # UCDP/PRIO Conflicts
            self.conflicts = pd.read_csv(self.datasets_path / 'UcdpPrioConflict_v25_1.csv')
            logger.info(f"Cargados {len(self.conflicts)} conflictos UCDP/PRIO")
            
            # Battle Deaths
            self.battle_deaths = pd.read_csv(self.datasets_path / 'BattleDeaths_v25_1.csv')
            logger.info(f"Cargadas {len(self.battle_deaths)} entradas de muertes en batalla")
            
            # Political Terror Scale
            self.pts = pd.read_csv(self.datasets_path / 'PTS-2024.csv')
            logger.info(f"Cargados {len(self.pts)} registros PTS")
            
            # GDELT (si existe)
            gdelt_path = self.datasets_path / '20250724.gkg.csv'
            if gdelt_path.exists():
                self.gdelt = pd.read_csv(gdelt_path, sep='\t', low_memory=False)
                logger.info(f"Cargados {len(self.gdelt)} eventos GDELT")
            
        except Exception as e:
            logger.error(f"Error cargando datasets: {e}")
    
    def get_conflict_hotspots(self, year_start=2020, year_end=2024):
        """Identificar hotspots de conflicto por ubicación"""
        try:
            # Filtrar eventos por años
            recent_events = self.ged_events[
                (self.ged_events['year'] >= year_start) & 
                (self.ged_events['year'] <= year_end)
            ].copy()
            
            # Agrupar por país y calcular métricas
            hotspots = recent_events.groupby('country').agg({
                'id': 'count',  # Número de eventos
                'best': 'sum',  # Total de muertes
                'latitude': 'mean',
                'longitude': 'mean'
            }).reset_index()
            
            hotspots.columns = ['country', 'event_count', 'total_deaths', 'avg_lat', 'avg_lng']
            
            # Calcular índice de intensidad
            hotspots['intensity_index'] = (
                hotspots['event_count'] * 0.3 + 
                hotspots['total_deaths'] * 0.7
            )
            
            return hotspots.sort_values('intensity_index', ascending=False)
            
        except Exception as e:
            logger.error(f"Error calculando hotspots: {e}")
            return pd.DataFrame()
    
    def get_conflict_timeline(self, country=None):
        """Obtener timeline de conflictos para un país o global"""
        try:
            data = self.ged_events.copy()
            
            if country:
                data = data[data['country'] == country]
            
            # Agrupar por año
            timeline = data.groupby('year').agg({
                'id': 'count',
                'best': 'sum',
                'deaths_civilians': 'sum'
            }).reset_index()
            
            timeline.columns = ['year', 'events', 'total_deaths', 'civilian_deaths']
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error generando timeline: {e}")
            return pd.DataFrame()
    
    def get_actor_analysis(self):
        """Analizar actores más activos en conflictos"""
        try:
            # Analizar lado A (generalmente gobiernos)
            side_a = self.ged_events.groupby('side_a').agg({
                'id': 'count',
                'best': 'sum'
            }).reset_index()
            side_a.columns = ['actor', 'events', 'deaths']
            side_a['type'] = 'Government/State'
            
            # Analizar lado B (generalmente grupos armados)
            side_b = self.ged_events.groupby('side_b').agg({
                'id': 'count',
                'best': 'sum'
            }).reset_index()
            side_b.columns = ['actor', 'events', 'deaths']
            side_b['type'] = 'Non-State/Rebel'
            
            # Combinar y ordenar
            actors = pd.concat([side_a, side_b]).sort_values('events', ascending=False)
            
            return actors.head(20)
            
        except Exception as e:
            logger.error(f"Error analizando actores: {e}")
            return pd.DataFrame()
    
    def get_political_terror_trends(self):
        """Analizar tendencias del Political Terror Scale"""
        try:
            # Calcular promedio por año
            yearly_trends = self.pts.groupby('Year').agg({
                'PTS_A': 'mean',
                'PTS_H': 'mean',
                'PTS_S': 'mean'
            }).reset_index()
            
            # Países con mayor terror político reciente
            recent_pts = self.pts[self.pts['Year'] >= 2020].groupby('Country').agg({
                'PTS_A': 'mean',
                'PTS_H': 'mean',
                'PTS_S': 'mean'
            }).reset_index()
            
            return {
                'yearly_trends': yearly_trends,
                'recent_by_country': recent_pts.sort_values('PTS_A', ascending=False)
            }
            
        except Exception as e:
            logger.error(f"Error analizando PTS: {e}")
            return {}
    
    def generate_risk_assessment(self, country):
        """Generar evaluación de riesgo para un país específico"""
        try:
            assessment = {
                'country': country,
                'timestamp': datetime.now().isoformat(),
                'metrics': {}
            }
            
            # Eventos recientes (últimos 2 años)
            recent_events = self.ged_events[
                (self.ged_events['country'] == country) & 
                (self.ged_events['year'] >= 2022)
            ]
            
            assessment['metrics']['recent_events'] = len(recent_events)
            assessment['metrics']['recent_deaths'] = recent_events['best'].sum()
            
            # Terror político
            recent_pts = self.pts[
                (self.pts['Country'] == country) & 
                (self.pts['Year'] >= 2020)
            ]
            
            if not recent_pts.empty:
                assessment['metrics']['political_terror'] = recent_pts['PTS_A'].mean()
            
            # Conflictos activos
            active_conflicts = self.conflicts[
                (self.conflicts['location'] == country) & 
                (self.conflicts['year'] >= 2020)
            ]
            
            assessment['metrics']['active_conflicts'] = len(active_conflicts)
            
            # Calcular índice de riesgo compuesto (0-10)
            risk_score = 0
            
            # Eventos recientes (0-3 puntos)
            if assessment['metrics']['recent_events'] > 50:
                risk_score += 3
            elif assessment['metrics']['recent_events'] > 20:
                risk_score += 2
            elif assessment['metrics']['recent_events'] > 5:
                risk_score += 1
            
            # Terror político (0-3 puntos)
            if 'political_terror' in assessment['metrics']:
                pts_score = assessment['metrics']['political_terror']
                if pts_score >= 4:
                    risk_score += 3
                elif pts_score >= 3:
                    risk_score += 2
                elif pts_score >= 2:
                    risk_score += 1
            
            # Conflictos activos (0-4 puntos)
            risk_score += min(assessment['metrics']['active_conflicts'], 4)
            
            assessment['risk_score'] = min(risk_score, 10)
            assessment['risk_level'] = self.get_risk_level(assessment['risk_score'])
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error generando evaluación de riesgo: {e}")
            return {}
    
    def get_risk_level(self, score):
        """Convertir puntuación numérica a nivel de riesgo"""
        if score >= 8:
            return 'Critical'
        elif score >= 6:
            return 'High'
        elif score >= 4:
            return 'Medium'
        elif score >= 2:
            return 'Low'
        else:
            return 'Very Low'
    
    def export_to_database(self):
        """Exportar análisis a la base de datos principal"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Crear tabla de hotspots
            hotspots = self.get_conflict_hotspots()
            hotspots.to_sql('conflict_hotspots', conn, if_exists='replace', index=False)
            
            # Crear tabla de evaluaciones de riesgo por país
            countries = self.ged_events['country'].unique()
            risk_assessments = []
            
            for country in countries[:20]:  # Limitar para prueba
                assessment = self.generate_risk_assessment(country)
                if assessment:
                    risk_assessments.append({
                        'country': country,
                        'risk_score': assessment.get('risk_score', 0),
                        'risk_level': assessment.get('risk_level', 'Unknown'),
                        'recent_events': assessment.get('metrics', {}).get('recent_events', 0),
                        'recent_deaths': assessment.get('metrics', {}).get('recent_deaths', 0),
                        'updated_at': datetime.now().isoformat()
                    })
            
            risk_df = pd.DataFrame(risk_assessments)
            risk_df.to_sql('country_risk_assessments', conn, if_exists='replace', index=False)
            
            conn.close()
            logger.info("Datos exportados a la base de datos")
            
        except Exception as e:
            logger.error(f"Error exportando a base de datos: {e}")

def main():
    """Función principal para testing"""
    analyzer = ConflictAnalyzer()
    
    print("🔍 Analizando hotspots de conflicto...")
    hotspots = analyzer.get_conflict_hotspots()
    print(f"Top 10 hotspots:\n{hotspots.head(10)}")
    
    print("\n📊 Analizando actores principales...")
    actors = analyzer.get_actor_analysis()
    print(f"Top 10 actores:\n{actors.head(10)}")
    
    print("\n🌍 Evaluación de riesgo para países específicos...")
    for country in ['Afghanistan', 'Syria', 'Ukraine', 'Myanmar']:
        assessment = analyzer.generate_risk_assessment(country)
        if assessment:
            print(f"{country}: {assessment['risk_level']} (Score: {assessment['risk_score']}/10)")
    
    print("\n💾 Exportando a base de datos...")
    analyzer.export_to_database()
    print("✅ Análisis completado")

if __name__ == "__main__":
    main()