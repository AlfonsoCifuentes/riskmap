#!/usr/bin/env python3
"""
Script para verificar disponibilidad de datos NLP por fecha
"""

import sqlite3
from datetime import datetime, timedelta

def check_nlp_data_by_date():
    """Verificar datos NLP por fechas"""
    
    try:
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Artículos de hoy con NLP
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE risk_score IS NOT NULL 
            AND created_at > datetime('now', '-24 hours')
        """)
        today_nlp = cursor.fetchone()[0]
        
        # Artículos de últimos 7 días con NLP
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE risk_score IS NOT NULL 
            AND created_at > datetime('now', '-7 days')
        """)
        week_nlp = cursor.fetchone()[0]
        
        # Total con NLP
        cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_score IS NOT NULL")
        total_nlp = cursor.fetchone()[0]
        
        # Verificar formato de fechas
        cursor.execute("SELECT created_at FROM articles LIMIT 5")
        dates = cursor.fetchall()
        
        print(f"Datos NLP por fecha:")
        print(f"  Últimas 24 horas: {today_nlp} artículos")
        print(f"  Últimos 7 días: {week_nlp} artículos")
        print(f"  Total con NLP: {total_nlp} artículos")
        print(f"\nFormatos de fecha (muestra):")
        for date in dates:
            print(f"  {date[0]}")
        
        # Prueba con query específica
        cursor.execute("""
            SELECT title, risk_score, sentiment_label, created_at
            FROM articles 
            WHERE risk_score IS NOT NULL 
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        recent_with_nlp = cursor.fetchall()
        print(f"\n10 artículos más recientes con NLP:")
        for row in recent_with_nlp:
            title, risk, sentiment, date = row
            print(f"  [{risk}] {title[:50]}... - {sentiment} - {date}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_nlp_data_by_date()
