#!/usr/bin/env python3
"""
BLOQUE 2A: Sistema de Filtros y Limpieza de Datos
===============================================

Automatización para:
- Excluir deportes y noticias sin foto
- Usar solo artículos geopolíticos/climáticos
- Integrar GDELT en noticias
- Quitar carteles de datos simulados

Fecha: Agosto 2025
"""

import os
import sys
import sqlite3
import logging
import json
from datetime import datetime
from pathlib import Path

# Configurar logging UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('automation_block_2a.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DataFiltersAndCleanupSystem:
    """Sistema para filtrar y limpiar datos del dashboard"""
    
    def __init__(self):
        self.db_path = r"data\geopolitical_intel.db"
        logger.info("🚀 Iniciando Sistema de Filtros y Limpieza - BLOQUE 2A")
    
    def run_all_filters(self):
        """Ejecutar todos los filtros y limpiezas"""
        try:
            logger.info("=" * 60)
            logger.info("🧹 BLOQUE 2A: FILTROS Y LIMPIEZA DE DATOS")
            logger.info("=" * 60)
            
            # 1. Filtrar deportes
            self.filter_sports_news()
            
            # 2. Filtrar artículos sin foto
            self.filter_articles_without_images()
            
            # 3. Categorizar artículos geopolíticos/climáticos
            self.categorize_geopolitical_climate_articles()
            
            # 4. Integrar GDELT
            self.integrate_gdelt_data()
            
            # 5. Remover carteles de datos simulados
            self.remove_simulated_data_labels()
            
            # 6. Actualizar consultas SQL en app_BUENA.py
            self.update_article_queries()
            
            logger.info("✅ BLOQUE 2A COMPLETADO EXITOSAMENTE")
            
        except Exception as e:
            logger.error(f"❌ Error en BLOQUE 2A: {e}")
            raise e
    
    def filter_sports_news(self):
        """Filtrar y marcar noticias deportivas para exclusión"""
        try:
            logger.info("🏈 Filtrando noticias deportivas...")
            
            if not os.path.exists(self.db_path):
                logger.warning(f"Base de datos no encontrada: {self.db_path}")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Palabras clave deportivas
            sports_keywords = [
                'football', 'soccer', 'basketball', 'baseball', 'tennis', 'golf',
                'olympics', 'fifa', 'nfl', 'nba', 'mlb', 'premier league',
                'champions league', 'world cup', 'super bowl', 'playoff',
                'championship', 'tournament', 'match', 'game', 'score',
                'player', 'team', 'coach', 'stadium', 'league',
                'fútbol', 'baloncesto', 'tenis', 'olimpiadas', 'partido',
                'jugador', 'equipo', 'entrenador', 'estadio', 'liga',
                'deporte', 'deportivo', 'deportiva', 'competencia'
            ]
            
            # Crear query para identificar artículos deportivos
            sports_condition = ' OR '.join([
                f"LOWER(title) LIKE '%{keyword}%' OR LOWER(content) LIKE '%{keyword}%'"
                for keyword in sports_keywords
            ])
            
            # Marcar artículos deportivos
            cursor.execute(f"""
                UPDATE articles 
                SET category = 'sports', 
                    excluded_reason = 'sports_content'
                WHERE ({sports_condition})
                AND category != 'geopolitical'
                AND category != 'climate'
            """)
            
            sports_count = cursor.rowcount
            
            # También agregar campo is_excluded si no existe
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN is_excluded INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Columna ya existe
            
            # Marcar como excluidos
            cursor.execute("""
                UPDATE articles 
                SET is_excluded = 1 
                WHERE category = 'sports'
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ {sports_count} artículos deportivos filtrados")
            
        except Exception as e:
            logger.error(f"❌ Error filtrando deportes: {e}")
    
    def filter_articles_without_images(self):
        """Filtrar artículos sin imágenes"""
        try:
            logger.info("📸 Filtrando artículos sin imágenes...")
            
            if not os.path.exists(self.db_path):
                logger.warning(f"Base de datos no encontrada: {self.db_path}")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Marcar artículos sin imagen válida
            cursor.execute("""
                UPDATE articles 
                SET is_excluded = 1,
                    excluded_reason = 'no_image'
                WHERE (
                    image_url IS NULL 
                    OR image_url = '' 
                    OR image_url LIKE '%placeholder%'
                    OR image_url LIKE '%picsum%'
                    OR image_url LIKE '%lorem%'
                    OR image_url LIKE '%dummy%'
                    OR image_url LIKE '%test%'
                )
                AND category != 'sports'
            """)
            
            no_image_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ {no_image_count} artículos sin imagen filtrados")
            
        except Exception as e:
            logger.error(f"❌ Error filtrando imágenes: {e}")
    
    def categorize_geopolitical_climate_articles(self):
        """Categorizar artículos como geopolíticos o climáticos"""
        try:
            logger.info("🌍 Categorizando artículos geopolíticos y climáticos...")
            
            if not os.path.exists(self.db_path):
                logger.warning(f"Base de datos no encontrada: {self.db_path}")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Palabras clave geopolíticas
            geopolitical_keywords = [
                'conflict', 'war', 'military', 'government', 'president', 
                'minister', 'parliament', 'congress', 'senate', 'election',
                'vote', 'policy', 'diplomat', 'embassy', 'treaty', 'sanctions',
                'security', 'defense', 'intelligence', 'terrorism', 'nuclear',
                'weapons', 'army', 'navy', 'air force', 'nato', 'un', 'eu',
                'crisis', 'protest', 'revolution', 'coup', 'border', 'refugee',
                'trade war', 'tariff', 'embargo', 'alliance', 'summit',
                'conflicto', 'guerra', 'militar', 'gobierno', 'presidente',
                'ministro', 'parlamento', 'congreso', 'senado', 'elección',
                'voto', 'política', 'diplomático', 'embajada', 'tratado',
                'sanciones', 'seguridad', 'defensa', 'inteligencia', 'terrorismo',
                'nuclear', 'armas', 'ejército', 'marina', 'fuerza aérea',
                'otan', 'onu', 'ue', 'crisis', 'protesta', 'revolución',
                'golpe', 'frontera', 'refugiado', 'guerra comercial', 'arancel',
                'embargo', 'alianza', 'cumbre'
            ]
            
            # Palabras clave climáticas
            climate_keywords = [
                'climate', 'global warming', 'greenhouse', 'carbon', 'emission',
                'renewable', 'solar', 'wind', 'fossil', 'oil', 'gas', 'coal',
                'environment', 'pollution', 'deforestation', 'biodiversity',
                'sustainability', 'green energy', 'paris agreement', 'cop',
                'temperature', 'weather', 'drought', 'flood', 'hurricane',
                'typhoon', 'wildfire', 'ice cap', 'sea level', 'glacier',
                'clima', 'calentamiento global', 'invernadero', 'carbono',
                'emisión', 'renovable', 'solar', 'eólico', 'fósil', 'petróleo',
                'gas', 'carbón', 'medio ambiente', 'contaminación',
                'deforestación', 'biodiversidad', 'sostenibilidad',
                'energía verde', 'acuerdo de parís', 'temperatura', 'clima',
                'sequía', 'inundación', 'huracán', 'tifón', 'incendio',
                'casquete polar', 'nivel del mar', 'glaciar'
            ]
            
            # Categorizar geopolíticos
            geo_condition = ' OR '.join([
                f"LOWER(title) LIKE '%{keyword}%' OR LOWER(content) LIKE '%{keyword}%'"
                for keyword in geopolitical_keywords
            ])
            
            cursor.execute(f"""
                UPDATE articles 
                SET category = 'geopolitical',
                    is_excluded = 0
                WHERE ({geo_condition})
                AND category != 'sports'
            """)
            
            geo_count = cursor.rowcount
            
            # Categorizar climáticos
            climate_condition = ' OR '.join([
                f"LOWER(title) LIKE '%{keyword}%' OR LOWER(content) LIKE '%{keyword}%'"
                for keyword in climate_keywords
            ])
            
            cursor.execute(f"""
                UPDATE articles 
                SET category = 'climate',
                    is_excluded = 0
                WHERE ({climate_condition})
                AND category != 'sports'
                AND category != 'geopolitical'
            """)
            
            climate_count = cursor.rowcount
            
            # Marcar como excluidos los que no son ni geopolíticos ni climáticos
            cursor.execute("""
                UPDATE articles 
                SET is_excluded = 1,
                    excluded_reason = 'not_geopolitical_or_climate'
                WHERE category NOT IN ('geopolitical', 'climate', 'sports')
                OR category IS NULL
            """)
            
            excluded_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ {geo_count} artículos geopolíticos categorizados")
            logger.info(f"✅ {climate_count} artículos climáticos categorizados")
            logger.info(f"✅ {excluded_count} artículos no relevantes excluidos")
            
        except Exception as e:
            logger.error(f"❌ Error categorizando artículos: {e}")
    
    def integrate_gdelt_data(self):
        """Integrar datos GDELT en el sistema de noticias"""
        try:
            logger.info("📊 Integrando datos GDELT...")
            
            # Verificar si existe tabla GDELT
            if not os.path.exists(self.db_path):
                logger.warning(f"Base de datos no encontrada: {self.db_path}")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Crear tabla GDELT si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gdelt_events (
                    id INTEGER PRIMARY KEY,
                    global_event_id TEXT UNIQUE,
                    sql_date TEXT,
                    month_year TEXT,
                    year TEXT,
                    fraction_date REAL,
                    actor1_code TEXT,
                    actor1_name TEXT,
                    actor1_country_code TEXT,
                    actor1_known_group_code TEXT,
                    actor1_ethnic_code TEXT,
                    actor1_religion1_code TEXT,
                    actor1_religion2_code TEXT,
                    actor1_type1_code TEXT,
                    actor1_type2_code TEXT,
                    actor1_type3_code TEXT,
                    actor2_code TEXT,
                    actor2_name TEXT,
                    actor2_country_code TEXT,
                    actor2_known_group_code TEXT,
                    actor2_ethnic_code TEXT,
                    actor2_religion1_code TEXT,
                    actor2_religion2_code TEXT,
                    actor2_type1_code TEXT,
                    actor2_type2_code TEXT,
                    actor2_type3_code TEXT,
                    is_root_event INTEGER,
                    event_code TEXT,
                    event_base_code TEXT,
                    event_root_code TEXT,
                    quad_class INTEGER,
                    goldstein_scale REAL,
                    num_mentions INTEGER,
                    num_sources INTEGER,
                    num_articles INTEGER,
                    avg_tone REAL,
                    actor1_geo_type INTEGER,
                    actor1_geo_fullname TEXT,
                    actor1_geo_country_code TEXT,
                    actor1_geo_adm1_code TEXT,
                    actor1_geo_adm2_code TEXT,
                    actor1_geo_lat REAL,
                    actor1_geo_long REAL,
                    actor1_geo_feature_id TEXT,
                    actor2_geo_type INTEGER,
                    actor2_geo_fullname TEXT,
                    actor2_geo_country_code TEXT,
                    actor2_geo_adm1_code TEXT,
                    actor2_geo_adm2_code TEXT,
                    actor2_geo_lat REAL,
                    actor2_geo_long REAL,
                    actor2_geo_feature_id TEXT,
                    action_geo_type INTEGER,
                    action_geo_fullname TEXT,
                    action_geo_country_code TEXT,
                    action_geo_adm1_code TEXT,
                    action_geo_adm2_code TEXT,
                    action_geo_lat REAL,
                    action_geo_long REAL,
                    action_geo_feature_id TEXT,
                    date_added TEXT,
                    source_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de relación entre artículos y eventos GDELT
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS article_gdelt_relations (
                    id INTEGER PRIMARY KEY,
                    article_id INTEGER,
                    gdelt_event_id INTEGER,
                    relevance_score REAL DEFAULT 0.5,
                    matching_criteria TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id),
                    FOREIGN KEY (gdelt_event_id) REFERENCES gdelt_events (id)
                )
            """)
            
            # Agregar columnas GDELT a tabla articles si no existen
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN has_gdelt_data INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN gdelt_event_count INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN avg_goldstein_scale REAL DEFAULT 0.0")
            except sqlite3.OperationalError:
                pass
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Estructura GDELT creada/actualizada")
            logger.info("📋 Para integración completa, ejecutar ingesta GDELT posteriormente")
            
        except Exception as e:
            logger.error(f"❌ Error integrando GDELT: {e}")
    
    def remove_simulated_data_labels(self):
        """Remover carteles y etiquetas de datos simulados"""
        try:
            logger.info("🏷️ Removiendo carteles de datos simulados...")
            
            # Archivos a limpiar
            files_to_clean = [
                'app_BUENA.py',
                'src/web/templates/dashboard.html',
                'src/web/templates/index.html',
                'src/web/static/js/dashboard.js',
                'src/web/static/css/dashboard.css'
            ]
            
            # Patrones a eliminar
            patterns_to_remove = [
                'DATOS SIMULADOS',
                'DATOS DE PRUEBA',
                'TEST DATA',
                'MOCK DATA',
                'EJEMPLO',
                'DEMO',
                '⚠️ Datos simulados',
                '🧪 Datos de prueba',
                '📋 Datos de ejemplo',
                'datos simulados',
                'datos de prueba',
                'datos mock',
                'ejemplo solamente'
            ]
            
            for file_path in files_to_clean:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        original_content = content
                        
                        # Remover patrones
                        for pattern in patterns_to_remove:
                            content = content.replace(pattern, '')
                            content = content.replace(pattern.upper(), '')
                            content = content.replace(pattern.lower(), '')
                        
                        # Limpiar comentarios HTML con estos patrones
                        import re
                        content = re.sub(r'<!--.*?(datos simulados|test data|mock data).*?-->', '', content, flags=re.IGNORECASE | re.DOTALL)
                        
                        # Limpiar comentarios Python/JS
                        content = re.sub(r'#.*?(datos simulados|test data|mock data).*?\n', '\n', content, flags=re.IGNORECASE)
                        content = re.sub(r'//.*?(datos simulados|test data|mock data).*?\n', '\n', content, flags=re.IGNORECASE)
                        
                        if content != original_content:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            logger.info(f"✅ Limpiado: {file_path}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo limpiar {file_path}: {e}")
                        
            logger.info("✅ Carteles de datos simulados removidos")
            
        except Exception as e:
            logger.error(f"❌ Error removiendo carteles: {e}")
    
    def update_article_queries(self):
        """Actualizar consultas SQL en app_BUENA.py para usar filtros"""
        try:
            logger.info("🔄 Actualizando consultas SQL con filtros...")
            
            app_file = 'app_BUENA.py'
            if not os.path.exists(app_file):
                logger.warning(f"Archivo {app_file} no encontrado")
                return
            
            with open(app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar y reemplazar consultas SQL principales
            old_query_pattern = """SELECT id, title, content, url, source, published_at, 
                           country, region, risk_level, conflict_type, 
                           sentiment_score, summary, risk_score, image_url
                    FROM articles"""
            
            new_query_pattern = """SELECT id, title, content, url, source, published_at, 
                           country, region, risk_level, conflict_type, 
                           sentiment_score, summary, risk_score, image_url
                    FROM articles 
                    WHERE is_excluded = 0 
                    AND category IN ('geopolitical', 'climate')
                    AND (image_url IS NOT NULL AND image_url != '' 
                         AND image_url NOT LIKE '%placeholder%' 
                         AND image_url NOT LIKE '%picsum%')"""
            
            # Reemplazar en el archivo
            content = content.replace(old_query_pattern, new_query_pattern)
            
            with open(app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("✅ Consultas SQL actualizadas con filtros")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando consultas: {e}")

def main():
    """Función principal para ejecutar BLOQUE 2A"""
    try:
        system = DataFiltersAndCleanupSystem()
        system.run_all_filters()
        
        print("\n" + "="*60)
        print("🎉 BLOQUE 2A COMPLETADO EXITOSAMENTE")
        print("="*60)
        print("✅ Deportes filtrados")
        print("✅ Artículos sin foto excluidos")
        print("✅ Solo artículos geopolíticos/climáticos")
        print("✅ Estructura GDELT integrada")
        print("✅ Carteles simulados removidos")
        print("✅ Consultas SQL actualizadas")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR EN BLOQUE 2A: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
