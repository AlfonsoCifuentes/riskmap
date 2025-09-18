#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 DIAGNÓSTICO DE ERROR GDELT API
================================
Diagnosticar el error 500 en /api/gdelt-events
"""

import sqlite3
import traceback
from pathlib import Path

def get_database_path():
    """Obtener la ruta de la base de datos"""
    return Path("data/geopolitical_intel.db")

def diagnose_gdelt_error():
    """Diagnosticar problemas con la API de GDELT"""
    print("🔍 DIAGNÓSTICO DEL ERROR EN GDELT API")
    print("=" * 50)
    
    db_path = get_database_path()
    
    if not db_path.exists():
        print(f"❌ Base de datos no existe: {db_path}")
        return
        
    print(f"✅ Base de datos encontrada: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Verificar tablas disponibles
            print("\n1. 📋 TABLAS DISPONIBLES:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                if 'gdelt' in table.lower():
                    print(f"   🎯 {table} (GDELT relacionado)")
                else:
                    print(f"   • {table}")
            
            # 2. Verificar tabla gdelt_events específicamente
            print("\n2. 🎯 TABLA gdelt_events:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gdelt_events'")
            has_gdelt = cursor.fetchone()
            
            if has_gdelt:
                print("   ✅ Tabla gdelt_events existe")
                
                # Verificar estructura de la tabla
                cursor.execute("PRAGMA table_info(gdelt_events)")
                columns = cursor.fetchall()
                
                print("   📊 Columnas disponibles:")
                expected_columns = ['event_id', 'event_date', 'actor1_name', 'actor2_name', 
                                  'event_code', 'event_description', 'country_code',
                                  'latitude', 'longitude', 'avg_tone', 'goldstein_scale']
                
                existing_columns = [col[1] for col in columns]
                
                for col in columns:
                    col_name = col[1]
                    if col_name in expected_columns:
                        print(f"      ✅ {col_name} ({col[2]})")
                    else:
                        print(f"      ℹ️  {col_name} ({col[2]})")
                
                # Verificar columnas faltantes
                missing = [col for col in expected_columns if col not in existing_columns]
                if missing:
                    print(f"   ❌ Columnas faltantes: {missing}")
                
                # Verificar datos
                cursor.execute("SELECT COUNT(*) FROM gdelt_events")
                count = cursor.fetchone()[0]
                print(f"   📊 Registros: {count}")
                
                if count > 0:
                    print("   ✅ Tabla tiene datos")
                    # Mostrar una muestra
                    cursor.execute("SELECT * FROM gdelt_events LIMIT 1")
                    sample = cursor.fetchone()
                    if sample:
                        print(f"   📝 Muestra: {sample[:5]}...")
                else:
                    print("   ⚠️  Tabla vacía")
                    
            else:
                print("   ⚠️  Tabla gdelt_events no existe")
            
            # 3. Verificar tabla articles como fallback
            print("\n3. 📰 TABLA articles (fallback):")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
            has_articles = cursor.fetchone()
            
            if has_articles:
                cursor.execute("PRAGMA table_info(articles)")
                columns = cursor.fetchall()
                
                needed_columns = ['id', 'title', 'country', 'published_at', 'risk_score', 'risk_level']
                existing_columns = [col[1] for col in columns]
                
                print("   ✅ Tabla articles existe")
                print("   📊 Columnas requeridas para fallback:")
                
                for col in needed_columns:
                    if col in existing_columns:
                        print(f"      ✅ {col}")
                    else:
                        print(f"      ❌ {col} (FALTANTE)")
                
                # Contar artículos procesados recientes
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE processed = 1 
                    AND created_at > datetime('now', '-1 day')
                """)
                recent_count = cursor.fetchone()[0]
                print(f"   📊 Artículos procesados (últimas 24h): {recent_count}")
                
            else:
                print("   ❌ Tabla articles no existe")
                
    except Exception as e:
        print(f"\n❌ ERROR DURANTE DIAGNÓSTICO:")
        print(f"   Error: {str(e)}")
        traceback.print_exc()

def test_gdelt_query():
    """Probar la consulta GDELT específica que falla"""
    print(f"\n🧪 PROBANDO CONSULTA GDELT:")
    print("=" * 40)
    
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Probar la consulta exacta que falla
            print("Ejecutando consulta GDELT...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gdelt_events'")
            has_gdelt = cursor.fetchone()
            
            if has_gdelt:
                print("✅ Tabla existe, probando SELECT...")
                try:
                    cursor.execute("""
                        SELECT 
                            event_id, event_date, actor1_name, actor2_name,
                            event_code, event_description, country_code,
                            latitude, longitude, avg_tone, goldstein_scale
                        FROM gdelt_events
                        ORDER BY event_date DESC
                        LIMIT 10
                    """)
                    
                    results = cursor.fetchall()
                    print(f"✅ Consulta exitosa: {len(results)} resultados")
                    
                except Exception as e:
                    print(f"❌ Error en consulta GDELT: {e}")
                    
                    # Probar consulta simplificada
                    try:
                        cursor.execute("SELECT * FROM gdelt_events LIMIT 1")
                        simple_result = cursor.fetchone()
                        print(f"✅ Consulta simple funciona: {simple_result is not None}")
                    except Exception as e2:
                        print(f"❌ Error en consulta simple: {e2}")
            else:
                print("ℹ️  Tabla gdelt_events no existe, probando fallback...")
                
                try:
                    cursor.execute("""
                        SELECT 
                            id, title, country, published_at, risk_score, risk_level
                        FROM articles 
                        WHERE processed = 1
                        AND created_at > datetime('now', '-1 day')
                        ORDER BY risk_score DESC
                        LIMIT 10
                    """)
                    
                    results = cursor.fetchall()
                    print(f"✅ Consulta fallback exitosa: {len(results)} resultados")
                    
                except Exception as e:
                    print(f"❌ Error en consulta fallback: {e}")
                    
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")

def main():
    try:
        diagnose_gdelt_error()
        test_gdelt_query()
        
        print(f"\n🎯 RECOMENDACIONES:")
        print("=" * 30)
        print("1. Verificar columnas faltantes en gdelt_events")
        print("2. Verificar columnas en tabla articles para fallback")
        print("3. Usar manejo de errores más robusto en la API")
        
    except Exception as e:
        print(f"❌ Error en diagnóstico general: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()