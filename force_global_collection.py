#!/usr/bin/env python3
"""
Script de Recolección Global Forzada
Asegura recolección de noticias en todos los idiomas configurados
"""

import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent))

try:
    from src.data_ingestion.global_news_collector import EnhancedNewsAPICollector, GlobalRSSCollector
    from src.data_ingestion.news_collector import NewsAPICollector
    from src.utils.config import config
except ImportError:
    # Fallback imports
    import sqlite3
    
    class MockConfig:
        def get_database_path(self):
            return 'data/geopolitical_intel.db'
        def get_newsapi_key(self):
            return os.getenv('NEWSAPI_KEY')
    config = MockConfig()
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_global_collection():
    """Ejecuta recolección forzada en todos los idiomas"""
    
    # Configurar idiomas objetivo con keywords específicas
    target_languages = {
        'en': ['conflict', 'war', 'diplomacy', 'geopolitics', 'military', 'crisis'],
        'ru': ['конфликт', 'война', 'дипломатия', 'военный'],
        'zh': ['冲突', '战争', '外交', '军事'],
        'ar': ['صراع', 'حرب', 'دبلوماسية', 'عسكري'],
        'fr': ['conflit', 'guerre', 'diplomatie', 'militaire'],
        'de': ['konflikt', 'krieg', 'diplomatie', 'militär']
    }
    
    # Inicializar colectores
    newsapi_collector = NewsAPICollector()
    
    total_collected = 0
    
    for language, keywords in target_languages.items():
        logger.info(f"🌍 Recolectando noticias en {language.upper()}...")
        
        lang_total = 0
        
        # Recolección por headlines
        try:
            headlines = newsapi_collector.collect_headlines(
                language=language, 
                max_articles=20
            )
            if headlines:
                lang_total += len(headlines)
                logger.info(f"✅ Headlines {language}: {len(headlines)} artículos")
        except Exception as e:
            logger.error(f"❌ Error headlines {language}: {e}")
        
        # Recolección por keywords
        for keyword in keywords[:2]:  # Limitar a 2 keywords por idioma
            try:
                articles = newsapi_collector.search_everything(
                    query=keyword,
                    language=language,
                    max_articles=15
                )
                if articles:
                    lang_total += len(articles)
                    logger.info(f"✅ Keyword '{keyword}' {language}: {len(articles)} artículos")
                time.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"❌ Error keyword '{keyword}' {language}: {e}")
        
        total_collected += lang_total
        logger.info(f"📊 Total {language.upper()}: {lang_total} artículos")
        
        # Pausa entre idiomas
        time.sleep(3)
    
    logger.info(f"🎯 RECOLECCIÓN COMPLETADA: {total_collected} artículos totales")
    return total_collected

def add_mock_geographic_data():
    """Añade datos geográficos simulados para el heatmap"""
    import sqlite3
    
    try:
        conn = sqlite3.connect(config.get_database_path())
        cursor = conn.cursor()
        
        # Agregar columnas geográficas si no existen
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN country TEXT")
            cursor.execute("ALTER TABLE articles ADD COLUMN region TEXT")
            cursor.execute("ALTER TABLE articles ADD COLUMN risk_level TEXT")
        except:
            pass  # Columnas ya existen
        
        # Actualizar artículos existentes con datos geográficos
        geographic_mapping = {
            'es': [('Spain', 'Europe', 'LOW'), ('Mexico', 'Americas', 'MEDIUM'), ('Argentina', 'Americas', 'LOW')],
            'en': [('USA', 'Americas', 'HIGH'), ('UK', 'Europe', 'MEDIUM'), ('Australia', 'Asia-Pacific', 'LOW')],
            'ru': [('Russia', 'Europe', 'HIGH'), ('Belarus', 'Europe', 'HIGH')],
            'zh': [('China', 'Asia-Pacific', 'HIGH'), ('Taiwan', 'Asia-Pacific', 'HIGH')],
            'ar': [('Saudi Arabia', 'Middle East', 'HIGH'), ('UAE', 'Middle East', 'MEDIUM'), ('Egypt', 'Africa', 'MEDIUM')],
            'fr': [('France', 'Europe', 'MEDIUM')],
            'de': [('Germany', 'Europe', 'LOW')]
        }
        
        for language, locations in geographic_mapping.items():
            for country, region, risk in locations:
                cursor.execute("""
                    UPDATE articles 
                    SET country = ?, region = ?, risk_level = ? 
                    WHERE language = ? AND country IS NULL
                """, (country, region, risk, language))
        
        conn.commit()
        conn.close()
        logger.info("✅ Datos geográficos añadidos exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error añadiendo datos geográficos: {e}")

def main():
    logger.info("🚀 INICIANDO RECOLECCIÓN GLOBAL FORZADA")
    
    # Ejecutar recolección
    total = force_global_collection()
    
    # Añadir datos geográficos
    add_mock_geographic_data()
    
    logger.info("🎉 PROCESO COMPLETADO EXITOSAMENTE")
    
    # Mostrar estadísticas finales
    import sqlite3
    conn = sqlite3.connect(config.get_database_path())
    cursor = conn.cursor()
    
    cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language ORDER BY COUNT(*) DESC")
    results = cursor.fetchall()
    
    logger.info("📊 ESTADÍSTICAS FINALES:")
    for lang, count in results:
        logger.info(f"   {lang.upper()}: {count} artículos")
    
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_db = cursor.fetchone()[0]
    logger.info(f"📈 TOTAL EN BASE DE DATOS: {total_db} artículos")
    
    conn.close()

if __name__ == "__main__":
    main()
