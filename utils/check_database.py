#!/usr/bin/env python3
"""
Script para verificar el estado de la base de datos
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Ruta de la base de datos
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')

def check_database():
    """Verificar el estado de la base de datos."""
    try:
        print(f"🔍 Verificando base de datos: {DB_PATH}")
        print("-" * 60)
        
        # Verificar si el archivo existe
        if not Path(DB_PATH).exists():
            print("❌ La base de datos no existe!")
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tablas encontradas: {', '.join(tables)}")
        
        if 'articles' in tables:
            # Verificar artículos
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            print(f"📰 Total artículos: {total_articles}")
            
            if total_articles > 0:
                # Artículos por nivel de riesgo
                cursor.execute("""
                    SELECT risk_level, COUNT(*) as count
                    FROM articles 
                    GROUP BY risk_level
                """)
                risk_levels = cursor.fetchall()
                print("🎯 Distribución por riesgo:")
                for level, count in risk_levels:
                    print(f"   - {level or 'Sin clasificar'}: {count}")
                
                # Artículos recientes
                cursor.execute("""
                    SELECT title, created_at, risk_level, country
                    FROM articles 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                recent = cursor.fetchall()
                print("\n📅 Últimos 5 artículos:")
                for title, date, risk, country in recent:
                    print(f"   - {title[:50]}... ({risk}, {country or 'Global'})")
                
                # Artículos de alto riesgo
                cursor.execute("""
                    SELECT COUNT(*) FROM articles WHERE risk_level = 'high'
                """)
                high_risk = cursor.fetchone()[0]
                print(f"\n🚨 Artículos de alto riesgo: {high_risk}")
                
                if high_risk > 0:
                    cursor.execute("""
                        SELECT title, country, created_at
                        FROM articles 
                        WHERE risk_level = 'high'
                        ORDER BY created_at DESC 
                        LIMIT 3
                    """)
                    high_risk_articles = cursor.fetchall()
                    print("   Ejemplos:")
                    for title, country, date in high_risk_articles:
                        print(f"   - {title[:40]}... ({country or 'Global'})")
        
        if 'events' in tables:
            # Verificar eventos
            cursor.execute("SELECT COUNT(*) FROM events")
            total_events = cursor.fetchone()[0]
            print(f"\n🌍 Total eventos: {total_events}")
            
            if total_events > 0:
                # Eventos con ubicación
                cursor.execute("""
                    SELECT COUNT(*) FROM events 
                    WHERE location IS NOT NULL AND location != ''
                """)
                events_with_location = cursor.fetchone()[0]
                print(f"📍 Eventos con ubicación: {events_with_location}")
        
        # Verificar datos recientes (últimas 24 horas)
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE datetime(created_at) > datetime('now', '-24 hours')
        """)
        recent_articles = cursor.fetchone()[0]
        print(f"\n⏰ Artículos últimas 24h: {recent_articles}")
        
        # Países activos
        cursor.execute("""
            SELECT COUNT(DISTINCT country) FROM articles 
            WHERE country IS NOT NULL
        """)
        active_countries = cursor.fetchone()[0]
        print(f"🌎 Países con actividad: {active_countries}")
        
        conn.close()
        
        print("\n✅ Verificación completada")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def test_api_endpoints():
    """Probar que los endpoints de la API funcionan."""
    import requests
    
    print("\n🔗 Probando endpoints de la API...")
    print("-" * 60)
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/api/test",
        "/api/dashboard/stats", 
        "/api/articles",
        "/api/articles/latest",
        "/api/articles/high-risk",
        "/api/articles/featured",
        "/api/events/heatmap"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if endpoint == "/api/test":
                    print(f"✅ {endpoint}: {data.get('message', 'OK')}")
                elif endpoint == "/api/dashboard/stats":
                    stats = data.get('stats', {})
                    print(f"✅ {endpoint}: {stats.get('total_articles', 0)} artículos")
                elif endpoint == "/api/articles":
                    articles = data if isinstance(data, list) else []
                    print(f"✅ {endpoint}: {len(articles)} artículos")
                elif endpoint == "/api/articles/latest":
                    articles = data if isinstance(data, list) else []
                    print(f"✅ {endpoint}: {len(articles)} últimos artículos")
                elif endpoint == "/api/articles/high-risk":
                    articles = data if isinstance(data, list) else []
                    print(f"✅ {endpoint}: {len(articles)} artículos alto riesgo")
                elif endpoint == "/api/articles/featured":
                    title = data.get('title', 'Sin título')
                    print(f"✅ {endpoint}: {title[:50]}...")
                elif endpoint == "/api/events/heatmap":
                    points = data if isinstance(data, list) else []
                    print(f"✅ {endpoint}: {len(points)} puntos en mapa")
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"🔌 {endpoint}: Servidor no disponible")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)}")

if __name__ == "__main__":
    print("🚀 Verificación del Sistema Riskmap")
    print("=" * 60)
    
    # Verificar base de datos
    db_ok = check_database()
    
    if db_ok:
        print("\n💡 La base de datos está funcionando correctamente.")
        print("   Puedes iniciar el dashboard con:")
        print("   python src/dashboard/app_modern.py")
        
        # Preguntar si quiere probar la API
        try:
            test_api = input("\n¿Quieres probar los endpoints de la API? (y/n): ").lower().strip()
            if test_api == 'y':
                test_api_endpoints()
        except KeyboardInterrupt:
            print("\n👋 Verificación cancelada")
    else:
        print("\n❌ Hay problemas con la base de datos.")
        print("   Ejecuta primero el sistema de ingesta:")
        print("   python run_complete_rss_system.py")