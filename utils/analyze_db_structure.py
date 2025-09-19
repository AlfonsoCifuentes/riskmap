#!/usr/bin/env python3
"""
Análisis completo de la estructura de la base de datos
"""
import sqlite3
import json
import os
from pathlib import Path

def analyze_database_structure():
    """Analizar la estructura actual de la base de datos"""
    db_path = './data/geopolitical_intel.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print('🔍 ANÁLISIS DE ESTRUCTURA ACTUAL DE BASE DE DATOS')
        print('=' * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f'📊 Total de tablas encontradas: {len(tables)}')
        print()
        
        for table in tables:
            table_name = table[0]
            print(f'📋 TABLA: {table_name}')
            
            # Get table schema
            cursor.execute(f'PRAGMA table_info({table_name});')
            columns = cursor.fetchall()
            
            print('   Columnas:')
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = 'NOT NULL' if col[3] else ''
                default = f'DEFAULT {col[4]}' if col[4] else ''
                pk = 'PRIMARY KEY' if col[5] else ''
                print(f'     • {col_name} ({col_type}) {not_null} {default} {pk}')
            
            # Get row count
            cursor.execute(f'SELECT COUNT(*) FROM {table_name};')
            count = cursor.fetchone()[0]
            print(f'   📊 Registros: {count}')
            
            # If it's articles table, show sample data structure (not content)
            if 'article' in table_name.lower() and count > 0:
                print('   🔍 Muestra de estructura de datos:')
                cursor.execute(f'SELECT * FROM {table_name} LIMIT 1;')
                sample = cursor.fetchone()
                if sample:
                    for i, col in enumerate(columns):
                        col_name = col[1]
                        value = sample[i] if sample[i] else 'NULL'
                        # Truncate long values
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + '...'
                        print(f'     {col_name}: {type(value).__name__} - {value}')
            
            print()
        
        # Análisis específico para artículos
        print('🔍 ANÁLISIS ESPECÍFICO DE ARTÍCULOS:')
        print('-' * 40)
        
        article_tables = [t[0] for t in tables if 'article' in t[0].lower()]
        
        for table_name in article_tables:
            print(f'📰 Tabla: {table_name}')
            
            # Get columns
            cursor.execute(f'PRAGMA table_info({table_name});')
            cols = [col[1] for col in cursor.fetchall()]
            
            # Check for key fields
            fields_check = {
                'imagen': any('image' in col.lower() or 'img' in col.lower() for col in cols),
                'ubicacion': any('location' in col.lower() or 'country' in col.lower() or 'region' in col.lower() for col in cols),
                'riesgo': any('risk' in col.lower() for col in cols),
                'nlp': any('nlp' in col.lower() or 'sentiment' in col.lower() for col in cols),
                'titulo': any('title' in col.lower() for col in cols),
                'contenido': any('content' in col.lower() or 'text' in col.lower() for col in cols),
                'fecha': any('date' in col.lower() or 'published' in col.lower() for col in cols),
                'fuente': any('source' in col.lower() or 'url' in col.lower() for col in cols)
            }
            
            print('   ✅ Campos presentes:')
            for field, present in fields_check.items():
                status = '✓' if present else '✗'
                print(f'     {status} {field.capitalize()}')
            
            print(f'   📊 Total columnas: {len(cols)}')
            print()
        
        # Check for processed_data table
        processed_tables = [t[0] for t in tables if 'processed' in t[0].lower()]
        if processed_tables:
            print('🧠 TABLAS DE PROCESAMIENTO NLP:')
            for table_name in processed_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name};')
                count = cursor.fetchone()[0]
                print(f'   📋 {table_name}: {count} registros')
        
        conn.close()
        print('✅ Análisis completado exitosamente')
        
    except Exception as e:
        print(f'❌ Error analizando BD: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_database_structure()