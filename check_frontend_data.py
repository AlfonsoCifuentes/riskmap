#!/usr/bin/env python3
"""
Script para verificar los datos que el frontend debería ver
"""

import sqlite3
import os
import json

def check_frontend_data():
    """Verificar qué datos ve el frontend"""
    db_path = "data/geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Verificando datos que ve el frontend...")
        print("=" * 60)
        
        # Simular la consulta que hace el endpoint /api/articles
        cursor.execute("""
            SELECT id, title, risk_level, created_at, country, summary, image_url
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        
        recent_articles = cursor.fetchall()
        
        print("📊 Artículos que debería mostrar el frontend (últimas 24h):")
        risk_counts = {'high': 0, 'medium': 0, 'low': 0, 'critical': 0, 'null': 0}
        
        for id, title, risk_level, created_at, country, summary, image_url in recent_articles:
            title_short = title[:60] + "..." if title and len(title) > 60 else title or "Sin título"
            risk_counts[risk_level or 'null'] += 1
            
            print(f"   ID {id}: [{risk_level or 'NULL':8}] {title_short}")
            print(f"        País: {country or 'N/A'} | Imagen: {'✅' if image_url else '❌'}")
        
        print(f"\n📈 Distribución en últimas 24h:")
        for risk, count in risk_counts.items():
            if count > 0:
                print(f"   {risk}: {count} artículos")
        
        # Verificar artículos de alto riesgo disponibles
        cursor.execute("""
            SELECT id, title, risk_level, created_at 
            FROM articles 
            WHERE risk_level IN ('high', 'critical')
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        high_risk_articles = cursor.fetchall()
        
        print(f"\n🚨 Últimos artículos de alto riesgo disponibles:")
        for id, title, risk_level, created_at in high_risk_articles:
            title_short = title[:60] + "..." if title and len(title) > 60 else title or "Sin título"
            print(f"   ID {id}: [{risk_level:8}] {title_short}")
            print(f"        Fecha: {created_at}")
        
        # Verificar si hay problemas con la codificación de risk_level
        cursor.execute("""
            SELECT DISTINCT risk_level, COUNT(*) 
            FROM articles 
            WHERE created_at > datetime('now', '-48 hours')
            GROUP BY risk_level
        """)
        
        recent_risk_distribution = cursor.fetchall()
        
        print(f"\n📊 Distribución últimas 48h (para más contexto):")
        for risk, count in recent_risk_distribution:
            print(f"   '{risk}': {count} artículos")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando datos del frontend: {e}")

if __name__ == "__main__":
    check_frontend_data()
