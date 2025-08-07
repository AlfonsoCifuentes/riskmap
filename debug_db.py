#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para debuggear la base de datos
"""

import sqlite3
import os
from src.utils.config import get_database_path

def main():
    try:
        db_path = get_database_path()
        print(f"Ruta de la base de datos: {db_path}")
        print(f"Base de datos existe: {os.path.exists(db_path)}")
        
        if not os.path.exists(db_path):
            print("❌ La base de datos no existe!")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla articles existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        table_exists = cursor.fetchone()
        print(f"Tabla 'articles' existe: {table_exists is not None}")
        
        if table_exists:
            # Contar artículos
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            print(f"Total de artículos: {total_articles}")
            
            # Verificar estructura de la tabla
            cursor.execute("PRAGMA table_info(articles)")
            columns = cursor.fetchall()
            print("\nColumnas de la tabla 'articles':")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Obtener algunos artículos de ejemplo
            cursor.execute("SELECT id, title, country, region, risk_level FROM articles WHERE title IS NOT NULL LIMIT 5")
            sample_articles = cursor.fetchall()
            print(f"\nPrimeros 5 artículos:")
            for article in sample_articles:
                print(f"  ID: {article[0]}, Título: {article[1][:50]}..., País: {article[2]}, Región: {article[3]}, Riesgo: {article[4]}")
            
            # Verificar filtros de geopolítica
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE (is_excluded IS NULL OR is_excluded != 1)
                AND risk_level IS NOT NULL
                AND country IS NOT NULL
            """)
            filtered_count = cursor.fetchone()[0]
            print(f"\nArtículos que cumplen filtros geopolíticos: {filtered_count}")
            
            # Verificar artículos de alto riesgo
            cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level = 'high'")
            high_risk_count = cursor.fetchone()[0]
            print(f"Artículos de alto riesgo: {high_risk_count}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
