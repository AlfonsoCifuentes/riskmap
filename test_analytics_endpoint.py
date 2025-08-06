#!/usr/bin/env python3
"""
Script para probar el endpoint de analytics/conflicts y diagnosticar el error 500
"""
import requests
import json
import sqlite3
from datetime import datetime, timedelta

def test_analytics_endpoint():
    """Probar el endpoint de analytics"""
    try:
        print("🧪 Probando endpoint de analytics...")
        
        # Probar el endpoint
        response = requests.get('http://localhost:8050/api/analytics/conflicts')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint funcionando correctamente!")
            print(f"Total conflicts: {data.get('statistics', {}).get('total_conflicts', 0)}")
            print(f"High risk: {data.get('statistics', {}).get('high_risk', 0)}")
            print(f"Medium risk: {data.get('statistics', {}).get('medium_risk', 0)}")
        else:
            print("❌ Error en el endpoint!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error conectando al endpoint: {e}")

def check_database_data():
    """Verificar que hay datos en la base de datos"""
    try:
        print("\n🔍 Verificando datos en la base de datos...")
        
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Verificar total de artículos
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        print(f"Total de artículos: {total_articles}")
        
        # Verificar artículos con risk_level
        cursor.execute("SELECT risk_level, COUNT(*) FROM articles WHERE risk_level IS NOT NULL GROUP BY risk_level")
        risk_levels = cursor.fetchall()
        print(f"Artículos por nivel de riesgo: {risk_levels}")
        
        # Verificar artículos recientes (últimos 7 días)
        cutoff_date = datetime.now() - timedelta(days=7)
        cursor.execute("SELECT COUNT(*) FROM articles WHERE published_at >= ?", (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))
        recent_articles = cursor.fetchone()[0]
        print(f"Artículos recientes (7 días): {recent_articles}")
        
        # Verificar artículos con ubicación
        cursor.execute("SELECT COUNT(*) FROM articles WHERE (key_locations IS NOT NULL OR country IS NOT NULL OR region IS NOT NULL)")
        articles_with_location = cursor.fetchone()[0]
        print(f"Artículos con ubicación: {articles_with_location}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")

def simulate_analytics_query():
    """Simular la consulta que hace el endpoint"""
    try:
        print("\n🔍 Simulando consulta del endpoint...")
        
        timeframe_days = 7
        cutoff_date = datetime.now() - timedelta(days=timeframe_days)
        
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # La misma consulta que usa el endpoint
        cursor.execute("""
            SELECT 
                id, title, key_locations, country, region, risk_level, conflict_type, 
                published_at, url, sentiment_score
            FROM articles 
            WHERE published_at >= ? 
            AND (
                risk_level IN ('high', 'medium') 
                OR sentiment_score < -0.3
                OR conflict_type IS NOT NULL
            )
            AND (key_locations IS NOT NULL OR country IS NOT NULL OR region IS NOT NULL)
            ORDER BY published_at DESC
        """, (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))
        
        conflicts = cursor.fetchall()
        print(f"Conflictos encontrados: {len(conflicts)}")
        
        # Mostrar algunos ejemplos
        if conflicts:
            print("\nPrimeros 3 conflictos:")
            for i, conflict in enumerate(conflicts[:3]):
                print(f"  {i+1}. {conflict[1][:50]}... (Risk: {conflict[5]}, Region: {conflict[4] or conflict[3] or conflict[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error simulando consulta: {e}")

if __name__ == "__main__":
    check_database_data()
    simulate_analytics_query()
    test_analytics_endpoint()
