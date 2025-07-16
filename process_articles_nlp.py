#!/usr/bin/env python3
"""
Script para procesar artículos existentes con análisis NLP avanzado.
Añade clasificación de riesgo, tipo de conflicto, país y región.
"""

import sys
import sqlite3
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from utils.config import config, DatabaseManager
from nlp_processing.text_analyzer import TextAnalyzer
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_existing_articles():
    """Procesa todos los artículos existentes con análisis NLP."""
    
    logger.info("🚀 Iniciando procesamiento NLP de artículos existentes...")
    
    # Initialize components
    db = DatabaseManager(config)
    analyzer = TextAnalyzer()
    
    # Get database connection
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # First, let's make sure the required columns exist
    logger.info("📊 Verificando estructura de la base de datos...")
    
    # Add missing columns if they don't exist
    columns_to_add = [
        ('risk_level', 'TEXT'),
        ('conflict_type', 'TEXT'),
        ('country', 'TEXT'),
        ('region', 'TEXT'),
        ('sentiment_score', 'REAL'),
        ('summary', 'TEXT')
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}")
            logger.info(f"✅ Agregada columna '{column_name}'")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info(f"ℹ️ Columna '{column_name}' ya existe")
            else:
                logger.error(f"❌ Error agregando columna '{column_name}': {e}")
    
    conn.commit()
    
    # Get all articles that need processing
    cursor.execute("""
        SELECT id, title, content, url, source, language 
        FROM articles 
        WHERE risk_level IS NULL OR risk_level = ''
        ORDER BY created_at DESC
    """)
    
    articles = cursor.fetchall()
    total_articles = len(articles)
    
    logger.info(f"📰 Encontrados {total_articles} artículos para procesar")
    
    if total_articles == 0:
        logger.info("✅ No hay artículos que procesar")
        conn.close()
        return
    
    processed_count = 0
    
    for article in articles:
        article_id, title, content, url, source, language = article
        
        try:
            logger.info(f"🔍 Procesando artículo {processed_count + 1}/{total_articles}: {title[:50]}...")
            
            # Combine title and content for analysis
            text_to_analyze = f"{title}. {content[:1000] if content else ''}"
            
            # Perform NLP analysis
            analysis_result = analyzer.analyze_article({
                'title': title,
                'content': content,
                'language': language,
                'source': source,
                'url': url
            })
            
            # Extract analysis results
            risk_level = analysis_result.get('risk_level', 'LOW')
            conflict_type = analysis_result.get('conflict_type', 'Other')
            country = analysis_result.get('country', 'Global')
            region = analysis_result.get('region', 'International')
            sentiment_score = analysis_result.get('sentiment_score', 0.0)
            summary = analysis_result.get('summary', title[:200] + '...' if len(title) > 200 else title)
            
            # Update article in database
            cursor.execute("""
                UPDATE articles 
                SET risk_level = ?, conflict_type = ?, country = ?, region = ?, 
                    sentiment_score = ?, summary = ?
                WHERE id = ?
            """, (risk_level, conflict_type, country, region, sentiment_score, summary, article_id))
            
            processed_count += 1
            
            # Commit every 10 articles
            if processed_count % 10 == 0:
                conn.commit()
                logger.info(f"💾 Progreso guardado: {processed_count}/{total_articles}")
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"❌ Error procesando artículo {article_id}: {e}")
            continue
    
    # Final commit
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Procesamiento completado! {processed_count}/{total_articles} artículos procesados")
    
    # Show some statistics
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT risk_level, COUNT(*) FROM articles WHERE risk_level IS NOT NULL GROUP BY risk_level")
    risk_stats = cursor.fetchall()
    
    cursor.execute("SELECT conflict_type, COUNT(*) FROM articles WHERE conflict_type IS NOT NULL GROUP BY conflict_type")
    conflict_stats = cursor.fetchall()
    
    logger.info("📊 Estadísticas de clasificación:")
    logger.info("🔥 Por nivel de riesgo:")
    for risk, count in risk_stats:
        logger.info(f"   {risk}: {count} artículos")
    
    logger.info("⚔️ Por tipo de conflicto:")
    for conflict, count in conflict_stats:
        logger.info(f"   {conflict}: {count} artículos")
    
    conn.close()

if __name__ == "__main__":
    process_existing_articles()
