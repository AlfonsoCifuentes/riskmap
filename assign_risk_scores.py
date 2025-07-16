#!/usr/bin/env python3
"""
Script para asignar puntajes de riesgo simulados a los artículos existentes
"""

import sqlite3
import random
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Obtiene conexión a la base de datos"""
    try:
        conn = sqlite3.connect('data/articles.db')
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None

def assign_risk_scores():
    """Asigna puntajes de riesgo simulados basados en palabras clave y categorías"""
    
    conn = get_database_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Palabras clave de alto riesgo
    high_risk_keywords = [
        'war', 'guerra', 'conflict', 'conflicto', 'военный', 'войн', '战争', '紛争',
        'attack', 'ataque', 'crisis', 'bomb', 'explosion', 'terror', 'violence',
        'invasion', 'military', 'missile', 'nuclear', 'weapons', 'assassination'
    ]
    
    medium_risk_keywords = [
        'protest', 'manifestation', 'riot', 'strike', 'election', 'diplomatic',
        'sanction', 'embargo', 'trade', 'economic', 'tension', 'dispute'
    ]
    
    try:
        # Primero añadir la columna si no existe
        try:
            cursor.execute('ALTER TABLE articles ADD COLUMN risk_score REAL')
            logger.info("Columna risk_score añadida")
        except sqlite3.OperationalError:
            logger.info("Columna risk_score ya existe")
        
        # Obtener todos los artículos
        cursor.execute('SELECT id, title, description, content, category FROM articles WHERE risk_score IS NULL')
        articles = cursor.fetchall()
        
        updated_count = 0
        
        for article_id, title, description, content, category in articles:
            # Calcular score basado en contenido
            text_content = f"{title or ''} {description or ''} {content or ''}".lower()
            
            risk_score = 1.0  # Base score
            
            # Aumentar score por palabras clave de alto riesgo
            for keyword in high_risk_keywords:
                if keyword in text_content:
                    risk_score += random.uniform(2.0, 3.5)
            
            # Aumentar score por palabras clave de riesgo medio
            for keyword in medium_risk_keywords:
                if keyword in text_content:
                    risk_score += random.uniform(0.5, 1.5)
            
            # Ajustar por categoría
            if category:
                if category.lower() in ['military_conflict', 'war', 'conflict']:
                    risk_score += random.uniform(1.5, 2.5)
                elif category.lower() in ['protest', 'crisis']:
                    risk_score += random.uniform(0.5, 1.5)
            
            # Añadir variación aleatoria
            risk_score += random.uniform(-0.5, 0.5)
            
            # Limitar entre 0 y 10
            risk_score = max(0, min(10, risk_score))
            
            # Actualizar en la base de datos
            cursor.execute('UPDATE articles SET risk_score = ? WHERE id = ?', (risk_score, article_id))
            updated_count += 1
        
        conn.commit()
        logger.info(f"✅ Asignados puntajes de riesgo a {updated_count} artículos")
        
        # Mostrar estadísticas
        cursor.execute('SELECT COUNT(*), AVG(risk_score), MIN(risk_score), MAX(risk_score) FROM articles WHERE risk_score IS NOT NULL')
        stats = cursor.fetchone()
        logger.info(f"📊 Estadísticas: {stats[0]} artículos, promedio: {stats[1]:.2f}, min: {stats[2]:.2f}, max: {stats[3]:.2f}")
        
        # Mostrar top 10 de mayor riesgo
        cursor.execute('SELECT title, risk_score FROM articles WHERE risk_score IS NOT NULL ORDER BY risk_score DESC LIMIT 10')
        top_risk = cursor.fetchall()
        
        logger.info("🔥 Top 10 artículos de mayor riesgo:")
        for i, (title, score) in enumerate(top_risk, 1):
            logger.info(f"  {i}. {score:.1f} - {title[:80]}...")
        
    except Exception as e:
        logger.error(f"Error asignando puntajes de riesgo: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    logger.info("🎯 Iniciando asignación de puntajes de riesgo...")
    assign_risk_scores()
    logger.info("✅ Proceso completado")
