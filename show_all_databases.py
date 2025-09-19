#!/usr/bin/env python3
"""Mostrar todas las tablas de todas las bases de datos del proyecto."""

import sqlite3
import os
import glob
from pathlib import Path

def find_databases():
    """Buscar todas las bases de datos SQLite en el proyecto."""
    databases = []
    
    # Buscar archivos .db en el proyecto
    db_patterns = ['**/*.db', '**/*.sqlite', '**/*.sqlite3']
    
    for pattern in db_patterns:
        for db_path in glob.glob(pattern, recursive=True):
            if os.path.exists(db_path):
                databases.append(db_path)
    
    return databases

def analyze_database(db_path):
    """Analizar una base de datos y mostrar sus tablas."""
    print(f"\n{'='*80}")
    print(f"📁 BASE DE DATOS: {db_path}")
    print(f"{'='*80}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No hay tablas en esta base de datos")
            conn.close()
            return
        
        print(f"📊 TOTAL DE TABLAS: {len(tables)}")
        print("-" * 40)
        
        for (table_name,) in tables:
            print(f"\n🗂️  TABLA: {table_name}")
            
            # Obtener información de las columnas
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            print(f"   📈 Registros: {count:,}")
            print(f"   🏗️  Columnas ({len(columns)}):")
            
            for col in columns:
                col_id, col_name, col_type, not_null, default, primary_key = col
                pk_indicator = " (PK)" if primary_key else ""
                null_indicator = " NOT NULL" if not_null else ""
                default_info = f" DEFAULT {default}" if default else ""
                print(f"      • {col_name:<25} {col_type:<15}{pk_indicator}{null_indicator}{default_info}")
            
            # Mostrar algunos registros de ejemplo para tablas pequeñas
            if count > 0 and count <= 5:
                print(f"   📝 Datos de ejemplo:")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                for i, row in enumerate(rows, 1):
                    print(f"      Registro {i}: {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analizando {db_path}: {e}")

def main():
    print("🔍 ANÁLISIS COMPLETO DE BASES DE DATOS")
    print("=" * 80)
    
    # Buscar todas las bases de datos
    databases = find_databases()
    
    if not databases:
        print("❌ No se encontraron bases de datos en el proyecto")
        return
    
    print(f"📊 Se encontraron {len(databases)} bases de datos:")
    for db in databases:
        print(f"   • {db}")
    
    # Analizar cada base de datos
    for db_path in databases:
        analyze_database(db_path)
    
    print(f"\n{'='*80}")
    print("✅ ANÁLISIS COMPLETADO")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()