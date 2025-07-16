"""
Script para verificar los datos del dashboard directamente
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

import sqlite3
import json
from src.utils.config import config

def check_dashboard_data():
    """Verificar datos que debería mostrar el dashboard"""
    print("=== VERIFICACIÓN DATOS DEL DASHBOARD ===")
    
    try:
        # Conectar a la base de datos
        db_path = config.get_database_path()
        print(f"Base de datos: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Estadísticas básicas
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        print(f"Total artículos: {total_articles}")
        
        # Artículos por idioma
        cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language ORDER BY COUNT(*) DESC")
        language_distribution = cursor.fetchall()
        print(f"Distribución por idioma: {dict(language_distribution)}")
        
        # Artículos recientes (últimos 7 días)
        cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-7 days')")
        articles_week = cursor.fetchone()[0]
        print(f"Artículos última semana: {articles_week}")
        
        # Artículos últimas 24 horas
        cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-24 hours')")
        articles_24h = cursor.fetchone()[0]
        print(f"Artículos últimas 24h: {articles_24h}")
        
        # Verificar fechas de los artículos
        cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM articles")
        min_date, max_date = cursor.fetchone()
        print(f"Rango de fechas: {min_date} a {max_date}")
        
        # Ver algunos artículos recientes
        cursor.execute("SELECT title, language, created_at FROM articles ORDER BY created_at DESC LIMIT 5")
        recent_articles = cursor.fetchall()
        print("\nArtículos recientes:")
        for i, (title, lang, date) in enumerate(recent_articles, 1):
            print(f"  {i}. [{lang}] {title[:50]}... ({date})")
        
        conn.close()
        
        # Simular datos del dashboard
        dashboard_data = {
            'total_articles': total_articles,
            'articles_week': articles_week,
            'articles_24h': articles_24h,
            'processed_articles': total_articles,
            'languages_count': len(language_distribution),
            'language_distribution': dict(language_distribution),
            'global_risk_level': 'MEDIUM' if total_articles > 50 else 'LOW'
        }
        
        print(f"\nDatos que debería mostrar el dashboard:")
        print(json.dumps(dashboard_data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_dashboard_data()
