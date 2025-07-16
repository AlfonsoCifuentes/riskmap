#!/usr/bin/env python3
"""
Script para verificar los datos del análisis NLP
"""

import sqlite3
import json

def check_nlp_data():
    """Verificar datos del análisis NLP en la base de datos"""
    
    try:
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tablas disponibles: {tables}")
        
        # Verificar estructura de la tabla articles
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        print(f"\nColumnas en articles: {[col[1] for col in columns]}")
        
        # Contar artículos con análisis NLP
        cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_score IS NOT NULL")
        nlp_count = cursor.fetchone()[0]
        print(f"\nArtículos con análisis NLP: {nlp_count}")
        
        # Ver algunos ejemplos
        cursor.execute("""
            SELECT title, risk_score, sentiment_label, sentiment_score, 
                   key_persons, key_locations 
            FROM articles 
            WHERE risk_score IS NOT NULL 
            ORDER BY risk_score DESC 
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        print(f"\nTop 5 artículos de mayor riesgo:")
        for i, row in enumerate(results, 1):
            title, risk, sentiment_label, sentiment_score, persons, locations = row
            print(f"{i}. [{risk}] {title[:60]}...")
            print(f"   Sentimiento: {sentiment_label} ({sentiment_score})")
            print(f"   Personas: {persons or 'N/A'}")
            print(f"   Ubicaciones: {locations or 'N/A'}")
            print()
        
        # Estadísticas generales
        cursor.execute("SELECT AVG(risk_score), MIN(risk_score), MAX(risk_score) FROM articles WHERE risk_score IS NOT NULL")
        stats = cursor.fetchone()
        print(f"Estadísticas de riesgo: Promedio={stats[0]:.2f}, Min={stats[1]}, Max={stats[2]}")
        
        # Distribución de sentimientos
        cursor.execute("SELECT sentiment_label, COUNT(*) FROM articles WHERE sentiment_label IS NOT NULL GROUP BY sentiment_label")
        sentiment_dist = cursor.fetchall()
        print(f"Distribución de sentimientos: {sentiment_dist}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_nlp_data()
