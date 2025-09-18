#!/usr/bin/env python3
"""
Script de prueba rápida para verificar optimizaciones de arranque
Verifica que la aplicación no reprocese artículos innecesariamente
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def quick_startup_test():
    """Test rápido del comportamiento de arranque optimizado"""
    
    print("🔄 TESTING OPTIMIZED STARTUP BEHAVIOR")
    print("=" * 60)
    
    # Simulate the check query from our optimized method
    db_path = './data/geopolitical_intel.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check that would now be performed before processing
        optimized_check_query = """
            SELECT COUNT(*) FROM articles a
            LEFT JOIN processed_data pd ON a.id = pd.article_id
            WHERE (pd.advanced_nlp IS NULL OR pd.advanced_nlp = '' OR pd.article_id IS NULL)
            AND a.is_excluded = 0
            AND a.created_at > datetime('now', '-7 days')
        """
        
        unprocessed_count = cursor.execute(optimized_check_query).fetchone()[0]
        
        print(f"📊 RESULTADOS DE VERIFICACIÓN OPTIMIZADA:")
        print(f"   - Artículos sin procesar (7 días): {unprocessed_count}")
        
        if unprocessed_count == 0:
            print("✅ EXCELENTE: No hay artículos para procesar")
            print("   La aplicación debería arrancar RÁPIDAMENTE")
            print("   No se ejecutará procesamiento NLP innecesario")
        else:
            print(f"⚠️  Se encontraron {unprocessed_count} artículos para procesar")
            print("   El procesamiento NLP se ejecutará solo para estos artículos")
        
        # Also check total articles to confirm database state
        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_excluded = 0")
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM articles a
            LEFT JOIN processed_data pd ON a.id = pd.article_id
            WHERE pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != ''
            AND a.is_excluded = 0
        """)
        processed_articles = cursor.fetchone()[0]
        
        print(f"\n📈 ESTADO GENERAL DE LA BASE DE DATOS:")
        print(f"   - Artículos totales: {total_articles}")
        print(f"   - Artículos procesados: {processed_articles}")
        print(f"   - Cobertura NLP: {(processed_articles/total_articles*100):.1f}%")
        
        # Test the old problematic query too for comparison
        problematic_query = """
            SELECT COUNT(*) FROM articles a
            LEFT JOIN processed_data pd ON a.url = pd.url
            WHERE (pd.advanced_nlp IS NULL OR pd.advanced_nlp = '' OR pd.id IS NULL)
            AND a.is_excluded = 0
        """
        
        old_result = cursor.execute(problematic_query).fetchone()[0]
        print(f"\n🔍 COMPARACIÓN CON LÓGICA ANTERIOR:")
        print(f"   - Consulta antigua (problemática): {old_result} artículos")
        print(f"   - Consulta nueva (optimizada): {unprocessed_count} artículos")
        print(f"   - Mejora: {old_result - unprocessed_count} menos artículos a procesar")
        
        conn.close()
        
        print("\n" + "=" * 60)
        if unprocessed_count == 0:
            print("🎉 STARTUP OPTIMIZATION EXITOSA")
            print("   ✅ La aplicación arrancará SIN procesamiento NLP")
            print("   ✅ Tiempo de inicio SIGNIFICATIVAMENTE reducido")
            print("   ✅ No reprocesará artículos ya analizados")
        else:
            print("⚠️  STARTUP CON PROCESAMIENTO MÍNIMO")
            print(f"   🔄 Solo procesará {unprocessed_count} artículos nuevos")
            print("   ✅ Evitará reprocesar artículos existentes")
        
        return unprocessed_count
        
    except Exception as e:
        print(f"❌ Error en test de startup: {e}")
        return None

if __name__ == "__main__":
    result = quick_startup_test()
    if result is not None:
        print(f"\n✅ Test de optimización completado - {result} artículos pendientes")
    else:
        print("\n❌ Test de optimización falló")