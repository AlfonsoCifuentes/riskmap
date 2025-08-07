#!/usr/bin/env python3
"""
Script para verificar el estado del análisis NLP y problemas específicos
"""

import sqlite3
import os
import json
from collections import Counter

def check_database_issues():
    """Verificar problemas específicos en la base de datos"""
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    print("🔍 ANÁLISIS DE PROBLEMAS ESPECÍFICOS")
    print("=" * 60)
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Problema: Todos los artículos con risk_level "medium"
        print("⚖️ PROBLEMA 1: DISTRIBUCIÓN DE RISK_LEVEL")
        cursor.execute("SELECT risk_level, COUNT(*) as count FROM articles GROUP BY risk_level ORDER BY count DESC")
        risk_levels = cursor.fetchall()
        for level in risk_levels:
            print(f"   - {level['risk_level']}: {level['count']} artículos")
        
        # Verificar si hay lógica que asigna "medium" por defecto
        cursor.execute("SELECT COUNT(*) as count FROM articles WHERE risk_score > 0.7 AND risk_level = 'medium'")
        high_score_medium = cursor.fetchone()
        print(f"   ⚠️ Artículos con risk_score > 0.7 pero risk_level = 'medium': {high_score_medium['count']}")
        print()
        
        # 2. Problema: Filtrado geopolítico fallando
        print("🌍 PROBLEMA 2: FILTRADO GEOPOLÍTICO")
        
        # Buscar artículos NO geopolíticos que se colaron
        non_geopolitical_keywords = [
            'deporte', 'sport', 'football', 'soccer', 'basketball', 'tennis', 'golf',
            'entretenimiento', 'entertainment', 'celebrity', 'música', 'music',
            'tecnología básica', 'apps', 'videojuegos', 'games',
            'salud general', 'health tips', 'diet', 'fitness',
            'clima tiempo', 'weather forecast'
        ]
        
        for keyword in non_geopolitical_keywords[:5]:  # Revisar algunos
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM articles 
                WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
            """, (f'%{keyword}%', f'%{keyword}%'))
            result = cursor.fetchone()
            if result['count'] > 0:
                print(f"   ❌ Artículos con '{keyword}': {result['count']}")
        
        # Verificar si hay categorías no geopolíticas
        cursor.execute("SELECT category, COUNT(*) as count FROM articles GROUP BY category ORDER BY count DESC LIMIT 10")
        categories = cursor.fetchall()
        print(f"   📊 TOP CATEGORÍAS:")
        for cat in categories:
            print(f"   - {cat['category']}: {cat['count']} artículos")
        print()
        
        # 3. Problema: Mapa de calor con puntos aleatorios
        print("🗺️ PROBLEMA 3: COORDENADAS PARA MAPA DE CALOR")
        
        # Verificar si existen columnas de coordenadas
        cursor.execute("PRAGMA table_info(articles)")
        columns = [col['name'] for col in cursor.fetchall()]
        has_lat_lon = 'latitude' in columns and 'longitude' in columns
        print(f"   - Tiene columnas latitude/longitude: {has_lat_lon}")
        
        if not has_lat_lon:
            print("   ❌ NO HAY COLUMNAS DE COORDENADAS - Este es el problema del mapa!")
            print("   🔧 Se necesita crear las columnas y geocodificar los países/regiones")
        
        # Verificar la distribución de países para saber qué geocodificar
        cursor.execute("SELECT country, COUNT(*) as count FROM articles WHERE country IS NOT NULL GROUP BY country ORDER BY count DESC LIMIT 15")
        countries = cursor.fetchall()
        print(f"   📍 TOP PAÍSES PARA GEOCODIFICAR:")
        for country in countries:
            print(f"   - {country['country']}: {country['count']} artículos")
        print()
        
        # 4. Verificar el procesamiento NLP real
        print("🧠 PROBLEMA 4: CALIDAD DEL ANÁLISIS NLP")
        
        # Buscar artículos que deberían ser "high" risk pero están como "medium"
        cursor.execute("""
            SELECT title, risk_level, risk_score, conflict_probability, geopolitical_relevance
            FROM articles 
            WHERE (
                LOWER(title) LIKE '%war%' OR 
                LOWER(title) LIKE '%guerra%' OR 
                LOWER(title) LIKE '%conflict%' OR 
                LOWER(title) LIKE '%militar%' OR
                LOWER(title) LIKE '%attack%' OR
                LOWER(title) LIKE '%ataque%'
            )
            AND risk_level = 'medium'
            LIMIT 5
        """)
        should_be_high = cursor.fetchall()
        
        if should_be_high:
            print(f"   ⚠️ ARTÍCULOS QUE DEBERÍAN SER 'HIGH' RISK:")
            for article in should_be_high:
                print(f"   - {article['title'][:60]}...")
                print(f"     Risk: {article['risk_level']} (score: {article['risk_score']})")
                print(f"     Conflict prob: {article['conflict_probability']}")
                print(f"     Geopolitical rel: {article['geopolitical_relevance']}")
                print()
        
        # 5. Verificar si el algoritmo de risk_level está mal
        print("🔧 PROBLEMA 5: LÓGICA DE ASIGNACIÓN DE RISK_LEVEL")
        cursor.execute("""
            SELECT 
                AVG(risk_score) as avg_score,
                MIN(risk_score) as min_score,
                MAX(risk_score) as max_score,
                risk_level
            FROM articles 
            GROUP BY risk_level
        """)
        risk_level_stats = cursor.fetchall()
        
        print("   📊 ESTADÍSTICAS POR RISK_LEVEL:")
        for stat in risk_level_stats:
            print(f"   - {stat['risk_level']}: avg={stat['avg_score']:.3f}, min={stat['min_score']:.3f}, max={stat['max_score']:.3f}")
        
        # Detectar si hay solapamiento problemático
        cursor.execute("SELECT COUNT(*) as count FROM articles WHERE risk_score > 0.8 AND risk_level != 'high'")
        high_score_not_high = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as count FROM articles WHERE risk_score < 0.3 AND risk_level != 'low'")
        low_score_not_low = cursor.fetchone()
        
        print(f"   ❌ Risk_score > 0.8 pero NO 'high': {high_score_not_high['count']}")
        print(f"   ❌ Risk_score < 0.3 pero NO 'low': {low_score_not_low['count']}")

if __name__ == "__main__":
    check_database_issues()
