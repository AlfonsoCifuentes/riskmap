#!/usr/bin/env python3
"""Script para verificar el esquema de la base de datos"""

import sqlite3

def check_database_schema():
    try:
        db = sqlite3.connect('data/geopolitical_intel.db')
        cursor = db.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("📊 TABLAS EN LA BASE DE DATOS:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verificar esquema de cada tabla relevante
        for table_name in ['articles', 'news_articles', 'processed_articles']:
            try:
                cursor.execute(f"PRAGMA table_info({table_name});")
                schema = cursor.fetchall()
                if schema:
                    print(f"\n🔍 ESQUEMA DE {table_name.upper()}:")
                    for column in schema:
                        print(f"  - {column[1]} ({column[2]})")
            except Exception as e:
                print(f"\n❌ Tabla {table_name} no existe")
        
        db.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database_schema()
