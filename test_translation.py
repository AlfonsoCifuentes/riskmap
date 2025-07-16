#!/usr/bin/env python3
"""
Script de prueba para validar la traducción gratuita con googletrans.
Prueba traducciones en los 5 idiomas soportados: ES, EN, RU, ZH, AR
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from nlp_processing.text_analyzer import TranslationService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_translations():
    """Prueba el servicio de traducción con textos de ejemplo."""
    
    print("🔧 Inicializando servicio de traducción...")
    translator = TranslationService()
    
    # Textos de prueba en diferentes idiomas
    test_cases = [
        {
            'text': 'La tensión geopolítica está aumentando en la región.',
            'source': 'es',
            'targets': ['en', 'ru', 'zh', 'ar'],
            'expected_en': 'Geopolitical tension is increasing in the region.'
        },
        {
            'text': 'Military conflict erupts in Eastern Europe.',
            'source': 'en', 
            'targets': ['es', 'ru', 'zh', 'ar'],
            'expected_es': 'El conflicto militar estalla en Europa del Este.'
        },
        {
            'text': 'Военный конфликт разразился в Восточной Европе.',
            'source': 'ru',
            'targets': ['en', 'es', 'zh', 'ar'],
            'expected_en': 'Military conflict broke out in Eastern Europe.'
        },
        {
            'text': '地缘政治局势正在升级',
            'source': 'zh',
            'targets': ['en', 'es', 'ru', 'ar'],
            'expected_en': 'The geopolitical situation is escalating'
        },
        {
            'text': 'الوضع الجيوسياسي يتصاعد في المنطقة',
            'source': 'ar',
            'targets': ['en', 'es', 'ru', 'zh'],
            'expected_en': 'The geopolitical situation is escalating in the region'
        }
    ]
    
    print(f"\n🌍 Probando traducción en {len(test_cases)} casos...")
    
    success_count = 0
    total_translations = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Caso {i}: {case['source'].upper()} ---")
        print(f"📝 Texto original: {case['text']}")
        
        for target in case['targets']:
            try:
                translated = translator.translate_text(
                    case['text'], 
                    target_language=target,
                    source_language=case['source']
                )
                
                print(f"  ➤ {target.upper()}: {translated}")
                
                if translated != case['text']:  # Si se tradujo correctamente
                    success_count += 1
                total_translations += 1
                
            except Exception as e:
                print(f"  ❌ Error {case['source']}->{target}: {e}")
                total_translations += 1
    
    # Mostrar estadísticas
    print(f"\n📊 RESULTADOS:")
    print(f"✅ Traducciones exitosas: {success_count}/{total_translations}")
    print(f"📈 Tasa de éxito: {(success_count/total_translations)*100:.1f}%")
    
    # Mostrar métricas del servicio
    stats = translator.stats
    print(f"\n📋 MÉTRICAS DEL SERVICIO:")
    print(f"🔄 Total traducciones: {stats['total_translations']}")
    print(f"⚡ Cache hits: {stats['cache_hits']}")
    print(f"❌ Fallos: {stats['failed_translations']}")
    print(f"⏱️ Tiempo promedio: {stats['avg_translation_time']:.3f}s")
    
    return success_count, total_translations

def test_language_detection():
    """Prueba la detección automática de idiomas."""
    print(f"\n🔍 PRUEBA DE DETECCIÓN DE IDIOMAS:")
    
    translator = TranslationService()
    
    test_texts = [
        ("Hola mundo", "es"),
        ("Hello world", "en"), 
        ("Привет мир", "ru"),
        ("你好世界", "zh"),
        ("مرحبا بالعالم", "ar")
    ]
    
    correct_detections = 0
    
    for text, expected_lang in test_texts:
        detected = translator._detect_language(text)
        is_correct = detected == expected_lang
        
        print(f"  📝 '{text}' -> {detected} {'✅' if is_correct else '❌'}")
        
        if is_correct:
            correct_detections += 1
    
    print(f"🎯 Detección correcta: {correct_detections}/{len(test_texts)}")
    return correct_detections, len(test_texts)

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DE TRADUCCIÓN GRATUITA")
    print("=" * 60)
    
    try:
        # Probar traducciones
        success, total = test_translations()
        
        # Probar detección de idiomas
        detection_success, detection_total = test_language_detection()
        
        print(f"\n🏆 RESUMEN FINAL:")
        print(f"🔄 Traducciones: {success}/{total} ({(success/total)*100:.1f}%)")
        print(f"🔍 Detección: {detection_success}/{detection_total} ({(detection_success/detection_total)*100:.1f}%)")
        
        if success > 0 and detection_success > 0:
            print(f"\n✅ ÉXITO: El sistema de traducción gratuita está funcionando!")
            print(f"💡 Ahora puedes usar traducciones sin API keys costosas.")
        else:
            print(f"\n⚠️ ADVERTENCIA: Algunas pruebas fallaron. Revisar configuración.")
            
    except ImportError as e:
        print(f"\n❌ ERROR: Dependencia faltante: {e}")
        print(f"💡 Ejecuta: pip install googletrans==4.0.0 langdetect")
        
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        
    print(f"\n🔚 Pruebas completadas.")
