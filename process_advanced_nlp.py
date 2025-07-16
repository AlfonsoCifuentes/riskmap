#!/usr/bin/env python3
"""
Script para procesar artículos existentes con análisis NLP avanzado
Utiliza NuNER, análisis de sentimientos y cálculo de riesgo avanzado
"""

import sqlite3
import logging
import json
from datetime import datetime
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp_processing.advanced_analyzer import get_nlp_analyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Obtiene conexión a la base de datos"""
    try:
        conn = sqlite3.connect('data/geopolitical_intel.db')
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None

def add_analysis_columns(cursor):
    """Añade columnas para el análisis avanzado"""
    columns_to_add = [
        ('risk_score', 'REAL'),
        ('sentiment_score', 'REAL'),
        ('sentiment_label', 'TEXT'),
        ('entities_json', 'TEXT'),
        ('key_persons', 'TEXT'),
        ('key_locations', 'TEXT'),
        ('conflict_indicators', 'TEXT'),
        ('analysis_timestamp', 'TEXT')
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE articles ADD COLUMN {column_name} {column_type}')
            logger.info(f"Columna {column_name} añadida")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info(f"Columna {column_name} ya existe")
            else:
                logger.error(f"Error añadiendo columna {column_name}: {e}")

def process_articles_with_advanced_nlp():
    """Procesa artículos con análisis NLP avanzado"""
    
    conn = get_database_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Añadir columnas si no existen
    add_analysis_columns(cursor)
    
    # Inicializar analizador
    logger.info("🧠 Inicializando analizador NLP avanzado...")
    analyzer = get_nlp_analyzer()
    
    try:
        # Obtener TODOS los artículos sin análisis avanzado
        cursor.execute("""
            SELECT id, title, summary, content, url, source, language, conflict_type
            FROM articles 
            WHERE risk_score IS NULL OR sentiment_score IS NULL
        """)
        
        articles = cursor.fetchall()
        logger.info(f"📊 Procesando {len(articles)} artículos...")
        
        processed_count = 0
        
        for row in articles:
            article_id, title, summary, content, url, source, language, category = row
            
            try:
                # Preparar datos del artículo
                article_data = {
                    'title': title or '',
                    'description': summary or '',  # Usar summary como description
                    'content': content or '',
                    'url': url or '',
                    'source_name': source or '',
                    'language': language or '',
                    'category': category or ''
                }
                
                # Realizar análisis comprehensivo
                analysis = analyzer.analyze_article_comprehensive(article_data)
                
                # Preparar datos para inserción
                entities_json = json.dumps(analysis['entities'], ensure_ascii=False)
                key_persons = json.dumps(analysis['key_persons'], ensure_ascii=False)
                key_locations = json.dumps(analysis['key_locations'], ensure_ascii=False)
                conflict_indicators = json.dumps(analysis['conflict_indicators'], ensure_ascii=False)
                
                # Actualizar base de datos
                cursor.execute("""
                    UPDATE articles SET 
                        risk_score = ?,
                        sentiment_score = ?,
                        sentiment_label = ?,
                        entities_json = ?,
                        key_persons = ?,
                        key_locations = ?,
                        conflict_indicators = ?,
                        analysis_timestamp = ?
                    WHERE id = ?
                """, (
                    analysis['risk_score'],
                    analysis['sentiment']['score'],
                    analysis['sentiment']['label'],
                    entities_json,
                    key_persons,
                    key_locations,
                    conflict_indicators,
                    analysis['analysis_timestamp'],
                    article_id
                ))
                
                processed_count += 1
                
                if processed_count % 10 == 0:
                    logger.info(f"✅ Procesados {processed_count} artículos...")
                    conn.commit()  # Commit parcial
                
            except Exception as e:
                logger.error(f"Error procesando artículo {article_id}: {e}")
                continue
        
        # Commit final
        conn.commit()
        logger.info(f"🎯 Procesamiento completado: {processed_count} artículos analizados")
        
        # Mostrar estadísticas
        show_analysis_statistics(cursor)
        
    except Exception as e:
        logger.error(f"Error en procesamiento: {e}")
        conn.rollback()
    finally:
        conn.close()

def show_analysis_statistics(cursor):
    """Muestra estadísticas del análisis"""
    try:
        # Estadísticas de riesgo
        cursor.execute("""
            SELECT COUNT(*), AVG(risk_score), MIN(risk_score), MAX(risk_score)
            FROM articles WHERE risk_score IS NOT NULL
        """)
        risk_stats = cursor.fetchone()
        logger.info(f"📊 Estadísticas de Riesgo: {risk_stats[0]} artículos, promedio: {risk_stats[1]:.2f}")
        
        # Estadísticas de sentimiento
        cursor.execute("""
            SELECT sentiment_label, COUNT(*), AVG(sentiment_score)
            FROM articles 
            WHERE sentiment_label IS NOT NULL
            GROUP BY sentiment_label
        """)
        sentiment_stats = cursor.fetchall()
        logger.info("📊 Distribución de Sentimientos:")
        for label, count, avg_score in sentiment_stats:
            logger.info(f"  {label}: {count} artículos (promedio: {avg_score:.2f})")
        
        # Top artículos de mayor riesgo
        cursor.execute("""
            SELECT title, risk_score, sentiment_label, key_persons
            FROM articles 
            WHERE risk_score IS NOT NULL
            ORDER BY risk_score DESC
            LIMIT 5
        """)
        top_risk = cursor.fetchall()
        logger.info("🔥 Top 5 artículos de mayor riesgo:")
        for i, (title, risk_score, sentiment, persons) in enumerate(top_risk, 1):
            logger.info(f"  {i}. [{risk_score:.1f}] {title[:60]}...")
            if persons and persons != '[]':
                logger.info(f"      Personas: {persons}")
        
    except Exception as e:
        logger.error(f"Error mostrando estadísticas: {e}")

if __name__ == '__main__':
    logger.info("🚀 Iniciando procesamiento NLP avanzado...")
    process_articles_with_advanced_nlp()
    logger.info("✅ Procesamiento completado")
