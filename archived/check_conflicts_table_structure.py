#!/usr/bin/env python3
"""
Verificar estructura actual de la tabla ai_detected_conflicts
"""

import sqlite3

def check_conflicts_table():
    """Verificar la tabla ai_detected_conflicts"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ai_detected_conflicts'
        """)
        
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ Tabla 'ai_detected_conflicts' existe")
            
            # Verificar columnas
            cursor.execute("PRAGMA table_info(ai_detected_conflicts)")
            columns = cursor.fetchall()
            
            print("📋 COLUMNAS:")
            for col in columns:
                print(f"   {col[1]} ({col[2]})")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM ai_detected_conflicts")
            total = cursor.fetchone()[0]
            print(f"\n📊 Total registros: {total}")
            
            if total > 0:
                # Verificar registros activos
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_detected_conflicts 
                    WHERE is_active = 1
                """)
                active = cursor.fetchone()[0]
                print(f"⚡ Registros activos: {active}")
                
                # Verificar con coordenadas
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_detected_conflicts 
                    WHERE is_active = 1 
                    AND latitude IS NOT NULL 
                    AND longitude IS NOT NULL
                """)
                with_coords = cursor.fetchone()[0]
                print(f"🌍 Con coordenadas: {with_coords}")
                
                # Verificar con alta confianza
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_detected_conflicts 
                    WHERE is_active = 1 
                    AND confidence >= 0.8
                    AND latitude IS NOT NULL 
                    AND longitude IS NOT NULL
                """)
                high_confidence = cursor.fetchone()[0]
                print(f"🎯 Alta confianza (>=0.8): {high_confidence}")
                
                # Mostrar algunos ejemplos
                cursor.execute("""
                    SELECT id, location, latitude, longitude, confidence, risk_level, detected_at
                    FROM ai_detected_conflicts 
                    WHERE is_active = 1
                    AND confidence >= 0.8
                    ORDER BY confidence DESC, detected_at DESC
                    LIMIT 5
                """)
                
                examples = cursor.fetchall()
                if examples:
                    print("\n🔍 EJEMPLOS DE REGISTROS:")
                    for ex in examples:
                        print(f"   ID: {ex[0]} | {ex[1]} | ({ex[2]}, {ex[3]}) | Conf: {ex[4]} | Risk: {ex[5]}")
                else:
                    print("\n❌ No hay registros que cumplan los criterios del endpoint")
            
        else:
            print("❌ Tabla 'ai_detected_conflicts' NO EXISTE")
            
            # Verificar qué tablas existen
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            tables = cursor.fetchall()
            print("\n📝 TABLAS EXISTENTES:")
            for table in tables:
                print(f"   {table[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    check_conflicts_table()
