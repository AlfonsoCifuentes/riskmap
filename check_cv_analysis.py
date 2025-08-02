#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el estado del análisis CV en la base de datos
"""

import sqlite3
import json
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_database_path():
    """Obtener la ruta de la base de datos desde variables de entorno"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/geopolitical_intel.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    return database_url

def check_cv_analysis():
    """Verificar el análisis CV en la base de datos"""
    try:
        db_path = get_database_path()
        print(f"🔗 Conectando a la base de datos: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Mostrar todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("🗃️ Tablas en la BD:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Verificar si existe la tabla articles o processed_data
        table_name = None
        for table in tables:
            if 'article' in table[0].lower() or 'processed' in table[0].lower():
                table_name = table[0]
                break
        
        if not table_name:
            print("❌ No se encontró tabla de artículos")
            return
        
        print(f"\n📊 Analizando tabla: {table_name}")
        
        # Verificar estructura de la tabla
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("📋 Columnas:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Verificar registros con análisis CV
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE cv_analysis IS NOT NULL AND cv_analysis != ''")
            count = cursor.fetchone()[0]
            print(f"\n✅ Registros con análisis CV: {count}")
            
            # Mostrar total de registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total = cursor.fetchone()[0]
            print(f"📈 Total de registros: {total}")
            
            if count > 0:
                # Mostrar algunos ejemplos
                cursor.execute(f"SELECT id, title, image_url, cv_analysis FROM {table_name} WHERE cv_analysis IS NOT NULL AND cv_analysis != '' LIMIT 3")
                print("\n🔍 Ejemplos de análisis CV:")
                for row in cursor.fetchall():
                    print(f"\n   ID: {row[0]}")
                    print(f"   Título: {row[1][:60]}...")
                    print(f"   URL imagen: {row[2][:80]}...")
                    if row[3]:
                        try:
                            cv_data = json.loads(row[3])
                            print(f"   Áreas de interés: {len(cv_data.get('interest_areas', []))}")
                            print(f"   Posición en mosaico: {cv_data.get('mosaic_position', 'N/A')}")
                        except:
                            print(f"   Análisis CV presente pero no es JSON válido")
                    print("   " + "-" * 50)
        except Exception as e:
            print(f"❌ Error al verificar cv_analysis: {e}")
            
    except Exception as e:
        print(f"❌ Error conectando a la BD: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_cv_analysis()
