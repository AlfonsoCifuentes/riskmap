#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Investigar qué campo contiene el contenido <think>
"""

import sqlite3

def investigate_think_content():
    """Investigar en qué campos está el contenido <think>"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Obtener un artículo específico para investigar
        cursor.execute("SELECT * FROM articles WHERE id = 312")
        article = cursor.fetchone()
        
        # Obtener nombres de columnas
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"🔍 Investigando artículo ID 312:")
        print(f"Total columnas: {len(column_names)}")
        
        # Buscar columnas que contengan <think>
        for i, value in enumerate(article):
            if value and isinstance(value, str) and '<think>' in value:
                col_name = column_names[i]
                content_preview = value[:200].replace('\n', ' ')
                print(f"\n❌ Columna '{col_name}' contiene <think>:")
                print(f"   Contenido: {content_preview}...")
                
                # Verificar si tiene </think> para cerrar
                if '</think>' in value:
                    think_end = value.find('</think>') + 8
                    after_think = value[think_end:think_end+100]
                    print(f"   Después de </think>: {after_think}...")
                else:
                    print(f"   ⚠️  NO tiene </think> de cierre")
        
        # Ver qué campos estamos usando en la query actual
        print(f"\n📊 Campos que usa nuestra query:")
        fields_in_query = ['summary', 'auto_generated_summary', 'content']
        
        for field in fields_in_query:
            if field in column_names:
                col_index = column_names.index(field)
                value = article[col_index]
                if value:
                    has_think = '<think>' in str(value)
                    has_close = '</think>' in str(value) if has_think else False
                    content_preview = str(value)[:100].replace('\n', ' ')
                    print(f"   {field}: {'❌ Tiene <think>' if has_think else '✅ Sin <think>'} {'+ cierre' if has_close else '- sin cierre' if has_think else ''}")
                    print(f"      Preview: {content_preview}...")
                else:
                    print(f"   {field}: ❌ NULL/vacío")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    investigate_think_content()