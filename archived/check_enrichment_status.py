#!/usr/bin/env python3
"""
Script para verificar el estado del enriquecimiento de datos
"""

import sqlite3
from pathlib import Path

def check_enrichment_status():
    db_path = Path('data/geopolitical_intel.db')
    if not db_path.exists():
        print('❌ Database not found')
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Verificar estructura de tabla
    cursor.execute('PRAGMA table_info(articles)')
    columns = [col[1] for col in cursor.fetchall()]
    print('✅ Columns in articles table:')
    for col in columns:
        print(f'  - {col}')
    
    print('\n' + '='*60)
    
    # Total de artículos
    cursor.execute('SELECT COUNT(*) FROM articles')
    total = cursor.fetchone()[0]
    print(f'📊 Total articles: {total}')
    
    # Verificar campos de análisis NLP
    nlp_fields = ['sentiment_score', 'key_persons', 'key_locations', 'extracted_entities_json', 'summary']
    
    print('\n🧠 NLP Analysis Status:')
    for field in nlp_fields:
        if field in columns:
            cursor.execute(f'SELECT COUNT(*) FROM articles WHERE {field} IS NOT NULL AND {field} != ""')
            count = cursor.fetchone()[0]
            percentage = (count / total * 100) if total > 0 else 0
            print(f'  - {field}: {count}/{total} ({percentage:.1f}%)')
        else:
            print(f'  - {field}: ❌ Column not found')
    
    # Verificar campos de imagen
    image_fields = ['image_url', 'detected_objects', 'visual_analysis_json', 'has_faces']
    
    print('\n🖼️ Image Analysis Status:')
    for field in image_fields:
        if field in columns:
            cursor.execute(f'SELECT COUNT(*) FROM articles WHERE {field} IS NOT NULL AND {field} != ""')
            count = cursor.fetchone()[0]
            percentage = (count / total * 100) if total > 0 else 0
            print(f'  - {field}: {count}/{total} ({percentage:.1f}%)')
        else:
            print(f'  - {field}: ❌ Column not found')
    
    # Verificar ejemplos de image_url
    print('\n🔍 Sample image_urls:')
    cursor.execute('SELECT id, title, image_url FROM articles WHERE image_url IS NOT NULL AND image_url != "" LIMIT 5')
    examples = cursor.fetchall()
    for ex in examples:
        print(f'  - ID {ex[0]}: {ex[1][:50]}... -> {ex[2]}')
    
    # Verificar artículos enriched
    if 'groq_enhanced' in columns:
        cursor.execute('SELECT COUNT(*) FROM articles WHERE groq_enhanced = 1')
        enriched = cursor.fetchone()[0]
        percentage = (enriched / total * 100) if total > 0 else 0
        print(f'\n✨ Groq enhanced: {enriched}/{total} ({percentage:.1f}%)')
    
    # Verificar artículos recientes sin enrichment
    cursor.execute('''
        SELECT COUNT(*) FROM articles 
        WHERE (groq_enhanced IS NULL OR groq_enhanced = 0)
        AND datetime(created_at) > datetime('now', '-24 hours')
    ''')
    recent_unprocessed = cursor.fetchone()[0]
    print(f'⏰ Recent unprocessed (24h): {recent_unprocessed}')
    
    conn.close()

if __name__ == '__main__':
    check_enrichment_status()
