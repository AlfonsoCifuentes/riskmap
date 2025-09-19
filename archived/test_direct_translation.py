#!/usr/bin/env python3
"""
Prueba de la función de traducción directa
"""

import sys
import os
import sqlite3

# Añadir directorio raíz al path
sys.path.append(os.path.dirname(__file__))

# Importar la función directamente del app
try:
    from app_BUENA import RiskMapUnifiedApplication
    app_available = True
except ImportError:
    app_available = False

def test_direct_translation():
    """Probar la función de traducción directa"""
    if not app_available:
        print("❌ No se pudo importar la aplicación")
        return
    
    try:
        print("🔄 Creando instancia de la aplicación...")
        
        # Crear instancia de la aplicación
        app = RiskMapUnifiedApplication()
        
        print("🔄 Ejecutando traducción directa...")
        
        # Ejecutar traducción directa
        result = app._translate_english_articles_direct()
        
        print("\n📊 Resultado de la traducción:")
        print(f"Éxito: {result.get('success', False)}")
        print(f"Artículos traducidos: {result.get('translated_count', 0)}")
        print(f"Errores: {result.get('errors', 0)}")
        print(f"Total revisados: {result.get('total_reviewed', 0)}")
        print(f"Mensaje: {result.get('message', '')}")
        
        if result.get('success'):
            print("✅ Traducción completada exitosamente")
        else:
            print(f"❌ Error en traducción: {result.get('error', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_translation_results():
    """Verificar resultados de traducción en la base de datos"""
    try:
        db_path = "data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 Verificando resultados de traducción...")
        
        # Contar artículos traducidos
        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_translated = 1")
        translated_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE original_language = 'en'")
        english_count = cursor.fetchone()[0]
        
        print(f"Artículos marcados como traducidos: {translated_count}")
        print(f"Artículos marcados como inglés: {english_count}")
        
        # Mostrar algunos ejemplos de traducciones
        cursor.execute("""
            SELECT id, original_title, title, is_translated
            FROM articles 
            WHERE is_translated = 1
            ORDER BY id DESC
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        
        if examples:
            print("\n🔍 Ejemplos de artículos traducidos:")
            for article_id, original_title, current_title, is_translated in examples:
                print(f"ID {article_id}:")
                print(f"  Original: {(original_title or 'N/A')[:80]}...")
                print(f"  Actual: {(current_title or 'N/A')[:80]}...")
                print(f"  ¿Traducido?: {bool(is_translated)}")
                print("-" * 60)
        else:
            print("ℹ️ No se encontraron ejemplos de traducciones")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando resultados: {e}")

def main():
    print("🌍 Prueba de Traducción Directa - RiskMap")
    print("=" * 50)
    
    test_direct_translation()
    check_translation_results()

if __name__ == "__main__":
    main()
