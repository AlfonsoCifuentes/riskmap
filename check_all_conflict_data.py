#!/usr/bin/env python3
"""
Verificar todas las fuentes de datos de conflictos y localización
"""

import sqlite3
import json

def check_all_conflict_data():
    """Verificar todas las fuentes de datos de conflictos disponibles"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        print("🗃️ VERIFICANDO TODAS LAS FUENTES DE DATOS DE CONFLICTOS...")
        
        # 1. Verificar todas las tablas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        all_tables = cursor.fetchall()
        print("\n📋 TODAS LAS TABLAS DISPONIBLES:")
        for table in all_tables:
            print(f"   📊 {table[0]}")
        
        # 2. Verificar tabla de artículos (fuente principal)
        print("\n🎯 VERIFICANDO TABLA DE ARTÍCULOS...")
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        print(f"📰 Total artículos: {total_articles}")
        
        if total_articles > 0:
            # Verificar artículos con análisis de riesgo
            cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_score IS NOT NULL")
            with_risk = cursor.fetchone()[0]
            print(f"⚠️ Con análisis de riesgo: {with_risk}")
            
            # Verificar artículos de alto riesgo recientes
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE risk_score > 0.7 
                AND published_at > date('now', '-7 days')
            """)
            high_risk_recent = cursor.fetchone()[0]
            print(f"🚨 Alto riesgo últimos 7 días: {high_risk_recent}")
            
            # Obtener ejemplos de artículos de alto riesgo
            cursor.execute("""
                SELECT id, title, risk_score, published_at, url 
                FROM articles 
                WHERE risk_score > 0.7 
                ORDER BY risk_score DESC, published_at DESC
                LIMIT 5
            """)
            
            high_risk_examples = cursor.fetchall()
            print("\n🔍 EJEMPLOS DE ARTÍCULOS DE ALTO RIESGO:")
            for ex in high_risk_examples:
                print(f"   📰 ID: {ex[0]} | Risk: {ex[2]:.2f} | {ex[1][:60]}...")
        
        # 3. Verificar tabla ai_detected_conflicts
        print("\n🎯 VERIFICANDO CONFLICTOS DETECTADOS POR IA...")
        try:
            cursor.execute("SELECT COUNT(*) FROM ai_detected_conflicts")
            total_conflicts = cursor.fetchone()[0]
            print(f"⚔️ Total conflictos detectados: {total_conflicts}")
            
            if total_conflicts > 0:
                # Verificar con coordenadas
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_detected_conflicts 
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                """)
                with_coords = cursor.fetchone()[0]
                print(f"🌍 Con coordenadas: {with_coords}")
                
                # Verificar activos
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_detected_conflicts 
                    WHERE is_active = 1
                """)
                active = cursor.fetchone()[0]
                print(f"✅ Activos: {active}")
                
                # Obtener ejemplos
                cursor.execute("""
                    SELECT location, latitude, longitude, risk_level, confidence, detected_at
                    FROM ai_detected_conflicts 
                    WHERE is_active = 1
                    AND latitude IS NOT NULL 
                    AND longitude IS NOT NULL
                    ORDER BY confidence DESC, detected_at DESC
                    LIMIT 10
                """)
                
                conflict_examples = cursor.fetchall()
                print("\n🔍 EJEMPLOS DE CONFLICTOS CON COORDENADAS:")
                for ex in conflict_examples:
                    print(f"   📍 {ex[0]} | ({ex[1]:.4f}, {ex[2]:.4f}) | {ex[3]} | Conf: {ex[4]:.2f}")
        
        except Exception as e:
            print(f"❌ Error con ai_detected_conflicts: {e}")
        
        # 4. Verificar otras tablas de conflictos
        conflict_tables = ['acled_events', 'conflict_events', 'external_feeds']
        for table_name in conflict_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"\n📊 {table_name}: {count} registros")
                
                if count > 0:
                    # Verificar estructura
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    location_cols = [col[1] for col in columns if any(kw in col[1].lower() for kw in ['lat', 'lon', 'geo', 'location', 'country'])]
                    if location_cols:
                        print(f"   🌍 Columnas de localización: {location_cols}")
                        
                        # Obtener ejemplos
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                        examples = cursor.fetchall()
                        for i, ex in enumerate(examples):
                            print(f"   📋 Ejemplo {i+1}: {ex[:5]}...")  # Primeros 5 campos
            
            except Exception as e:
                print(f"   ❌ Tabla {table_name} no existe o error: {e}")
        
        # 5. Verificar feeds externos actualizados
        print("\n🎯 VERIFICANDO FEEDS EXTERNOS...")
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE name LIKE '%feed%' OR name LIKE '%external%'")
            feed_tables = cursor.fetchall()
            
            for table in feed_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"   📡 {table[0]}: {count} registros")
        
        except Exception as e:
            print(f"❌ Error verificando feeds: {e}")
        
        # 6. Análisis de cobertura geográfica
        print("\n🌍 ANÁLISIS DE COBERTURA GEOGRÁFICA...")
        
        # Desde artículos con palabras clave de conflicto
        conflict_keywords = ['gaza', 'ukraine', 'russia', 'war', 'conflict', 'crisis', 'syria', 'israel', 'palestine']
        
        for keyword in conflict_keywords:
            cursor.execute(f"""
                SELECT COUNT(*) FROM articles 
                WHERE (title LIKE '%{keyword}%' OR content LIKE '%{keyword}%')
                AND published_at > date('now', '-30 days')
            """)
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"   🔍 '{keyword.upper()}': {count} artículos (últimos 30 días)")
        
        conn.close()
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_all_conflict_data()
