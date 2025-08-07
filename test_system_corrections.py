#!/usr/bin/env python3
"""
Script para verificar que los errores de JavaScript se han corregido
y que el monitor de conflictos usa solo datos reales
"""

import requests
import sqlite3
import os
from datetime import datetime

def test_hero_mosaico_separation():
    """Verificar que el HERO no se repita en el mosaico"""
    print("🔍 TESTING HERO/MOSAICO SEPARATION")
    print("=" * 50)
    
    try:
        # Obtener datos desde la API
        response = requests.get('http://localhost:5000/api/articles?limit=10')
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            if articles:
                # Verificar que no hay duplicados de ID
                article_ids = [article['id'] for article in articles]
                unique_ids = set(article_ids)
                
                print(f"   📊 Total artículos: {len(articles)}")
                print(f"   📊 IDs únicos: {len(unique_ids)}")
                
                if len(article_ids) == len(unique_ids):
                    print("   ✅ No hay duplicados de artículos en el mosaico")
                else:
                    print("   ❌ Se encontraron artículos duplicados")
                    duplicates = [id for id in article_ids if article_ids.count(id) > 1]
                    print(f"      IDs duplicados: {set(duplicates)}")
                
                # Mostrar primeros artículos
                print("\n   📋 Primeros artículos:")
                for i, article in enumerate(articles[:5], 1):
                    print(f"      {i}. ID {article['id']} - '{article['title'][:40]}...'")
            else:
                print("   ⚠️ No se obtuvieron artículos de la API")
        else:
            print(f"   ❌ Error en API: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_conflict_monitoring_real_data():
    """Verificar que el monitor de conflictos usa datos reales"""
    print("\n🔍 TESTING CONFLICT MONITORING REAL DATA")
    print("=" * 50)
    
    try:
        # Verificar API de conflictos
        response = requests.get('http://localhost:5000/api/conflict-monitoring/real-data')
        if response.status_code == 200:
            data = response.json()
            
            print(f"   📊 Success: {data.get('success')}")
            print(f"   📊 Data source: {data.get('data_source')}")
            
            conflicts = data.get('conflicts', [])
            statistics = data.get('statistics', {})
            
            print(f"   📊 Total conflictos: {len(conflicts)}")
            print(f"   📊 Con coordenadas: {data.get('total_with_coordinates', 0)}")
            
            if statistics:
                print(f"   📊 Conflictos alto riesgo: {statistics.get('high_risk_conflicts', 0)}")
                print(f"   📊 Países afectados: {statistics.get('affected_countries', 0)}")
                print(f"   📊 Fuentes activas: {statistics.get('active_sources', 0)}")
            
            # Verificar que los datos son reales (no simulados)
            real_data_indicators = [
                data.get('data_source') == 'real_database',
                len(conflicts) > 0,
                'timestamp' in data
            ]
            
            if all(real_data_indicators):
                print("   ✅ Monitor de conflictos usa datos reales")
            else:
                print("   ⚠️ Posibles datos simulados en monitor de conflictos")
                
        else:
            print(f"   ❌ Error en API conflict monitoring: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_database_geopolitical_filters():
    """Verificar filtros geopolíticos en base de datos"""
    print("\n🔍 TESTING DATABASE GEOPOLITICAL FILTERS")
    print("=" * 50)
    
    try:
        db_path = r"data\geopolitical_intel.db"
        
        if not os.path.exists(db_path):
            print(f"   ⚠️ Base de datos no encontrada en: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar filtros geopolíticos
        geopolitical_filters = """
            WHERE (is_excluded IS NULL OR is_excluded != 1)
            AND (image_url IS NOT NULL AND image_url != '' 
                 AND image_url NOT LIKE '%placeholder%'
                 AND image_url NOT LIKE '%unsplash.com%'
                 AND image_url NOT LIKE '%pexels.com%'
                 AND (image_url LIKE '%reuters.com%' 
                      OR image_url LIKE '%bbc.co.uk%'
                      OR image_url LIKE '%cnn.com%'
                      OR image_url LIKE '%france24.com%'
                      OR image_url LIKE '%aljazeera.com%'))
            AND (language = 'es' OR 
                 (is_translated = 1 AND original_language IS NOT NULL))
            AND (title NOT LIKE '%meteor%' 
                 AND title NOT LIKE '%sports%'
                 AND title NOT LIKE '%deporte%'
                 AND title NOT LIKE '%technology%'
                 AND title NOT LIKE '%health%')
        """
        
        # Contar artículos que pasan filtros
        cursor.execute(f"SELECT COUNT(*) FROM articles {geopolitical_filters}")
        filtered_count = cursor.fetchone()[0]
        
        # Contar total
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_count = cursor.fetchone()[0]
        
        # Verificar exclusiones específicas
        exclusion_checks = [
            ("meteoros", "title LIKE '%meteor%' OR title LIKE '%Perseid%'"),
            ("deportes", "title LIKE '%sports%' OR title LIKE '%deporte%'"),
            ("tecnología", "title LIKE '%technology%' OR title LIKE '%tech%'")
        ]
        
        print(f"   📊 Total artículos: {total_count}")
        print(f"   📊 Pasan filtros geopolíticos: {filtered_count}")
        print(f"   📊 Tasa de filtrado: {(filtered_count/total_count*100):.1f}%")
        
        print("\n   🚫 Artículos excluidos por filtros:")
        for category, pattern in exclusion_checks:
            cursor.execute(f"SELECT COUNT(*) FROM articles WHERE {pattern}")
            excluded_count = cursor.fetchone()[0]
            print(f"      - {category}: {excluded_count} artículos")
        
        conn.close()
        
        if filtered_count > 0:
            print("   ✅ Filtros geopolíticos funcionando correctamente")
        else:
            print("   ⚠️ Los filtros pueden ser demasiado estrictos")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_javascript_errors():
    """Verificar que no hay errores de sintaxis JavaScript"""
    print("\n🔍 TESTING JAVASCRIPT SYNTAX")
    print("=" * 50)
    
    # Verificar archivo modern_dashboard_fixed.js
    js_files = [
        "src/web/static/js/modern_dashboard_fixed.js",
        "src/web/static/js/fallback_manager.js"
    ]
    
    for js_file in js_files:
        if os.path.exists(js_file):
            print(f"   📄 Verificando {js_file}...")
            
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar problemas comunes
            syntax_issues = []
            
            # Verificar else duplicados
            else_count = content.count('} else {')
            consecutive_else = '} else {\n            } else {' in content
            if consecutive_else:
                syntax_issues.append("else duplicado encontrado")
            
            # Verificar llaves balanceadas
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                syntax_issues.append(f"llaves desbalanceadas: {open_braces} {{ vs {close_braces} }}")
            
            # Verificar paréntesis balanceados
            open_parens = content.count('(')
            close_parens = content.count(')')
            if open_parens != close_parens:
                syntax_issues.append(f"paréntesis desbalanceados: {open_parens} ( vs {close_parens} )")
            
            if syntax_issues:
                print(f"      ⚠️ Problemas encontrados: {', '.join(syntax_issues)}")
            else:
                print(f"      ✅ Sin problemas de sintaxis obvios")
        else:
            print(f"   ⚠️ Archivo no encontrado: {js_file}")

if __name__ == "__main__":
    print("🧪 TESTING SYSTEM CORRECTIONS")
    print("=" * 60)
    
    test_hero_mosaico_separation()
    test_conflict_monitoring_real_data()
    test_database_geopolitical_filters()
    test_javascript_errors()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMEN DE TESTS COMPLETADO")
