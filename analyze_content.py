#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizar qué campos tienen datos en la tabla articles
"""

import sqlite3

def analyze_content_fields():
    """Analizar qué campos de contenido tienen datos"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Campos de contenido a verificar
        content_fields = ['summary', 'content', 'ai_summary', 'auto_generated_summary']
        
        print("📊 Análisis de campos de contenido:")
        print("-" * 40)
        
        for field in content_fields:
            cursor.execute(f"SELECT COUNT(*) FROM articles WHERE {field} IS NOT NULL AND {field} != ''")
            count = cursor.fetchone()[0]
            print(f"  {field}: {count} artículos")
        
        print("\n🔍 Análisis de otros campos importantes:")
        other_fields = ['image_url', 'risk_score', 'ai_importance']
        
        for field in other_fields:
            cursor.execute(f"SELECT COUNT(*) FROM articles WHERE {field} IS NOT NULL AND {field} != ''")
            count = cursor.fetchone()[0]
            print(f"  {field}: {count} artículos")
        
        # Verificar si hay artículos con al menos content o ai_summary
        cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE (content IS NOT NULL AND content != '') 
        OR (ai_summary IS NOT NULL AND ai_summary != '')
        """)
        usable_articles = cursor.fetchone()[0]
        print(f"\n✅ Artículos con contenido usable: {usable_articles}")
        
        # Mostrar un ejemplo de artículo con datos
        cursor.execute("""
        SELECT id, title, 
               CASE WHEN content IS NOT NULL AND content != '' THEN 'content' ELSE 'none' END as has_content,
               CASE WHEN ai_summary IS NOT NULL AND ai_summary != '' THEN 'ai_summary' ELSE 'none' END as has_ai_summary,
               CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 'image' ELSE 'none' END as has_image,
               risk_score
        FROM articles 
        WHERE title IS NOT NULL AND title != ''
        LIMIT 5
        """)
        
        examples = cursor.fetchall()
        print(f"\n🎯 Primeros 5 artículos:")
        for ex in examples:
            print(f"  ID {ex[0]}: {ex[1][:50]}...")
            print(f"    Content: {ex[2]}, AI Summary: {ex[3]}, Image: {ex[4]}, Risk: {ex[5]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_content_fields()