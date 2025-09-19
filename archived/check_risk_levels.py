#!/usr/bin/env python3
"""
Verificar el estado del nivel de riesgo geopolítico en los artículos
"""

import sqlite3
from pathlib import Path

def check_risk_levels():
    """Verificar niveles de riesgo geopolítico"""
    
    db_path = Path('data/geopolitical_intel.db')
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🎯 ANÁLISIS DE NIVELES DE RIESGO GEOPOLÍTICO")
    print("=" * 60)
    
    # Total de artículos
    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]
    print(f"📰 Total de artículos: {total_articles}")
    
    # Artículos con risk_level asignado
    cursor.execute('SELECT COUNT(*) FROM articles WHERE risk_level IS NOT NULL AND risk_level != ""')
    with_risk = cursor.fetchone()[0]
    print(f"⚠️ Con nivel de riesgo: {with_risk}/{total_articles} ({with_risk/total_articles*100:.1f}%)")
    
    # Distribución de niveles de riesgo
    print("\n📊 DISTRIBUCIÓN DE NIVELES DE RIESGO:")
    print("-" * 40)
    
    risk_levels = ['low', 'medium', 'high']
    for level in risk_levels:
        cursor.execute('SELECT COUNT(*) FROM articles WHERE risk_level = ?', (level,))
        count = cursor.fetchone()[0]
        percentage = (count / total_articles * 100) if total_articles > 0 else 0
        print(f"🔶 {level.capitalize()}: {count} ({percentage:.1f}%)")
    
    # Artículos sin nivel de riesgo
    cursor.execute('SELECT COUNT(*) FROM articles WHERE risk_level IS NULL OR risk_level = ""')
    no_risk = cursor.fetchone()[0]
    print(f"❌ Sin nivel de riesgo: {no_risk} ({no_risk/total_articles*100:.1f}%)")
    
    # Artículos con relevancia geopolítica pero sin risk_level
    cursor.execute('''
        SELECT COUNT(*) FROM articles 
        WHERE (risk_level IS NULL OR risk_level = "") 
        AND (geopolitical_relevance > 5 OR 
             title LIKE '%war%' OR title LIKE '%conflict%' OR 
             title LIKE '%military%' OR title LIKE '%sanction%' OR
             title LIKE '%ukraine%' OR title LIKE '%russia%' OR
             title LIKE '%china%' OR title LIKE '%iran%')
    ''')
    potential_high_risk = cursor.fetchone()[0]
    print(f"🚨 Potencialmente importantes sin riesgo: {potential_high_risk}")
    
    # Los 150 artículos más recientes con riesgo medio/alto
    print(f"\n📅 ANÁLISIS DE LOS 150 ARTÍCULOS MÁS RECIENTES:")
    print("-" * 40)
    
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE risk_level IN ('medium', 'high')
    ''')
    recent_medium_high = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE risk_level IS NOT NULL AND risk_level != ""
    ''')
    recent_with_risk = cursor.fetchone()[0]
    
    print(f"⚠️ Con nivel de riesgo: {recent_with_risk}/150 ({recent_with_risk/150*100:.1f}%)")
    print(f"🔴 Riesgo medio/alto: {recent_medium_high}/150 ({recent_medium_high/150*100:.1f}%)")
    
    # Muestra de artículos recientes sin risk_level
    print(f"\n📋 ARTÍCULOS RECIENTES SIN NIVEL DE RIESGO:")
    print("-" * 40)
    
    cursor.execute('''
        SELECT id, title, geopolitical_relevance 
        FROM articles 
        WHERE risk_level IS NULL OR risk_level = ""
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    
    for row in cursor.fetchall():
        article_id, title, geo_relevance = row
        geo_score = geo_relevance if geo_relevance else 0
        print(f"ID {article_id}: {title[:50]}... (geo: {geo_score})")
    
    # Campos relacionados con análisis NLP/BERT
    print(f"\n🧠 ANÁLISIS NLP/BERT:")
    print("-" * 40)
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE groq_enhanced = 1')
    groq_enhanced = cursor.fetchone()[0]
    print(f"🤖 Procesados con Groq/LLM: {groq_enhanced}/{total_articles} ({groq_enhanced/total_articles*100:.1f}%)")
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE extracted_entities_json IS NOT NULL AND extracted_entities_json != ""')
    with_entities = cursor.fetchone()[0]
    print(f"🔍 Con entidades extraídas: {with_entities}/{total_articles} ({with_entities/total_articles*100:.1f}%)")
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE key_persons IS NOT NULL AND key_persons != "" AND key_persons != "[]"')
    with_persons = cursor.fetchone()[0]
    print(f"👥 Con personas clave: {with_persons}/{total_articles} ({with_persons/total_articles*100:.1f}%)")
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE key_locations IS NOT NULL AND key_locations != "" AND key_locations != "[]"')
    with_locations = cursor.fetchone()[0]
    print(f"📍 Con ubicaciones clave: {with_locations}/{total_articles} ({with_locations/total_articles*100:.1f}%)")
    
    conn.close()

if __name__ == '__main__':
    check_risk_levels()
