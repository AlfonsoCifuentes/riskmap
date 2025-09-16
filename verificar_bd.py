#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la estructura de la base de datos
"""

import sqlite3
import os

def check_database_structure():
    db_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    print(f"✅ Base de datos encontrada: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📊 Tablas encontradas ({len(tables)}):")
        for table in tables:
            table_name = table[0]
            print(f"\n🗂️  Tabla: {table_name}")
            
            # Obtener estructura de cada tabla
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"   Columnas ({len(columns)}):")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, primary_key = col
                pk_marker = " (PK)" if primary_key else ""
                null_marker = " NOT NULL" if not_null else ""
                print(f"     - {col_name}: {col_type}{null_marker}{pk_marker}")
            
            # Obtener conteo de registros
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   📈 Registros: {count}")
            except Exception as e:
                print(f"   ⚠️ Error contando registros: {e}")
        
        # Buscar tablas que contengan artículos/noticias
        print(f"\n🔍 Buscando tablas con contenido de artículos...")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1].lower() for col in columns]
            
            # Buscar columnas típicas de artículos
            has_title = any('title' in col or 'titulo' in col for col in column_names)
            has_content = any('content' in col or 'texto' in col or 'body' in col or 'descripcion' in col for col in column_names)
            has_url = any('url' in col or 'link' in col for col in column_names)
            
            if has_title or has_content or has_url:
                print(f"\n🎯 Tabla candidata: {table_name}")
                print(f"   - Tiene título: {'✅' if has_title else '❌'}")
                print(f"   - Tiene contenido: {'✅' if has_content else '❌'}")
                print(f"   - Tiene URL: {'✅' if has_url else '❌'}")
                
                # Mostrar algunas columnas relevantes
                relevant_columns = [col for col in column_names if any(keyword in col for keyword in 
                    ['title', 'titulo', 'content', 'texto', 'body', 'descripcion', 'url', 'link', 'summary', 'resumen'])]
                if relevant_columns:
                    print(f"   - Columnas relevantes: {', '.join(relevant_columns)}")
                
                # Mostrar un registro de ejemplo
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                    sample = cursor.fetchone()
                    if sample:
                        print(f"   - Registro de ejemplo encontrado (primeras 3 columnas): {sample[:3]}")
                except Exception as e:
                    print(f"   ⚠️ Error obteniendo ejemplo: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database_structure()
