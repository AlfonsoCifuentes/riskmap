#!/usr/bin/env python3
"""
Script para verificar la estructura y contenido de la base de datos geopolitical_intel.db
"""

import sqlite3
import os
from pathlib import Path

def check_database():
    # Ruta correcta de la base de datos
    db_path = r"data\geopolitical_intel.db"
    
    print(f"🔍 Verificando base de datos en: {db_path}")
    print(f"📁 Ruta absoluta: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print(f"❌ La base de datos no existe en: {db_path}")
        
        # Buscar archivos .db en el directorio actual
        print("\n🔎 Buscando archivos .db en el directorio actual:")
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.db'):
                    full_path = os.path.join(root, file)
                    size = os.path.getsize(full_path)
                    print(f"  📄 {full_path} ({size} bytes)")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener lista de tablas
        print("\n📋 Tablas en la base de datos:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No se encontraron tablas en la base de datos")
            conn.close()
            return
        
        for table in tables:
            table_name = table[0]
            print(f"\n🗂️  Tabla: {table_name}")
            
            # Obtener esquema de la tabla
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("   Columnas:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = "NOT NULL" if col[3] else ""
                primary_key = "PRIMARY KEY" if col[5] else ""
                print(f"     - {col_name} ({col_type}) {not_null} {primary_key}")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   📊 Registros: {count}")
            
            # Si es la tabla articles, mostrar algunos ejemplos
            if table_name == 'articles' and count > 0:
                print("\n   📄 Primeros 3 artículos:")
                cursor.execute("""
                    SELECT id, title, source, country, risk_level, published_at 
                    FROM articles 
                    ORDER BY id 
                    LIMIT 3
                """)
                articles = cursor.fetchall()
                
                for article in articles:
                    print(f"     ID: {article[0]}")
                    print(f"     Título: {article[1][:80]}{'...' if len(str(article[1])) > 80 else ''}")
                    print(f"     Fuente: {article[2]}")
                    print(f"     País: {article[3]}")
                    print(f"     Riesgo: {article[4]}")
                    print(f"     Fecha: {article[5]}")
                    print("     ---")
        
        conn.close()
        print("\n✅ Verificación completada")
        
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")

if __name__ == "__main__":
    check_database()
