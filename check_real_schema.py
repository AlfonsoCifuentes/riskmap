#!/usr/bin/env python3
"""
Verificar estructura real de la base de datos
"""

import sqlite3
import os

def check_real_schema():
    """Verificar esquema real"""
    print("🔍 VERIFICANDO ESQUEMA REAL DE LA BASE DE DATOS")
    print("=" * 60)
    
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📋 TABLAS EN LA BASE DE DATOS:")
        for table in tables:
            print(f"• {table[0]}")
        
        # Esquema de articles
        print("\n🔧 ESQUEMA DE LA TABLA ARTICLES:")
        print("-" * 40)
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"• {col[1]} ({col[2]})")
        
        # Ejemplo de artículos
        print("\n📰 EJEMPLOS DE ARTÍCULOS:")
        print("-" * 40)
        cursor.execute("SELECT * FROM articles LIMIT 3")
        rows = cursor.fetchall()
        
        if rows:
            # Mostrar las columnas para el primer artículo
            column_names = [desc[0] for desc in cursor.description]
            print(f"Columnas encontradas: {column_names}")
            
            for i, row in enumerate(rows, 1):
                print(f"\nArtículo {i}:")
                for j, value in enumerate(row):
                    if value is not None and str(value).strip():
                        print(f"  {column_names[j]}: {str(value)[:100]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def create_fixed_diagnostic_app():
    """Crear app diagnóstica con las columnas correctas"""
    print("\n🛠️ CREANDO APP DIAGNÓSTICA CORREGIDA")
    print("-" * 40)
    
    # Primero verificamos qué columnas existen realmente
    db_path = "./data/geopolitical_intel.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]
    
    conn.close()
    
    print(f"Columnas disponibles: {columns}")
    
    # Determinar qué columnas usar
    date_column = None
    if 'pub_date' in columns:
        date_column = 'pub_date'
    elif 'published_date' in columns:
        date_column = 'published_date'
    elif 'date' in columns:
        date_column = 'date'
    elif 'created_at' in columns:
        date_column = 'created_at'
    elif 'timestamp' in columns:
        date_column = 'timestamp'
    
    image_column = None
    if 'image_url' in columns:
        image_column = 'image_url'
    elif 'image' in columns:
        image_column = 'image'
    elif 'thumbnail' in columns:
        image_column = 'thumbnail'
    
    print(f"Usando columna de fecha: {date_column}")
    print(f"Usando columna de imagen: {image_column}")
    
    return date_column, image_column, columns

if __name__ == "__main__":
    check_real_schema()
    create_fixed_diagnostic_app()