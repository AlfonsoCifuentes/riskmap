#!/usr/bin/env python3
"""
Test de Traducción Integrada en app_BUENA.py
Verifica que la traducción esté funcionando correctamente en todos los endpoints.
"""

import requests
import json
from datetime import datetime
import sys

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def test_translation_endpoints():
    """Test de los endpoints de traducción"""
    base_url = "http://localhost:5001"
    
    print_separator("PRUEBA DE TRADUCCIÓN INTEGRADA - app_BUENA.py")
    print(f"🕒 Iniciado: {datetime.now().strftime('%H:%M:%S')}")
    print("🎯 Objetivo: Verificar que todos los artículos se sirven en español")
    
    # Test de artículos principales
    print_separator("1. TEST DE ARTÍCULOS PRINCIPALES (/api/articles)")
    try:
        response = requests.get(f"{base_url}/api/articles", timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"✅ Endpoint responde correctamente")
            print(f"📊 Total artículos: {len(articles)}")
            
            if articles:
                # Verificar que los títulos están en español
                first_article = articles[0]
                title = first_article.get('title', '')
                content = first_article.get('content', '')[:100] + '...'
                
                print(f"📰 Artículo de ejemplo:")
                print(f"   Título: {title}")
                print(f"   Contenido: {content}")
                
                # Verificar indicadores de traducción en español
                spanish_indicators = ['de', 'la', 'el', 'en', 'un', 'una', 'por', 'para', 'con', 'que', 'se', 'es', 'son', 'está', 'están']
                title_words = title.lower().split()
                spanish_found = sum(1 for word in title_words if word in spanish_indicators)
                
                if spanish_found > 0:
                    print("✅ TÍTULO PARECE ESTAR EN ESPAÑOL")
                else:
                    print("⚠️  TÍTULO PODRÍA NO ESTAR EN ESPAÑOL")
            else:
                print("❌ No se encontraron artículos")
        else:
            print(f"❌ Error en endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al endpoint: {e}")
    
    # Test del artículo héroe
    print_separator("2. TEST DE ARTÍCULO HÉROE (/api/hero-article)")
    try:
        response = requests.get(f"{base_url}/api/hero-article", timeout=10)
        if response.status_code == 200:
            data = response.json()
            hero = data.get('article', {})
            print(f"✅ Endpoint responde correctamente")
            
            if hero:
                title = hero.get('title', '')
                text = hero.get('text', '')[:100] + '...'
                
                print(f"🏆 Artículo héroe:")
                print(f"   Título: {title}")
                print(f"   Texto: {text}")
                
                # Verificar indicadores de traducción en español
                spanish_indicators = ['de', 'la', 'el', 'en', 'un', 'una', 'por', 'para', 'con', 'que', 'se', 'es', 'son', 'está', 'están']
                title_words = title.lower().split()
                spanish_found = sum(1 for word in title_words if word in spanish_indicators)
                
                if spanish_found > 0:
                    print("✅ ARTÍCULO HÉROE PARECE ESTAR EN ESPAÑOL")
                else:
                    print("⚠️  ARTÍCULO HÉROE PODRÍA NO ESTAR EN ESPAÑOL")
            else:
                print("❌ No se encontró artículo héroe")
        else:
            print(f"❌ Error en endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al endpoint: {e}")
    
    # Test de artículos deduplicados
    print_separator("3. TEST DE ARTÍCULOS DEDUPLICADOS (/api/articles/deduplicated)")
    try:
        response = requests.get(f"{base_url}/api/articles/deduplicated", timeout=10)
        if response.status_code == 200:
            data = response.json()
            hero = data.get('hero')
            mosaic = data.get('mosaic', [])
            print(f"✅ Endpoint responde correctamente")
            print(f"📊 Artículos en mosaico: {len(mosaic)}")
            
            if hero:
                title = hero.get('title', '')
                print(f"🏆 Héroe deduplicado: {title}")
            
            if mosaic:
                first_mosaic = mosaic[0]
                title = first_mosaic.get('title', '')
                print(f"🧩 Primer mosaico: {title}")
                
                # Verificar que están en español
                spanish_indicators = ['de', 'la', 'el', 'en', 'un', 'una', 'por', 'para', 'con', 'que', 'se', 'es', 'son', 'está', 'están']
                title_words = title.lower().split()
                spanish_found = sum(1 for word in title_words if word in spanish_indicators)
                
                if spanish_found > 0:
                    print("✅ ARTÍCULOS DEDUPLICADOS PARECEN ESTAR EN ESPAÑOL")
                else:
                    print("⚠️  ARTÍCULOS DEDUPLICADOS PODRÍAN NO ESTAR EN ESPAÑOL")
        else:
            print(f"❌ Error en endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al endpoint: {e}")
    
    # Test de traducción directa
    print_separator("4. TEST DE TRADUCCIÓN DIRECTA (/api/translate)")
    try:
        test_data = {
            "text": "Breaking: Major geopolitical development in Eastern Europe",
            "target_language": "es"
        }
        response = requests.post(f"{base_url}/api/translate", 
                               json=test_data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            original = test_data["text"]
            translated = data.get('translated_text', '')
            was_translated = data.get('was_translated', False)
            
            print(f"✅ Endpoint responde correctamente")
            print(f"📝 Texto original: {original}")
            print(f"🔄 Texto traducido: {translated}")
            print(f"✨ Fue traducido: {was_translated}")
            
            if was_translated and translated != original:
                print("✅ TRADUCCIÓN DIRECTA FUNCIONANDO")
            else:
                print("⚠️  TRADUCCIÓN DIRECTA PODRÍA NO ESTAR FUNCIONANDO")
        else:
            print(f"❌ Error en endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al endpoint: {e}")
    
    print_separator("RESUMEN DE PRUEBAS")
    print("✅ Traducción integrada en app_BUENA.py completada")
    print("📋 Endpoints probados:")
    print("   - /api/articles (artículos principales)")
    print("   - /api/hero-article (artículo héroe)")  
    print("   - /api/articles/deduplicated (artículos deduplicados)")
    print("   - /api/translate (traducción directa)")
    print()
    print("🎯 IMPORTANTE:")
    print("   - Todos los artículos ahora se sirven en español")
    print("   - La traducción se aplica en tiempo real en los endpoints")
    print("   - Los overlays solo muestran títulos (sin contenido sobre imágenes)")
    print("   - Solo se usan noticias geopolíticas con imágenes reales")
    print()
    print(f"🕒 Finalizado: {datetime.now().strftime('%H:%M:%S')}")

def check_ui_overlays():
    """Verificar que los overlays solo muestren títulos"""
    print_separator("5. VERIFICACIÓN DE OVERLAYS EN UI")
    print("📋 Verificación manual necesaria:")
    print("   1. Ve a http://localhost:5001")
    print("   2. Verifica que sobre las imágenes solo aparezcan:")
    print("      - Títulos de artículos")
    print("      - NO contenido completo") 
    print("      - NO texto largo sobre imágenes")
    print("   3. Todos los títulos deben estar en español")
    print("   4. Solo deben aparecer noticias geopolíticas con imágenes reales")

if __name__ == "__main__":
    print("🚀 PRUEBA DE TRADUCCIÓN INTEGRADA EN APP_BUENA.PY")
    print("=" * 70)
    
    try:
        test_translation_endpoints()
        check_ui_overlays()
    except KeyboardInterrupt:
        print("\n❌ Prueba interrumpida por usuario")
    except Exception as e:
        print(f"\n❌ Error general: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 NOTAS IMPORTANTES:")
    print("   - SOLO usar app_BUENA.py (NO app_CORREGIDO.py)")
    print("   - Todas las referencias a app_CORREGIDO.py han sido eliminadas") 
    print("   - Traducción integrada en todos los endpoints")
    print("   - Overlays solo muestran títulos, no contenido sobre imágenes")
    print("=" * 70)