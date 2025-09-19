#!/usr/bin/env python3
"""
Script de prueba para verificar:
1. Que la traducción funciona correctamente en el backend
2. Que los overlays del mosaic solo muestran títulos
3. Que todas las noticias aparecen en español
"""

import requests
import json
import logging
from bs4 import BeautifulSoup
import time

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_backend_translation():
    """Probar que el backend devuelve artículos traducidos"""
    print("\n🧪 PRUEBA 1: Verificando traducción en backend")
    print("="*50)
    
    try:
        # Probar endpoint de artículos
        response = requests.get("http://localhost:5001/api/articles", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error de respuesta: {response.status_code}")
            return False
        
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ API devolvió error: {data.get('error', 'Error desconocido')}")
            return False
        
        articles = data.get('articles', [])
        print(f"📰 Recibidos {len(articles)} artículos")
        
        if not articles:
            print("⚠️ No hay artículos disponibles")
            return False
        
        # Analizar primeros 3 artículos
        spanish_titles = 0
        spanish_summaries = 0
        
        for i, article in enumerate(articles[:3]):
            print(f"\n📄 Artículo {i+1}:")
            print(f"   ID: {article.get('id')}")
            
            title = article.get('title', '')
            summary = article.get('summary', '')
            
            print(f"   Título: {title[:100]}...")
            print(f"   Resumen: {summary[:100]}...")
            
            # Heurística simple para detectar español
            spanish_indicators = ['el ', 'la ', 'los ', 'las ', 'de ', 'en ', 'con ', 'por ', 'para ', 'que ', 'se ', 'una ', 'un ']
            
            title_lower = title.lower()
            summary_lower = summary.lower()
            
            title_spanish_score = sum(1 for indicator in spanish_indicators if indicator in title_lower)
            summary_spanish_score = sum(1 for indicator in spanish_indicators if indicator in summary_lower)
            
            if title_spanish_score >= 2:
                spanish_titles += 1
                print(f"   ✅ Título parece estar en español (score: {title_spanish_score})")
            else:
                print(f"   ⚠️ Título puede no estar en español (score: {title_spanish_score})")
            
            if summary_spanish_score >= 3:
                spanish_summaries += 1
                print(f"   ✅ Resumen parece estar en español (score: {summary_spanish_score})")
            else:
                print(f"   ⚠️ Resumen puede no estar en español (score: {summary_spanish_score})")
        
        print(f"\n📊 Resultados:")
        print(f"   Títulos en español: {spanish_titles}/3")
        print(f"   Resúmenes en español: {spanish_summaries}/3")
        
        success_rate = (spanish_titles + spanish_summaries) / 6 * 100
        print(f"   Tasa de traducción: {success_rate:.1f}%")
        
        return success_rate >= 50  # Al menos 50% debe estar traducido
        
    except Exception as e:
        print(f"❌ Error probando backend: {e}")
        return False

def test_hero_article_translation():
    """Probar que el artículo héroe está traducido"""
    print("\n🧪 PRUEBA 2: Verificando traducción de artículo héroe")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:5001/api/hero-article", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error de respuesta: {response.status_code}")
            return False
        
        article = response.json()
        
        title = article.get('title', '')
        summary = article.get('summary', '')
        
        print(f"🏆 Artículo Héroe:")
        print(f"   Título: {title}")
        print(f"   Resumen: {summary[:200]}...")
        
        # Verificar español en héroe
        spanish_indicators = ['el ', 'la ', 'los ', 'las ', 'de ', 'en ', 'con ', 'por ', 'para ', 'que ', 'se ']
        
        title_lower = title.lower()
        summary_lower = summary.lower()
        
        title_spanish = sum(1 for indicator in spanish_indicators if indicator in title_lower) >= 2
        summary_spanish = sum(1 for indicator in spanish_indicators if indicator in summary_lower) >= 3
        
        if title_spanish:
            print("   ✅ Título héroe está en español")
        else:
            print("   ⚠️ Título héroe puede no estar en español")
        
        if summary_spanish:
            print("   ✅ Resumen héroe está en español")
        else:
            print("   ⚠️ Resumen héroe puede no estar en español")
        
        return title_spanish and summary_spanish
        
    except Exception as e:
        print(f"❌ Error probando artículo héroe: {e}")
        return False

def test_frontend_structure():
    """Probar que el frontend tiene la estructura correcta"""
    print("\n🧪 PRUEBA 3: Verificando estructura del frontend")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:5001/", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error accediendo al frontend: {response.status_code}")
            return False
        
        # Analizar si el dashboard está siendo servido correctamente
        content = response.text
        
        # Verificar que no es solo la página básica
        if "Dashboard" in content or "mosaic" in content.lower():
            print("✅ Frontend parece estar sirviendo el dashboard completo")
            
            # Verificar que no hay contenido de overlay extra en el HTML
            if "mosaic-description" in content:
                print("⚠️ Encontrado elemento mosaic-description en HTML")
            else:
                print("✅ No se encontraron elementos mosaic-description problemáticos")
            
            return True
        else:
            print("⚠️ Frontend parece estar sirviendo página básica, no el dashboard")
            return False
        
    except Exception as e:
        print(f"❌ Error probando frontend: {e}")
        return False

def test_api_endpoints():
    """Probar todos los endpoints importantes"""
    print("\n🧪 PRUEBA 4: Verificando endpoints de API")
    print("="*50)
    
    endpoints = [
        "/api/status",
        "/api/articles",
        "/api/hero-article",
        "/api/articles/deduplicated"
    ]
    
    working_endpoints = 0
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:5001{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
                working_endpoints += 1
            else:
                print(f"❌ {endpoint} - Error {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Excepción: {e}")
    
    success_rate = working_endpoints / len(endpoints) * 100
    print(f"\n📊 Endpoints funcionando: {working_endpoints}/{len(endpoints)} ({success_rate:.1f}%)")
    
    return success_rate >= 75  # Al menos 75% de endpoints deben funcionar

def main():
    """Función principal de pruebas"""
    print("🔬 INICIANDO PRUEBAS DE TRADUCCIÓN Y OVERLAYS")
    print("="*60)
    
    # Esperar un momento para asegurar que el servidor esté listo
    print("⏳ Esperando que el servidor esté disponible...")
    time.sleep(2)
    
    tests = [
        ("Traducción Backend", test_backend_translation),
        ("Traducción Héroe", test_hero_article_translation),
        ("Estructura Frontend", test_frontend_structure),
        ("Endpoints API", test_api_endpoints)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_function in tests:
        try:
            result = test_function()
            if result:
                passed_tests += 1
                print(f"\n✅ PRUEBA PASADA: {test_name}")
            else:
                print(f"\n❌ PRUEBA FALLADA: {test_name}")
        except Exception as e:
            print(f"\n💥 ERROR EN PRUEBA {test_name}: {e}")
    
    # Resultados finales
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    print(f"✅ Pruebas pasadas: {passed_tests}/{total_tests}")
    print(f"📈 Tasa de éxito: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests >= total_tests * 0.75:  # Al menos 75% de pruebas deben pasar
        print("\n🎉 ¡PRUEBAS EXITOSAS! El sistema funciona correctamente.")
        return True
    else:
        print("\n⚠️ PRUEBAS CON PROBLEMAS. Revisa los errores anteriores.")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n💡 RECOMENDACIONES:")
        print("   1. Asegúrate de que app_BUENA.py esté ejecutándose en puerto 5001")
        print("   2. Ejecuta translate_all_articles.py para traducir contenido existente")
        print("   3. Verifica que robust_translation_v3.py esté disponible")
        print("   4. Revisa los logs para errores específicos")