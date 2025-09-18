#!/usr/bin/env python3
"""
Script para verificar y optimizar la lógica de procesamiento NLP
Diagnostica por qué se están reprocesando artículos que ya tienen análisis avanzado
"""

import sqlite3
from datetime import datetime, timedelta

def check_nlp_processing_logic():
    """Verificar la lógica de la consulta NLP actual"""
    
    db_path = './data/geopolitical_intel.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 DIAGNÓSTICO DE PROCESAMIENTO NLP")
        print("=" * 60)
        
        # 1. Verificar estructura de tablas
        print("1. VERIFICANDO ESTRUCTURA DE TABLAS:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"   Tablas disponibles: {[t[0] for t in tables]}")
        
        # 2. Verificar columnas de processed_data
        print("\n2. COLUMNAS EN processed_data:")
        cursor.execute("PRAGMA table_info(processed_data)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # 3. Contar artículos totales
        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_excluded = 0")
        total_articles = cursor.fetchone()[0]
        print(f"\n3. ARTÍCULOS TOTALES (no excluidos): {total_articles}")
        
        # 4. Verificar artículos con advanced_nlp
        cursor.execute("""
            SELECT COUNT(*) FROM processed_data 
            WHERE advanced_nlp IS NOT NULL AND advanced_nlp != ''
        """)
        with_advanced_nlp = cursor.fetchone()[0]
        print(f"4. ARTÍCULOS CON ADVANCED_NLP: {with_advanced_nlp}")
        
        # 5. Consulta actual que usa el sistema (problemática)
        print("\n5. CONSULTA ACTUAL (PROBLEMÁTICA):")
        current_query = """
            SELECT a.id, a.title, a.content, a.country, a.language
            FROM articles a
            LEFT JOIN processed_data pd ON a.url = pd.url
            WHERE (pd.advanced_nlp IS NULL OR pd.advanced_nlp = '' OR pd.id IS NULL)
            AND a.is_excluded = 0
            ORDER BY a.created_at DESC
            LIMIT 10
        """
        print(current_query)
        
        cursor.execute(current_query)
        problematic_results = cursor.fetchall()
        print(f"   Artículos encontrados por consulta problemática: {len(problematic_results)}")
        
        # 6. Consulta mejorada
        print("\n6. CONSULTA OPTIMIZADA (RECOMENDADA):")
        optimized_query = """
            SELECT a.id, a.title, a.content, a.country, a.language
            FROM articles a
            LEFT JOIN processed_data pd ON a.id = pd.article_id
            WHERE (pd.advanced_nlp IS NULL OR pd.advanced_nlp = '' OR pd.article_id IS NULL)
            AND a.is_excluded = 0
            AND a.created_at > datetime('now', '-7 days')
            ORDER BY a.created_at DESC
            LIMIT 10
        """
        print(optimized_query)
        
        cursor.execute(optimized_query)
        optimized_results = cursor.fetchall()
        print(f"   Artículos encontrados por consulta optimizada: {len(optimized_results)}")
        
        # 7. Verificar artículos recientes (últimos 7 días)
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE created_at > datetime('now', '-7 days') 
            AND is_excluded = 0
        """)
        recent_articles = cursor.fetchone()[0]
        print(f"\n7. ARTÍCULOS RECIENTES (7 días): {recent_articles}")
        
        # 8. Verificar join correcto
        cursor.execute("""
            SELECT COUNT(*) FROM articles a
            LEFT JOIN processed_data pd ON a.id = pd.article_id
            WHERE pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != ''
            AND a.is_excluded = 0
        """)
        correct_join_count = cursor.fetchone()[0]
        print(f"8. ARTÍCULOS CON NLP (JOIN CORRECTO): {correct_join_count}")
        
        print("\n" + "=" * 60)
        print("🎯 DIAGNÓSTICO COMPLETO:")
        print(f"   - Total artículos: {total_articles}")
        print(f"   - Con análisis NLP: {with_advanced_nlp}")
        print(f"   - Consulta actual encuentra: {len(problematic_results)} (MALO)")
        print(f"   - Consulta optimizada encuentra: {len(optimized_results)} (BUENO)")
        print(f"   - Artículos recientes: {recent_articles}")
        print(f"   - Join correcto: {correct_join_count}")
        
        if len(problematic_results) > 100:
            print("\n❌ PROBLEMA IDENTIFICADO:")
            print("   La consulta actual está usando JOIN incorrecto (a.url = pd.url)")
            print("   Debería usar (a.id = pd.article_id)")
            print("   Esto causa que encuentre artículos ya procesados")
            
        return {
            'total_articles': total_articles,
            'with_advanced_nlp': with_advanced_nlp,
            'problematic_query_results': len(problematic_results),
            'optimized_query_results': len(optimized_results),
            'recent_articles': recent_articles,
            'correct_join_count': correct_join_count
        }
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    results = check_nlp_processing_logic()
    if results:
        print("\n✅ Diagnóstico completado")
    else:
        print("\n❌ Diagnóstico falló")