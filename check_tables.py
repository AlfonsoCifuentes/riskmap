#!/usr/bin/env python3
"""
Script para verificar las tablas en la base de datos
"""

import sqlite3

def check_tables():
    try:
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("Tablas disponibles:")
        for table in tables:
            print(f"  - {table[0]}")
            
        # Si hay tablas, verificar estructura de la primera
        if tables:
            table_name = tables[0][0]
            print(f"\nEstructura de la tabla '{table_name}':")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
                
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tables()
