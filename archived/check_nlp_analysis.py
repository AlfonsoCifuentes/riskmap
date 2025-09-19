#!/usr/bin/env python3
"""
Script para verificar el estado del análisis NLP y filtrado geopolítico
"""

import sqlite3
import os
import json
from collections import Counter

def check_risk_analysis():
    """Verificar el estado del análisis de riesgo en la base de datos"""
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    print("🔍 ANÁLISIS DEL ESTADO DE LA BASE DE DATOS")
    print("=" * 60)
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Verificar estructura de la tabla articles
        print("📊 ESTRUCTURA DE LA TABLA ARTICLES:")
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col['name']}: {col['type']}")
        print()
        
        # 2. Analizar distribución de niveles de riesgo
        print("⚖️ DISTRIBUCIÓN DE NIVELES DE RIESGO:")
        cursor.execute("SELECT risk_level, COUNT(*) as count FROM articles GROUP BY risk_level")
        risk_levels = cursor.fetchall()
        for level in risk_levels:
            print(f"   - {level['risk_level'] or 'NULL'}: {level['count']} artículos")
        print()
        
        # 3. Analizar puntuaciones de riesgo
        print("📈 DISTRIBUCIÓN DE PUNTUACIONES DE RIESGO:")
        cursor.execute("SELECT risk_score, COUNT(*) as count FROM articles GROUP BY risk_score ORDER BY risk_score")
        risk_scores = cursor.fetchall()
        for score in risk_scores[:10]:  # Solo primeros 10
            print(f"   - {score['risk_score'] or 'NULL'}: {score['count']} artículos")
        if len(risk_scores) > 10:
            print(f"   ... y {len(risk_scores) - 10} valores más")
        print()
        
        # 4. Verificar filtrado geopolítico - buscar artículos de deportes
        print("🏈 VERIFICANDO FILTRADO GEOPOLÍTICO (buscando deportes):")
        cursor.execute("""
            SELECT id, title, category, content, risk_level, risk_score 
            FROM articles 
            WHERE (LOWER(title) LIKE '%deporte%' 
                   OR LOWER(title) LIKE '%football%' 
                   OR LOWER(title) LIKE '%basketball%'
                   OR LOWER(title) LIKE '%soccer%'
                   OR LOWER(title) LIKE '%tennis%'
                   OR LOWER(title) LIKE '%golf%'
                   OR LOWER(content) LIKE '%deporte%'
                   OR category LIKE '%sport%')
            LIMIT 5
        """)
        sports_articles = cursor.fetchall()
        
        if sports_articles:
            print(f"   ❌ ENCONTRADOS {len(sports_articles)} ARTÍCULOS DE DEPORTES:")
            for article in sports_articles:
                print(f"   - ID: {article['id']}")
                print(f"     Título: {article['title'][:80]}...")
                print(f"     Risk: {article['risk_level']} ({article['risk_score']})")
                print()
        else:
            print("   ✅ No se encontraron artículos de deportes")
        print()
        
        # 5. Verificar procesamiento NLP - buscar artículos sin procesar
        print("🧠 VERIFICANDO ESTADO DEL PROCESAMIENTO NLP:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN risk_level IS NULL THEN 1 ELSE 0 END) as sin_risk_level,
                SUM(CASE WHEN risk_score IS NULL OR risk_score = 0 THEN 1 ELSE 0 END) as sin_risk_score,
                SUM(CASE WHEN sentiment_score IS NULL THEN 1 ELSE 0 END) as sin_sentiment,
                SUM(CASE WHEN category IS NULL OR category = '' THEN 1 ELSE 0 END) as sin_categoria
            FROM articles
        """)
        nlp_stats = cursor.fetchone()
        
        print(f"   - Total artículos: {nlp_stats['total']}")
        print(f"   - Sin risk_level: {nlp_stats['sin_risk_level']}")
        print(f"   - Sin risk_score: {nlp_stats['sin_risk_score']}")
        print(f"   - Sin sentiment: {nlp_stats['sin_sentiment']}")
        print(f"   - Sin categoría: {nlp_stats['sin_categoria']}")
        print()
        
        # 6. Verificar coordenadas para el mapa
        print("🗺️ VERIFICANDO COORDENADAS PARA EL MAPA:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as con_coordenadas,
                SUM(CASE WHEN country IS NOT NULL AND country != '' THEN 1 ELSE 0 END) as con_pais
            FROM articles
        """)
        coords_stats = cursor.fetchone()
        
        print(f"   - Total artículos: {coords_stats['total']}")
        print(f"   - Con coordenadas: {coords_stats['con_coordenadas']}")
        print(f"   - Con país: {coords_stats['con_pais']}")
        
        # Mostrar algunos ejemplos de coordenadas
        cursor.execute("SELECT title, country, latitude, longitude FROM articles WHERE latitude IS NOT NULL LIMIT 5")
        coord_examples = cursor.fetchall()
        print(f"   - Ejemplos de coordenadas:")
        for example in coord_examples:
            print(f"     • {example['title'][:50]}... → {example['country']} ({example['latitude']}, {example['longitude']})")
        print()
        
        # 7. Buscar zonas de conflicto
        print("⚔️ VERIFICANDO ZONAS DE CONFLICTO:")
        cursor.execute("""
            SELECT country, COUNT(*) as conflictos, AVG(risk_score) as riesgo_promedio
            FROM articles 
            WHERE risk_level = 'high' OR risk_score > 0.7
            GROUP BY country 
            ORDER BY conflictos DESC 
            LIMIT 10
        """)
        conflict_zones = cursor.fetchall()
        
        if conflict_zones:
            print("   🎯 TOP ZONAS DE CONFLICTO:")
            for zone in conflict_zones:
                print(f"   - {zone['country'] or 'Sin país'}: {zone['conflictos']} conflictos (riesgo: {zone['riesgo_promedio']:.2f})")
        else:
            print("   ❌ No se encontraron zonas de conflicto de alto riesgo")

if __name__ == "__main__":
    check_risk_analysis()
