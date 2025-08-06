#!/usr/bin/env python3
"""Script para verificar el estado de los datos de geolocalización y análisis."""

import sqlite3
import json
from datetime import datetime

def check_geolocation_data():
    """Verificar datos de geolocalización en la base de datos."""
    try:
        db_path = "./data/geopolitical_intel.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("🗺️ VERIFICANDO DATOS DE GEOLOCALIZACIÓN")
            print("=" * 60)
            
            # Verificar tabla conflict_geolocation
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conflict_geolocation'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM conflict_geolocation")
                count = cursor.fetchone()[0]
                print(f"📍 Conflictos geolocalizados: {count}")
                
                if count > 0:
                    cursor.execute("""
                        SELECT latitude, longitude, location_name, confidence_score, created_at 
                        FROM conflict_geolocation 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """)
                    recent = cursor.fetchall()
                    print("\n🔍 Últimas 5 geolocalizaciones:")
                    for row in recent:
                        print(f"   📍 {row[2]} ({row[0]:.3f}, {row[1]:.3f}) - Confianza: {row[3]:.2f}")
            else:
                print("❌ Tabla conflict_geolocation no existe")
            
            # Verificar tabla conflict_cache
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conflict_cache'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM conflict_cache")
                count = cursor.fetchone()[0]
                print(f"💾 Entradas en caché de conflictos: {count}")
                
                if count > 0:
                    cursor.execute("""
                        SELECT cache_key, created_at, data 
                        FROM conflict_cache 
                        ORDER BY created_at DESC 
                        LIMIT 3
                    """)
                    recent = cursor.fetchall()
                    print("\n🔍 Últimas 3 entradas en caché:")
                    for row in recent:
                        try:
                            data = json.loads(row[2])
                            zones = len(data.get('conflict_zones', []))
                            print(f"   🔑 {row[0]}: {zones} zonas de conflicto")
                        except:
                            print(f"   🔑 {row[0]}: datos no válidos")
            else:
                print("❌ Tabla conflict_cache no existe")
            
            # Verificar artículos con riesgo alto
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE risk_level = 'high' AND created_at > datetime('now', '-72 hours')
            """)
            high_risk = cursor.fetchone()[0]
            print(f"⚠️ Artículos de riesgo alto (últimas 72h): {high_risk}")
            
            # Verificar artículos procesados recientemente
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE nlp_processed = 1 AND created_at > datetime('now', '-24 hours')
            """)
            processed = cursor.fetchone()[0]
            print(f"🤖 Artículos procesados con NLP (últimas 24h): {processed}")
            
            print("\n📊 RECOMENDACIONES:")
            if count == 0:
                print("   🔧 Ejecutar análisis de geolocalización para generar zonas de conflicto")
                print("   🔧 Verificar que hay artículos de riesgo alto para analizar")
            
            if high_risk == 0:
                print("   🔧 Verificar que el análisis de riesgo está funcionando correctamente")
                print("   🔧 Revisar los criterios de clasificación de riesgo")
                
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")

if __name__ == "__main__":
    check_geolocation_data()
