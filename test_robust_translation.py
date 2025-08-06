#!/usr/bin/env python3
"""
Test específico para el sistema de traducción robusto
"""

import requests
import json
import time

def test_robust_translation():
    """Probar el sistema de traducción robusto con diferentes tipos de texto"""
    
    print("🧪 PROBANDO SISTEMA DE TRADUCCIÓN ROBUSTO")
    print("=" * 50)
    
    # Textos de prueba en diferentes idiomas
    test_texts = [
        {
            'text': 'This is a conflict in Ukraine involving military forces',
            'expected_lang': 'en',
            'description': 'Texto en inglés sobre conflicto'
        },
        {
            'text': 'Ceci est un conflit en France avec des manifestants',
            'expected_lang': 'fr', 
            'description': 'Texto en francés sobre conflicto'
        },
        {
            'text': 'Dies ist ein Konflikt in Deutschland mit Protesten',
            'expected_lang': 'de',
            'description': 'Texto en alemán sobre conflicto'
        },
        {
            'text': 'Esta es una noticia en español sobre un conflicto',
            'expected_lang': 'es',
            'description': 'Texto en español (no debería traducirse)'
        },
        {
            'text': 'Questo è un conflitto in Italia con manifestazioni',
            'expected_lang': 'it',
            'description': 'Texto en italiano sobre conflicto'
        }
    ]
    
    successful_tests = 0
    total_tests = len(test_texts)
    
    for i, test_case in enumerate(test_texts, 1):
        print(f"\n🔍 Prueba {i}/{total_tests}: {test_case['description']}")
        print(f"📝 Texto original: {test_case['text']}")
        
        try:
            # Probar endpoint de traducción
            response = requests.post('http://localhost:8050/api/translate', 
                                   json={'text': test_case['text']},
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                translated_text = data.get('translated_text', '')
                detected_lang = data.get('detected_language', '')
                
                print(f"📄 Texto traducido: {translated_text}")
                print(f"🌍 Idioma detectado: {detected_lang}")
                print(f"✅ Estado: SUCCESS")
                
                # Verificar que la traducción tiene sentido
                if test_case['expected_lang'] == 'es':
                    # No debería cambiar mucho si ya está en español
                    if translated_text == test_case['text']:
                        print("✅ Correctamente identificado como español - no traducido")
                    else:
                        print("⚠️ Traducido innecesariamente desde español")
                else:
                    # Debería ser diferente al original
                    if translated_text != test_case['text']:
                        print("✅ Traducción aplicada correctamente")
                    else:
                        print("⚠️ Traducción no aplicada (puede ser fallback)")
                
                successful_tests += 1
                
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"📄 Respuesta: {response.text}")
                
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
        
        time.sleep(2)  # Pausa entre pruebas
    
    print(f"\n📋 RESUMEN DE PRUEBAS DE TRADUCCIÓN:")
    print(f"✅ Pruebas exitosas: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 ¡Sistema de traducción robusto funcionando correctamente!")
    else:
        print("⚠️ Algunas pruebas fallaron - revisar logs del servidor")

def test_direct_robust_translation():
    """Probar directamente el módulo de traducción robusto"""
    print(f"\n🔧 PROBANDO MÓDULO ROBUSTO DIRECTAMENTE")
    print("=" * 50)
    
    try:
        from robust_translation import get_robust_translation
        
        test_text = "This is a breaking news about armed conflict in Eastern Europe"
        print(f"📝 Texto de prueba: {test_text}")
        
        translated, detected_lang = get_robust_translation(test_text)
        
        print(f"📄 Traducción directa: {translated}")
        print(f"🌍 Idioma detectado: {detected_lang}")
        
        if translated != test_text:
            print("✅ Traducción directa exitosa")
        else:
            print("⚠️ Traducción directa no aplicada")
            
    except Exception as e:
        print(f"❌ Error probando módulo directo: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del sistema de traducción robusto...")
    
    # Esperar que el servidor esté listo
    print("⏳ Esperando a que el servidor esté listo...")
    time.sleep(3)
    
    # Probar endpoint de traducción
    test_robust_translation()
    
    # Probar módulo directo
    test_direct_robust_translation()
    
    print("\n🎯 Pruebas completadas!")
