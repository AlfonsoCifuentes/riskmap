#!/usr/bin/env python3
"""
Script para verificar las estructuras de tablas satelitales
"""

import sqlite3

def main():
    print("=" * 60)
    print("VERIFICACIÓN DE TABLAS SATELITALES")
    print("=" * 60)
    
    conn = sqlite3.connect('./data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Listar todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    print("=== TODAS LAS TABLAS EN LA BASE DE DATOS ===")
    for table in sorted(all_tables):
        print(f"  • {table}")
    
    print("\n=== TABLAS RELACIONADAS CON SATÉLITES ===")
    satellite_tables = [t for t in all_tables if 'satellite' in t.lower()]
    
    if satellite_tables:
        for table in satellite_tables:
            print(f"\n--- ESTRUCTURA DE {table} ---")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[0]}: {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT: ' + str(col[4]) if col[4] else ''}")
            
            # Mostrar algunos registros de ejemplo
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  Total de registros: {count}")
            
            if count > 0:
                print("  Primeros 3 registros:")
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                for i, row in enumerate(rows):
                    print(f"    [{i+1}] {row}")
    else:
        print("  No se encontraron tablas con 'satellite' en el nombre")
    
    # Buscar otras tablas que podrían contener datos satelitales
    print("\n=== BUSCANDO OTRAS TABLAS POSIBLES ===")
    potential_tables = [t for t in all_tables if any(keyword in t.lower() for keyword in ['analysis', 'monitoring', 'zones', 'images'])]
    
    for table in potential_tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        column_names = [col[1].lower() for col in columns]
        
        # Verificar si tiene columnas relacionadas con coordenadas/satélites
        if any(keyword in ' '.join(column_names) for keyword in ['latitude', 'longitude', 'coordinates', 'satellite', 'image']):
            print(f"\n--- {table} (POSIBLE TABLA SATELITAL) ---")
            for col in columns:
                print(f"  {col[1]}: {col[2]}")
            
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  Total de registros: {count}")
    
    conn.close()

if __name__ == "__main__":
    main()
