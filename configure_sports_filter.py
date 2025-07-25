#!/usr/bin/env python3
"""
Script para configurar filtros de deportes en fuentes RSS
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SportsFilterConfigurator:
    """Configura filtros para excluir fuentes deportivas."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Patrones de URLs y nombres que indican fuentes deportivas
        self.sports_url_patterns = [
            'sport', 'deportes', 'football', 'soccer', 'basketball',
            'tennis', 'golf', 'hockey', 'baseball', 'athletics',
            'olympics', 'fifa', 'uefa', 'nba', 'nfl', 'mlb', 'nhl',
            'espn', 'marca', 'as.com', 'sport.es', 'mundodeportivo',
            'ole.com.ar', 'lance.com.br', 'globoesporte',
            'skysports', 'bbc.com/sport', 'eurosport',
            'sports.yahoo', 'bleacherreport', 'si.com'
        ]
        
        # Nombres de fuentes que son claramente deportivas
        self.sports_source_names = [
            'ESPN', 'Marca', 'AS', 'Sport', 'Mundo Deportivo',
            'Ole', 'Lance', 'Globo Esporte', 'Sky Sports',
            'BBC Sport', 'Eurosport', 'Sports Illustrated',
            'Bleacher Report', 'The Athletic', 'Goal.com',
            'FIFA', 'UEFA', 'NBA', 'NFL', 'MLB', 'NHL',
            'Olympics', 'Olympic Channel', 'Tennis.com',
            'Golf Digest', 'ESPN Deportes', 'Fox Sports',
            'CBS Sports', 'NBC Sports', 'Sport1',
            'Kicker', 'L\'Équipe', 'La Gazzetta dello Sport',
            'Corriere dello Sport', 'Tuttosport'
        ]
    
    def get_db_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def is_sports_source(self, name: str, url: str) -> bool:
        """Determina si una fuente es deportiva."""
        name_lower = name.lower()
        url_lower = url.lower()
        
        # Verificar nombres exactos
        for sports_name in self.sports_source_names:
            if sports_name.lower() in name_lower:
                return True
        
        # Verificar patrones en URL
        for pattern in self.sports_url_patterns:
            if pattern in url_lower:
                return True
        
        return False
    
    def find_sports_sources(self) -> List[Dict]:
        """Encuentra fuentes deportivas en la base de datos."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todas las fuentes
        cursor.execute('''
            SELECT id, name, url, language, region, active, priority
            FROM sources
            ORDER BY name
        ''')
        
        sources = cursor.fetchall()
        sports_sources = []
        
        logger.info(f"Analizando {len(sources)} fuentes RSS...")
        
        for source in sources:
            name = source['name'] or ''
            url = source['url'] or ''
            
            if self.is_sports_source(name, url):
                sports_sources.append({
                    'id': source['id'],
                    'name': name,
                    'url': url,
                    'language': source['language'],
                    'region': source['region'],
                    'active': source['active'],
                    'priority': source['priority']
                })
        
        conn.close()
        return sports_sources
    
    def deactivate_sports_sources(self, source_ids: List[int]) -> int:
        """Desactiva fuentes deportivas."""
        if not source_ids:
            return 0
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join(['?' for _ in source_ids])
            cursor.execute(f'''
                UPDATE sources 
                SET active = 0, last_error = 'Desactivada: fuente deportiva'
                WHERE id IN ({placeholders})
            ''', source_ids)
            
            updated_count = cursor.rowcount
            conn.commit()
            return updated_count
            
        except Exception as e:
            logger.error(f"Error desactivando fuentes: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def add_sports_category_filter(self) -> bool:
        """Añade configuración para filtrar categoría deportiva."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar si existe tabla de configuración
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Añadir configuración para filtrar deportes
            cursor.execute('''
                INSERT OR REPLACE INTO config (key, value, description)
                VALUES (?, ?, ?)
            ''', (
                'filter_sports_content',
                'true',
                'Filtrar automáticamente contenido deportivo y de entretenimiento'
            ))
            
            cursor.execute('''
                INSERT OR REPLACE INTO config (key, value, description)
                VALUES (?, ?, ?)
            ''', (
                'excluded_categories',
                'sports_entertainment',
                'Categorías de contenido a excluir del procesamiento'
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error añadiendo configuración: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def configure_sports_filter(self, dry_run: bool = True) -> Dict:
        """Configura filtros para excluir contenido deportivo."""
        logger.info("Iniciando configuración de filtros deportivos...")
        
        # Encontrar fuentes deportivas
        sports_sources = self.find_sports_sources()
        
        logger.info(f"Encontradas {len(sports_sources)} fuentes deportivas")
        
        if sports_sources:
            logger.info("Fuentes deportivas encontradas:")
            for source in sports_sources:
                status = "ACTIVA" if source['active'] else "INACTIVA"
                logger.info(f"  - [{status}] {source['name']} ({source['url']})")
        
        deactivated_count = 0
        if not dry_run and sports_sources:
            # Desactivar fuentes deportivas
            active_sports_sources = [s for s in sports_sources if s['active']]
            if active_sports_sources:
                source_ids = [source['id'] for source in active_sports_sources]
                deactivated_count = self.deactivate_sports_sources(source_ids)
                logger.info(f"Desactivadas {deactivated_count} fuentes deportivas")
        
        # Añadir configuración de filtros
        config_added = False
        if not dry_run:
            config_added = self.add_sports_category_filter()
            if config_added:
                logger.info("Configuración de filtros añadida a la base de datos")
        
        return {
            'found_sources': len(sports_sources),
            'deactivated_sources': deactivated_count,
            'config_added': config_added,
            'dry_run': dry_run,
            'sources': sports_sources
        }
    
    def show_current_config(self):
        """Muestra la configuración actual de filtros."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar configuración
            cursor.execute('''
                SELECT key, value, description 
                FROM config 
                WHERE key LIKE '%filter%' OR key LIKE '%exclude%'
                ORDER BY key
            ''')
            
            configs = cursor.fetchall()
            
            if configs:
                logger.info("Configuración actual de filtros:")
                for config in configs:
                    logger.info(f"  {config['key']}: {config['value']} - {config['description']}")
            else:
                logger.info("No hay configuración de filtros establecida")
            
            # Mostrar estadísticas de fuentes
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN active = 0 THEN 1 ELSE 0 END) as inactive
                FROM sources
            ''')
            
            stats = cursor.fetchone()
            logger.info(f"Estadísticas de fuentes: {stats['total']} total, {stats['active']} activas, {stats['inactive']} inactivas")
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {e}")
        finally:
            conn.close()

def main():
    """Función principal."""
    # Ruta de la base de datos
    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')
    
    # Verificar que existe la base de datos
    if not Path(DB_PATH).exists():
        logger.error(f"Base de datos no encontrada: {DB_PATH}")
        return
    
    # Crear configurador
    configurator = SportsFilterConfigurator(DB_PATH)
    
    # Mostrar configuración actual
    logger.info("=== CONFIGURACIÓN ACTUAL ===")
    configurator.show_current_config()
    
    # Analizar fuentes deportivas
    logger.info("\n=== ANÁLISIS DE FUENTES DEPORTIVAS ===")
    result = configurator.configure_sports_filter(dry_run=True)
    
    print(f"\nResultados del análisis:")
    print(f"- Fuentes deportivas encontradas: {result['found_sources']}")
    print(f"- Modo dry run: {result['dry_run']}")
    
    if result['found_sources'] > 0:
        print(f"\nFuentes deportivas encontradas:")
        for source in result['sources']:
            status = "ACTIVA" if source['active'] else "INACTIVA"
            print(f"  - [{status}] {source['name']}")
            print(f"    URL: {source['url']}")
        
        # Preguntar si desactivar fuentes deportivas
        active_sports = [s for s in result['sources'] if s['active']]
        if active_sports:
            response = input(f"\n¿Desea desactivar las {len(active_sports)} fuentes deportivas activas? (s/N): ")
            if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                logger.info("=== DESACTIVANDO FUENTES DEPORTIVAS ===")
                config_result = configurator.configure_sports_filter(dry_run=False)
                print(f"Desactivadas {config_result['deactivated_sources']} fuentes deportivas")
                print(f"Configuración añadida: {config_result['config_added']}")
            else:
                print("No se desactivaron fuentes")
        else:
            print("No hay fuentes deportivas activas para desactivar")
    
    # Configurar filtros adicionales
    response = input("\n¿Desea añadir configuración de filtros deportivos? (s/N): ")
    if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        logger.info("=== AÑADIENDO CONFIGURACIÓN DE FILTROS ===")
        config_added = configurator.add_sports_category_filter()
        if config_added:
            print("Configuración de filtros añadida correctamente")
        else:
            print("Error añadiendo configuración de filtros")
    
    # Mostrar configuración final
    logger.info("\n=== CONFIGURACIÓN FINAL ===")
    configurator.show_current_config()

if __name__ == "__main__":
    main()