#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar estructura de la tabla articles
"""

import sqlite3

def check_table_structure():
    """Verificar las columnas de la tabla articles"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Obtener información de la tabla
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        
        print("📊 Estructura de la tabla 'articles':")
        print("ID | Nombre | Tipo | NotNull | Default | PK")
        print("-" * 50)
        for col in columns:
            print(f"{col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]} | {col[5]}")
        
        print(f"\n✅ Total columnas: {len(columns)}")
        
        # También verificar algunos datos
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        print(f"📈 Total filas: {total}")
        
        # Verificar columnas de fecha disponibles
        date_columns = [col[1] for col in columns if 'date' in col[1].lower() or 'time' in col[1].lower()]
        print(f"📅 Columnas de fecha encontradas: {date_columns}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_table_structure()