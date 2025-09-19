#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos y mostrar datos de ejemplo
"""
import sqlite3
import os
from pathlib import Path

def test_database_connection():
    """Probar conexión a la base de datos y mostrar información"""
    
    # Ruta de la base de datos
    db_path = r"data\geopolitical_intel.db"
    
    print(f"🔍 Verificando base de datos en: {db_path}")
    print(f"📁 Ruta absoluta: {os.path.abspath(db_path)}")
    print(f"✅ Existe el archivo: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("❌ La base de datos no existe!")
        return False
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📊 Tablas encontradas: {[table[0] for table in tables]}")
        
        # Verificar si existe la tabla articles
        if ('articles',) in tables:
            print("✅ Tabla 'articles' encontrada")
            
            # Contar artículos
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            print(f"📰 Total de artículos: {count}")
            
            # Mostrar algunos ejemplos
            if count > 0:
                cursor.execute("""
                    SELECT id, title, country, region, risk_level, published_at
                    FROM articles 
                    ORDER BY published_at DESC 
                    LIMIT 5
                """)
                articles = cursor.fetchall()
                
                print("\n📋 Últimos 5 artículos:")
                for article in articles:
                    id_art, title, country, region, risk_level, published_at = article
                    print(f"  • ID: {id_art}")
                    print(f"    Título: {title[:80]}..." if len(str(title)) > 80 else f"    Título: {title}")
                    print(f"    País: {country}, Región: {region}")
                    print(f"    Riesgo: {risk_level}, Fecha: {published_at}")
                    print()
            
            # Verificar estructura de la tabla
            cursor.execute("PRAGMA table_info(articles)")
            columns = cursor.fetchall()
            print("🏗️  Estructura de la tabla 'articles':")
            for col in columns:
                print(f"  • {col[1]} ({col[2]})")
        
        else:
            print("❌ Tabla 'articles' no encontrada")
        
        conn.close()
        print("\n✅ Conexión a la base de datos exitosa!")
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando prueba de conexión a la base de datos...")
    test_database_connection()
