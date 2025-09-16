#!/usr/bin/env python3
"""
Script para verificar la estructura de la base de datos y diagnosticar errores
"""
import sqlite3
import os

def check_db_structure():
    """Verifica la estructura de la base de datos"""
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada:", db_path)
        return
    
    print("📊 VERIFICANDO ESTRUCTURA DE LA BASE DE DATOS")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar tabla articles
    cursor.execute("PRAGMA table_info(articles)")
    columns = cursor.fetchall()
    
    print("🗂️  COLUMNAS EN LA TABLA 'articles':")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Contar artículos
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]
    print(f"\n📰 Total de artículos: {total:,}")
    
    # Verificar columnas específicas que causan problemas
    column_names = [col[1] for col in columns]
    
    problematic_columns = ['description', 'summary', 'content']
    print(f"\n🔍 VERIFICANDO COLUMNAS PROBLEMÁTICAS:")
    for col in problematic_columns:
        if col in column_names:
            print(f"   ✅ '{col}' existe")
        else:
            print(f"   ❌ '{col}' NO existe")
    
    # Verificar algunas consultas problemáticas
    print(f"\n🧪 PROBANDO CONSULTAS:")
    
    # Test 1: Consulta básica
    try:
        cursor.execute("SELECT id, title, url, source, created_at FROM articles LIMIT 3")
        results = cursor.fetchall()
        print(f"   ✅ Consulta básica: {len(results)} resultados")
    except Exception as e:
        print(f"   ❌ Error en consulta básica: {e}")
    
    # Test 2: Consulta con image_url
    try:
        cursor.execute("SELECT id, title, image_url FROM articles WHERE image_url IS NOT NULL LIMIT 3")
        results = cursor.fetchall()
        print(f"   ✅ Consulta con image_url: {len(results)} resultados")
    except Exception as e:
        print(f"   ❌ Error en consulta image_url: {e}")
    
    # Test 3: Consulta con description (problemática)
    try:
        cursor.execute("SELECT id, title, description FROM articles LIMIT 3")
        results = cursor.fetchall()
        print(f"   ✅ Consulta con description: {len(results)} resultados")
    except Exception as e:
        print(f"   ❌ Error en consulta description: {e}")
    
    # Test 4: Consulta geopolítica
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%politics%'
        """)
        geo_count = cursor.fetchone()[0]
        print(f"   ✅ Artículos geopolíticos: {geo_count}")
    except Exception as e:
        print(f"   ❌ Error en consulta geopolítica: {e}")
    
    conn.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_db_structure()