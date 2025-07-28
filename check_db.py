#!/usr/bin/env python3
"""
Script para verificar el contenido de la base de datos
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "geopolitical_intel.db"

try:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Verificar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print("📊 Tablas en la base de datos:")
    for table in tables:
        print(f"   - {table}")
    
    print("\n📈 Conteo de registros:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} registros")
        except Exception as e:
            print(f"   - {table}: Error - {e}")
    
    # Verificar algunos eventos recientes
    print("\n🔍 Eventos recientes (últimos 5):")
    try:
        cursor.execute("""
            SELECT title, published_at, source, type 
            FROM events 
            ORDER BY published_at DESC 
            LIMIT 5
        """)
        events = cursor.fetchall()
        for event in events:
            print(f"   - {event[0][:50]}... ({event[1]}, {event[2]})")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Verificar artículos
    print("\n📰 Artículos recientes (últimos 5):")
    try:
        cursor.execute("""
            SELECT title, created_at, country, risk_level 
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        articles = cursor.fetchall()
        for article in articles:
            print(f"   - {article[0][:50]}... ({article[1]}, {article[2]}, {article[3]})")
    except Exception as e:
        print(f"   Error: {e}")
    
    conn.close()
    print(f"\n✅ Base de datos verificada: {DB_PATH}")
    
except Exception as e:
    print(f"❌ Error al verificar la base de datos: {e}")