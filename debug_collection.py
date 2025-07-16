#!/usr/bin/env python3
"""
Script de debug para verificar la recolección global y corregir problemas.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import sqlite3
import logging
from datetime import datetime

from src.utils.config import config, DatabaseManager
from src.data_ingestion.news_collector import NewsAPICollector

# Configurar logging sin emojis para Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug_collection.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def debug_database():
    """Verifica el estado de la base de datos"""
    logger.info("=== DEBUG DATABASE ===")
    
    db_path = config.get_database_path()
    logger.info(f"Database path: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info(f"Tables found: {[table[0] for table in tables]}")
        
        # Verificar artículos
        cursor.execute("SELECT COUNT(*) FROM articles;")
        total_articles = cursor.fetchone()[0]
        logger.info(f"Total articles: {total_articles}")
        
        # Verificar por idioma
        cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language;")
        by_language = cursor.fetchall()
        logger.info(f"Articles by language: {dict(by_language)}")
        
        # Verificar artículos recientes
        cursor.execute("SELECT title, language, created_at FROM articles ORDER BY created_at DESC LIMIT 5;")
        recent = cursor.fetchall()
        logger.info("Recent articles:")
        for article in recent:
            logger.info(f"  - {article[1]}: {article[0][:50]}... ({article[2]})")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"Database error: {e}")

def test_single_collection():
    """Prueba recolección individual para debug"""
    logger.info("=== TEST SINGLE COLLECTION ===")
    
    try:
        # Inicializar DatabaseManager
        db_manager = DatabaseManager(config)
        db_manager.create_tables()
        
        # Crear collector
        collector = NewsAPICollector()  # Sin parámetros
        
        # Test simple collection
        logger.info("Testing English collection...")
        articles = collector.search_everything(
            query="conflict",
            language="en",
            max_articles=5
        )
        
        if articles:
            logger.info(f"Collected {len(articles)} articles successfully")
            for i, article in enumerate(articles[:3]):
                logger.info(f"  Article {i+1}: {article.get('title', 'No title')[:50]}...")
        else:
            logger.warning("No articles collected")
            
    except Exception as e:
        logger.error(f"Collection test error: {e}")
        import traceback
        traceback.print_exc()

def fix_content_errors():
    """Corrige errores de contenido NoneType"""
    logger.info("=== FIX CONTENT ERRORS ===")
    
    try:
        conn = sqlite3.connect(config.get_database_path())
        cursor = conn.cursor()
        
        # Buscar artículos con contenido NULL
        cursor.execute("SELECT id, title FROM articles WHERE content IS NULL;")
        null_content = cursor.fetchall()
        
        logger.info(f"Found {len(null_content)} articles with NULL content")
        
        # Actualizar con contenido vacío en lugar de NULL
        cursor.execute("UPDATE articles SET content = '' WHERE content IS NULL;")
        conn.commit()
        
        logger.info("Fixed NULL content articles")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Fix content error: {e}")

def main():
    """Función principal de debug"""
    logger.info("STARTING DEBUG SESSION")
    logger.info(f"Python path: {sys.path[:3]}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Debug de la base de datos
    debug_database()
    
    # Corregir errores de contenido
    fix_content_errors()
    
    # Test de recolección
    test_single_collection()
    
    # Debug final
    debug_database()
    
    logger.info("DEBUG SESSION COMPLETED")

if __name__ == "__main__":
    main()
