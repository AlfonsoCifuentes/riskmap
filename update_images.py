"""
Script para actualizar las imágenes de los artículos existentes
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
from utils.image_extractor import NewsImageExtractor
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_articles_images():
    """
    Actualizar las imágenes de los artículos que no las tienen
    """
    db_path = 'data/geopolitical_intel.db'
    
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        extractor = NewsImageExtractor()
        
        # Actualizar imágenes
        updated_count = extractor.update_article_images(conn)
        
        conn.close()
        
        logger.info(f"✅ Process completed. Updated {updated_count} articles with images.")
        
        # Mostrar algunos ejemplos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, source, image_url 
            FROM articles 
            WHERE image_url IS NOT NULL AND image_url != ''
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        articles = cursor.fetchall()
        logger.info("\n📸 Ejemplos de artículos con imágenes:")
        for i, (title, source, image_url) in enumerate(articles, 1):
            logger.info(f"{i}. {title[:60]}... ({source})")
            logger.info(f"   Imagen: {image_url[:80]}...")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error updating images: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting image extraction for articles...")
    update_articles_images()
