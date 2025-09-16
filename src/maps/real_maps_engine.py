
import folium
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import sqlite3
import json
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class RealMapsEngine:
    """Motor de mapas con datos reales exclusivamente"""
    
    def __init__(self):
        self.mapbox_token = os.getenv('MAPBOX_TOKEN')
        self.db_path = 'geopolitical_intelligence.db'
        
    def get_real_conflicts_data(self):
        """Obtener datos reales de conflictos desde BD"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT DISTINCT 
                location, latitude, longitude, 
                event_type, intensity_score, 
                date, source_reliability,
                description, affected_population
            FROM conflicts 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND date >= date('now', '-30 days')
            AND source_reliability >= 0.7
            ORDER BY intensity_score DESC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"Error obteniendo datos reales de conflictos: {e}")
            return pd.DataFrame()
    
    def get_real_climate_data(self):
        """Obtener datos reales de clima desde GDELT"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT DISTINCT 
                location, latitude, longitude,
                event_type, goldstein_scale,
                event_date, num_mentions,
                avg_tone, source_url
            FROM gdelt_events 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND event_date >= date('now', '-7 days')
            AND (event_type LIKE '%CLIMATE%' 
                 OR event_type LIKE '%ENVIRONMENT%'
                 OR event_type LIKE '%DISASTER%')
            ORDER BY num_mentions DESC
            LIMIT 1000
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"Error obteniendo datos climáticos reales: {e}")
            return pd.DataFrame()
    
    def create_real_heatmap(self):
        """Crear mapa de calor con datos reales"""
        try:
            # Datos reales de conflictos
            conflicts_df = self.get_real_conflicts_data()
            
            if conflicts_df.empty:
                return self.create_empty_map_message("No hay datos de conflictos disponibles")
            
            # Crear mapa de calor con Plotly
            fig = go.Figure()
            
            # Añadir puntos de conflictos reales
            fig.add_trace(go.Scattermapbox(
                lat=conflicts_df['latitude'],
                lon=conflicts_df['longitude'],
                mode='markers',
                marker=dict(
                    size=conflicts_df['intensity_score'] * 10,
                    color=conflicts_df['intensity_score'],
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Intensidad"),
                    sizemode='diameter'
                ),
                text=conflicts_df.apply(lambda row: 
                    f"<b>{row['location']}</b><br>"
                    f"Tipo: {row['event_type']}<br>"
                    f"Intensidad: {row['intensity_score']:.2f}<br>"
                    f"Fecha: {row['date']}<br>"
                    f"Fiabilidad: {row['source_reliability']:.2f}", axis=1),
                hovertemplate='%{text}<extra></extra>',
                name='Conflictos Actuales'
            ))
            
            # Configuración del mapa
            fig.update_layout(
                mapbox=dict(
                    accesstoken=self.mapbox_token,
                    style='satellite-streets',
                    zoom=2,
                    center=dict(lat=20, lon=0)
                ),
                height=600,
                margin=dict(r=0, t=0, l=0, b=0),
                title={
                    'text': 'Mapa de Calor - Conflictos Reales (Últimos 30 días)',
                    'x': 0.5,
                    'xanchor': 'center'
                }
            )
            
            return fig.to_html(include_plotlyjs=True)
            
        except Exception as e:
            print(f"Error creando mapa de calor real: {e}")
            return self.create_empty_map_message(f"Error: {str(e)}")
    
    def create_real_3d_globe(self):
        """Crear globo 3D con datos reales"""
        try:
            # Combinar datos reales
            conflicts_df = self.get_real_conflicts_data()
            climate_df = self.get_real_climate_data()
            
            fig = go.Figure()
            
            # Conflictos en rojo
            if not conflicts_df.empty:
                fig.add_trace(go.Scatter3d(
                    x=conflicts_df['longitude'],
                    y=conflicts_df['latitude'],
                    z=[0] * len(conflicts_df),
                    mode='markers',
                    marker=dict(
                        size=8,
                        color='red',
                        symbol='diamond'
                    ),
                    text=conflicts_df['location'],
                    name='Conflictos'
                ))
            
            # Eventos climáticos en azul
            if not climate_df.empty:
                fig.add_trace(go.Scatter3d(
                    x=climate_df['longitude'],
                    y=climate_df['latitude'],
                    z=[1] * len(climate_df),
                    mode='markers',
                    marker=dict(
                        size=6,
                        color='blue',
                        symbol='circle'
                    ),
                    text=climate_df['location'],
                    name='Eventos Climáticos'
                ))
            
            fig.update_layout(
                scene=dict(
                    xaxis_title='Longitud',
                    yaxis_title='Latitud',
                    zaxis_title='Tipo de Evento',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                ),
                title='Globo 3D - Eventos Reales Mundiales',
                height=600
            )
            
            return fig.to_html(include_plotlyjs=True)
            
        except Exception as e:
            print(f"Error creando globo 3D: {e}")
            return self.create_empty_map_message(f"Error: {str(e)}")
    
    def create_empty_map_message(self, message):
        """Crear mensaje para mapa vacío"""
        return f"""
        <div class="alert alert-info text-center">
            <h4><i class="fas fa-info-circle"></i> Información</h4>
            <p>{message}</p>
            <small>Los datos se actualizan automáticamente cada hora</small>
        </div>
        """
    
    def get_real_statistics(self):
        """Obtener estadísticas reales de la BD"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Estadísticas de conflictos
            conflicts_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_conflicts,
                    AVG(intensity_score) as avg_intensity,
                    MAX(intensity_score) as max_intensity,
                    COUNT(DISTINCT location) as affected_locations
                FROM conflicts 
                WHERE date >= date('now', '-30 days')
            """, conn)
            
            # Estadísticas GDELT
            gdelt_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_events,
                    AVG(goldstein_scale) as avg_goldstein,
                    COUNT(DISTINCT location) as gdelt_locations
                FROM gdelt_events 
                WHERE event_date >= date('now', '-7 days')
            """, conn)
            
            conn.close()
            
            return {
                'conflicts': conflicts_stats.to_dict('records')[0] if not conflicts_stats.empty else {},
                'gdelt': gdelt_stats.to_dict('records')[0] if not gdelt_stats.empty else {}
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {'conflicts': {}, 'gdelt': {}}
            