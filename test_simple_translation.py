#!/usr/bin/env python3
"""
Script simple para probar que la traducción funciona
"""

from robust_translation_v3 import UltraRobustTranslationService

def test_translation():
    try:
        # Inicializar traductor
        translator = UltraRobustTranslationService()
        print("✅ Traductor inicializado")
        
        # Probar traducción simple
        test_text = "This is a test article about geopolitics"
        translated, detected_lang = translator.translate_text(test_text, 'es')
        
        print(f"📝 Texto original: {test_text}")
        print(f"🌍 Idioma detectado: {detected_lang}")
        print(f"🔄 Texto traducido: {translated}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Probando sistema de traducción...")
    success = test_translation()
    
    if success:
        print("✅ Sistema de traducción funciona correctamente")
    else:
        print("❌ Sistema de traducción tiene problemas")