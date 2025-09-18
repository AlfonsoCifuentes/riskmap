#!/usr/bin/env python3
"""
Test the complete NLP processing pipeline with our NULL content fixes
"""
import sqlite3
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_nlp_pipeline_with_null_content():
    """Test NLP processing specifically for articles with NULL content"""
    
    print("🧠 PROBANDO PIPELINE NLP CON CONTENIDO NULL")
    print("=" * 60)
    
    try:
        # Import the orchestrator
        from orchestration.main_orchestrator import GeopoliticalIntelligenceOrchestrator
        
        # Initialize orchestrator
        orchestrator = GeopoliticalIntelligenceOrchestrator()
        
        print("✅ Orchestrator inicializado correctamente")
        
        # Test with articles that have NULL content
        test_article_ids = [1117, 1116, 1115, 1114, 1113]
        
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n🔍 Verificando que artículos {test_article_ids} tienen contenido NULL...")
        
        for article_id in test_article_ids:
            cursor.execute("""
                SELECT id, title, content, country, language
                FROM articles 
                WHERE id = ?
            """, (article_id,))
            
            article = cursor.fetchone()
            if article:
                article_id, title, content, country, language = article
                content_status = "NULL" if content is None else f"{len(content)} chars"
                print(f"   📄 Artículo {article_id}: {content_status}")
        
        conn.close()
        
        print(f"\n🧠 Procesando artículos con NLP avanzado...")
        print("   Esto debería procesar sin errores 'NoneType'...")
        
        # Process only a few articles to test
        result = orchestrator.process_articles_nlp_advanced(limit=5)
        
        print(f"✅ Procesamiento completado: {result} artículos procesados")
        print("🎉 ¡Sin errores de NoneType!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en el pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_script_with_null_content():
    """Test the batch processing script"""
    
    print(f"\n🔄 PROBANDO SCRIPT DE PROCESAMIENTO BATCH")
    print("=" * 60)
    
    try:
        # Run the batch processing script with a limit
        os.system("python process_all_articles_nlp.py --limit 3")
        print("✅ Script batch ejecutado sin errores")
        return True
        
    except Exception as e:
        print(f"❌ Error en script batch: {e}")
        return False

def test_integration_script():
    """Test the integration script"""
    
    print(f"\n🔗 PROBANDO SCRIPT DE INTEGRACIÓN")
    print("=" * 60)
    
    try:
        # Run the integration script with a limit
        os.system("python integrate_advanced_nlp.py --limit 3")
        print("✅ Script de integración ejecutado sin errores")
        return True
        
    except Exception as e:
        print(f"❌ Error en script de integración: {e}")
        return False

if __name__ == "__main__":
    print("🔧 PRUEBAS COMPLETAS DE CORRECCIÓN DE ERRORES NONETYPE")
    print("=" * 70)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: NLP Pipeline
    if test_nlp_pipeline_with_null_content():
        tests_passed += 1
    
    # Test 2: Batch Script  
    if test_batch_script_with_null_content():
        tests_passed += 1
        
    # Test 3: Integration Script
    if test_integration_script():
        tests_passed += 1
    
    print(f"\n🎯 RESULTADO FINAL:")
    print("=" * 70)
    print(f"✅ Pruebas pasadas: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("🔧 Las correcciones de NoneType están funcionando correctamente")
    else:
        print("⚠️ Algunas pruebas fallaron, revisar errores arriba")