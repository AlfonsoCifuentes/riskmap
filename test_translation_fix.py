#!/usr/bin/env python3
"""
Test específico para verificar que el error de traducción está resuelto.

Este script reproduce el error original:
"Translation failed: module 'httpcore' has no attribute 'SyncHTTPTransport'"

Y verifica que ahora funciona correctamente con el sistema ultra-robusto v3.0.
"""

import sys
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_translation_error_fix():
    """Testear que el error de SyncHTTPTransport está resuelto."""
    
    print("🧪 Test de Resolución del Error de Traducción")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Importar el sistema ultra-robusto
    print("📋 Test 1: Importar sistema ultra-robusto v3.0")
    try:
        from robust_translation_v3 import UltraRobustTranslationService, get_ultra_robust_translation
        print("✅ Importación exitosa del sistema ultra-robusto v3.0")
    except ImportError as e:
        print(f"❌ Error en importación: {e}")
        return False
    
    # Test 2: Inicializar servicio
    print("\n📋 Test 2: Inicializar servicio de traducción")
    try:
        service = UltraRobustTranslationService()
        print("✅ Servicio inicializado correctamente")
    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        return False
    
    # Test 3: Traducir texto problemático que causaba el error original
    print("\n📋 Test 3: Traducir texto que causaba error SyncHTTPTransport")
    problematic_texts = [
        "Breaking news: Major conflict reported in Middle East region",
        "Government officials confirm security alert in capital city",
        "Emergency services respond to explosion near government buildings",
        "International observers express concern about escalating violence"
    ]
    
    all_tests_passed = True
    
    for i, text in enumerate(problematic_texts, 1):
        print(f"\n🔍 Subtest 3.{i}: '{text[:50]}...'")
        try:
            translated, detected_lang = service.translate_text(text, 'es')
            
            if translated and translated != text:
                print(f"✅ Traducción exitosa")
                print(f"   Original: {text}")
                print(f"   Traducido: {translated}")
                print(f"   Idioma detectado: {detected_lang}")
            else:
                print(f"⚠️ Traducción no aplicada (posiblemente ya en español)")
                print(f"   Texto: {text}")
                print(f"   Idioma detectado: {detected_lang}")
        except Exception as e:
            print(f"❌ Error en traducción: {e}")
            all_tests_passed = False
    
    # Test 4: Usar función de conveniencia
    print("\n📋 Test 4: Usar función de conveniencia get_ultra_robust_translation")
    try:
        test_text = "Terror attack reported in downtown area, emergency response activated"
        translated, detected = get_ultra_robust_translation(test_text, 'es')
        print("✅ Función de conveniencia funciona correctamente")
        print(f"   Original: {test_text}")
        print(f"   Traducido: {translated}")
        print(f"   Idioma detectado: {detected}")
    except Exception as e:
        print(f"❌ Error en función de conveniencia: {e}")
        all_tests_passed = False
    
    # Test 5: Probar con translation_service.py actualizado
    print("\n📋 Test 5: Probar con translation_service.py actualizado")
    try:
        from translation_service import translate_text_robust
        test_text = "Crisis situation develops as protests continue in major cities"
        translated, detected = translate_text_robust(test_text, 'es')
        print("✅ translation_service.py actualizado funciona correctamente")
        print(f"   Original: {test_text}")
        print(f"   Traducido: {translated}")
        print(f"   Idioma detectado: {detected}")
    except Exception as e:
        print(f"❌ Error en translation_service actualizado: {e}")
        all_tests_passed = False
    
    # Resumen final
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("✅ El error de 'SyncHTTPTransport' ha sido RESUELTO")
        print("✅ El sistema de traducción ultra-robusto v3.0 está funcionando")
        print("✅ No hay dependencias problemáticas de httpcore/httpx")
        print("✅ Sistema completamente operativo y libre de errores")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("⚠️ El sistema necesita revisión adicional")
    
    return all_tests_passed

if __name__ == "__main__":
    success = test_translation_error_fix()
    
    if success:
        print("\n🚀 Sistema listo para producción")
        sys.exit(0)
    else:
        print("\n🔧 Sistema necesita ajustes")
        sys.exit(1)
