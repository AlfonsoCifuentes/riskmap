#!/usr/bin/env python3
"""
Script de prueba para el nuevo sistema de traducción gratuito
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from free_translation_v4 import initialize_translation_system

def test_translation_system():
    """Probar el sistema de traducción con casos reales"""
    print("🔄 Inicializando sistema de traducción gratuito...")
    
    translator = initialize_translation_system()
    
    if translator is None:
        print("❌ Error: No se pudo inicializar el sistema de traducción")
        return False
    
    print("✅ Sistema inicializado correctamente")
    
    # Casos de prueba reales del problema reportado
    test_cases = [
        "Denmark picks French-Italian SAMP/T air defense system over Patriot",
        "Pentagon stages first 'Top Drone' school for operators", 
        "NATO shot down 3 Russia drones in Poland",
        "Israel says Gaza is burning as it launches ground assault",
        "US issues new round of sanctions targeting Iran financing"
    ]
    
    print("\n🔍 Probando casos de traducción...")
    
    success_count = 0
    for i, text in enumerate(test_cases, 1):
        try:
            translated, detected_lang = translator.translate_text(text, 'es')
            
            if translated and translated != text:
                print(f"✅ Caso {i}: {text[:50]}...")
                print(f"   Traducido: {translated}")
                print(f"   Idioma: {detected_lang}")
                success_count += 1
            else:
                print(f"⚠️ Caso {i}: No se tradujo - {text[:50]}...")
                print(f"   Resultado: {translated}")
                
        except Exception as e:
            print(f"❌ Caso {i}: Error - {e}")
        
        print("-" * 60)
    
    print(f"\n📊 Resultados: {success_count}/{len(test_cases)} traducciones exitosas")
    
    if success_count > 0:
        print("✅ Sistema de traducción funcionando correctamente")
        return True
    else:
        print("❌ Sistema de traducción no funcionó en ningún caso")
        return False

if __name__ == "__main__":
    success = test_translation_system()
    sys.exit(0 if success else 1)