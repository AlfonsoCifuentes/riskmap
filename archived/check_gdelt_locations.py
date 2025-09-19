#!/usr/bin/env python3
"""
Verificar información de localización precisa en GDELT
"""

import sqlite3
import json
from datetime import datetime, timedelta

def check_gdelt_locations():
    """Verificar qué conflictos tienen información de localización precisa en GDELT"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Verificar si existe la tabla de eventos GDELT
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%gdelt%'
        """)
        
        gdelt_tables = cursor.fetchall()
        print("🗃️ TABLAS GDELT DISPONIBLES:")
        for table in gdelt_tables:
            print(f"   📋 {table[0]}")
        
        if not gdelt_tables:
            print("❌ No se encontraron tablas GDELT")
            return
        
        # Verificar la tabla principal de eventos GDELT
        main_table = None
        for table in gdelt_tables:
            if 'events' in table[0].lower() or 'gdelt' in table[0].lower():
                main_table = table[0]
                break
        
        if not main_table:
            main_table = gdelt_tables[0][0]  # Usar la primera tabla disponible
        
        print(f"\n🎯 ANALIZANDO TABLA: {main_table}")
        
        # Verificar estructura de la tabla
        cursor.execute(f"PRAGMA table_info({main_table})")
        columns = cursor.fetchall()
        
        print("\n📋 COLUMNAS DISPONIBLES:")
        location_columns = []
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
            if any(keyword in col[1].lower() for keyword in ['lat', 'lon', 'geo', 'location', 'country', 'region']):
                location_columns.append(col[1])
        
        print(f"\n🌍 COLUMNAS DE LOCALIZACIÓN: {location_columns}")
        
        # Contar registros totales
        cursor.execute(f"SELECT COUNT(*) FROM {main_table}")
        total = cursor.fetchone()[0]
        print(f"\n📊 TOTAL REGISTROS GDELT: {total}")
        
        if total == 0:
            print("❌ No hay registros en la tabla GDELT")
            return
        
        # Buscar registros con coordenadas
        lat_cols = [col for col in location_columns if 'lat' in col.lower()]
        lon_cols = [col for col in location_columns if 'lon' in col.lower()]
        
        if lat_cols and lon_cols:
            lat_col = lat_cols[0]
            lon_col = lon_cols[0]
            
            cursor.execute(f"""
                SELECT COUNT(*) FROM {main_table} 
                WHERE {lat_col} IS NOT NULL 
                AND {lon_col} IS NOT NULL
                AND {lat_col} != 0 
                AND {lon_col} != 0
            """)
            
            with_coords = cursor.fetchone()[0]
            print(f"🎯 REGISTROS CON COORDENADAS: {with_coords}")
            
            if with_coords > 0:
                # Obtener ejemplos de eventos con coordenadas
                cursor.execute(f"""
                    SELECT * FROM {main_table} 
                    WHERE {lat_col} IS NOT NULL 
                    AND {lon_col} IS NOT NULL
                    AND {lat_col} != 0 
                    AND {lon_col} != 0
                    ORDER BY rowid DESC
                    LIMIT 10
                """)
                
                examples = cursor.fetchall()
                print(f"\n🔍 EJEMPLOS DE EVENTOS CON COORDENADAS:")
                
                for i, example in enumerate(examples[:5]):
                    print(f"\n📍 EVENTO {i+1}:")
                    for j, col in enumerate(columns):
                        if example[j] is not None and str(example[j]).strip():
                            print(f"   {col[1]}: {example[j]}")
                
                # Buscar eventos relacionados con conflictos
                conflict_keywords = ['war', 'conflict', 'battle', 'attack', 'violence', 'military', 'terror', 'bomb', 'shoot', 'kill']
                
                for keyword in conflict_keywords:
                    # Buscar en todas las columnas de texto
                    text_columns = [col[1] for col in columns if col[2].upper() in ['TEXT', 'VARCHAR', 'CHAR']]
                    
                    if text_columns:
                        where_conditions = []
                        for text_col in text_columns:
                            where_conditions.append(f"{text_col} LIKE '%{keyword}%'")
                        
                        where_clause = " OR ".join(where_conditions)
                        
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM {main_table} 
                            WHERE ({where_clause})
                            AND {lat_col} IS NOT NULL 
                            AND {lon_col} IS NOT NULL
                            AND {lat_col} != 0 
                            AND {lon_col} != 0
                        """)
                        
                        conflict_count = cursor.fetchone()[0]
                        if conflict_count > 0:
                            print(f"\n⚔️ EVENTOS DE '{keyword.upper()}' CON COORDENADAS: {conflict_count}")
                            
                            # Obtener ejemplos
                            cursor.execute(f"""
                                SELECT {lat_col}, {lon_col}, * FROM {main_table} 
                                WHERE ({where_clause})
                                AND {lat_col} IS NOT NULL 
                                AND {lon_col} IS NOT NULL
                                AND {lat_col} != 0 
                                AND {lon_col} != 0
                                ORDER BY rowid DESC
                                LIMIT 3
                            """)
                            
                            conflict_examples = cursor.fetchall()
                            for ex in conflict_examples:
                                print(f"   📍 Lat: {ex[0]}, Lon: {ex[1]}")
                                # Mostrar información relevante
                                for j, col in enumerate(columns):
                                    if j < len(ex) and ex[j] is not None and str(ex[j]).strip():
                                        if any(kw in str(ex[j]).lower() for kw in conflict_keywords):
                                            print(f"      {col[1]}: {ex[j]}")
                            break  # Solo mostrar el primer tipo de conflicto encontrado
        
        # Verificar eventos recientes (últimos 30 días)
        cursor.execute(f"SELECT COUNT(*) FROM {main_table} WHERE date > date('now', '-30 days')")
        recent = cursor.fetchone()[0]
        print(f"\n📅 EVENTOS ÚLTIMOS 30 DÍAS: {recent}")
        
        # Verificar países/regiones más activas
        country_cols = [col for col in location_columns if 'country' in col.lower() or 'nation' in col.lower()]
        if country_cols:
            country_col = country_cols[0]
            cursor.execute(f"""
                SELECT {country_col}, COUNT(*) as eventos 
                FROM {main_table} 
                WHERE {country_col} IS NOT NULL
                GROUP BY {country_col}
                ORDER BY eventos DESC
                LIMIT 10
            """)
            
            top_countries = cursor.fetchall()
            print(f"\n🌍 PAÍSES/REGIONES MÁS ACTIVOS:")
            for country, count in top_countries:
                print(f"   {country}: {count} eventos")
        
        conn.close()
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_gdelt_locations()
