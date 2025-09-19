#!/usr/bin/env python3
"""
Prueba del endpoint de traducción al vuelo
"""

import requests
import json
import sys

def test_translation_endpoint():
    """Prueba el endpoint /api/translate"""
    
    base_url = "http://localhost:8050"
    endpoint = "/api/translate"
    
    test_cases = [
        {
            "name": "English to Spanish",
            "data": {
                "text": "Breaking news: tensions escalate in Eastern Europe as diplomatic crisis unfolds",
                "source_lang": "en",
                "target_lang": "es"
            }
        },
        {
            "name": "Auto-detect English",
            "data": {
                "text": "The situation is becoming increasingly complex with multiple stakeholders involved",
                "source_lang": "auto",
                "target_lang": "es"
            }
        },
        {
            "name": "Already Spanish",
            "data": {
                "text": "Las tensiones geopolíticas se intensifican en Europa Oriental",
                "source_lang": "auto",
                "target_lang": "es"
            }
        },
        {
            "name": "Short text",
            "data": {
                "text": "Hi",
                "source_lang": "auto",
                "target_lang": "es"
            }
        }
    ]
    
    print("🧪 Probando endpoint de traducción...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"Texto original: {test_case['data']['text']}")
        
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Traducción: {result.get('translated_text', 'N/A')}")
                    print(f"Idioma detectado: {result.get('detected_lang', 'N/A')}")
                    if result.get('original_text') != result.get('translated_text'):
                        print("🔄 Texto traducido correctamente")
                    else:
                        print("ℹ️ Texto sin cambios (ya en español)")
                else:
                    print(f"❌ Error en respuesta: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ Error HTTP: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Error: No se puede conectar al servidor")
            print("   Asegúrate de que el servidor Flask esté corriendo en puerto 5000")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")

if __name__ == "__main__":
    test_translation_endpoint()
