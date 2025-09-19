#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el sistema de fallback inteligente
Verifica que Ollama tome el control cuando Groq tiene rate limits
"""

import os
import sys
import logging
import time
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from src.ai.unified_ai_service import unified_ai_service
from src.ai.ollama_service import ollama_service
from src.ai.intelligent_fallback import get_fallback_stats, enhance_article_with_fallback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ollama_availability():
    """Verificar que Ollama esté funcionando"""
    print("🧪 Probando disponibilidad de Ollama...")
    
    status = ollama_service.check_ollama_status()
    print(f"📊 Ollama disponible: {status}")
    
    if status:
        models = ollama_service.get_available_models()
        print(f"🤖 Modelos disponibles: {len(models)}")
        for model in models:
            print(f"  - {model.get('name', 'Unknown')}")
    
    return status

def test_unified_service():
    """Probar el servicio unificado"""
    print("\n🧪 Probando servicio unificado...")
    
    status = unified_ai_service.get_service_status()
    print(f"📊 Estado del servicio:")
    print(f"  - Ollama: {status['ollama']['available']}")
    print(f"  - Groq: {status['groq']['available']}")
    print(f"  - Proveedor preferido: {status['preferred_provider']}")
    
    # Capacidades especializadas
    capabilities = status['capabilities']
    print(f"🎯 Capacidades especializadas:")
    print(f"  - Razonamiento profundo (DeepSeek): {capabilities['deep_reasoning']}")
    print(f"  - Procesamiento rápido (Gemma): {capabilities['fast_processing']}")
    print(f"  - Multiidioma (Qwen): {capabilities['multilingual']}")
    print(f"  - Propósito general (Llama): {capabilities['general_purpose']}")

def test_analysis_with_fallback():
    """Probar análisis con fallback automático"""
    print("\n🧪 Probando análisis con fallback...")
    
    test_content = """
    TÍTULO: Tensiones geopolíticas en Europa Oriental
    CONTENIDO: Las recientes decisiones militares han aumentado las tensiones en la región. 
    Varios países han expresado preocupación por la escalada del conflicto. 
    Los líderes internacionales buscan soluciones diplomáticas mientras se mantiene la vigilancia militar.
    """
    
    print("🔄 Iniciando análisis...")
    start_time = time.time()
    
    try:
        # Usar el servicio unificado (preferirá Ollama para evitar rate limits)
        import asyncio
        response = asyncio.run(unified_ai_service.analyze_geopolitical_content(
            content=test_content,
            prefer_local=True
        ))
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Análisis completado en {duration:.2f}s")
        print(f"🤖 Proveedor usado: {response.provider}")
        print(f"📋 Modelo: {response.model}")
        print(f"✨ Éxito: {response.success}")
        
        if response.success:
            print(f"📄 Resumen: {response.content[:200]}...")
            if response.metadata:
                print(f"🎯 Metadata disponible: {list(response.metadata.keys())}")
        else:
            print(f"❌ Error: {response.error}")
            
    except Exception as e:
        print(f"❌ Error en análisis: {e}")

def test_summary_generation():
    """Probar generación de resúmenes"""
    print("\n🧪 Probando generación de resúmenes...")
    
    title = "Crisis diplomática internacional"
    content = """
    La situación diplomática se ha complicado tras las declaraciones del ministro.
    Varios embajadores han sido convocados para explicaciones.
    La comunidad internacional observa con preocupación estos desarrollos.
    Se espera una respuesta coordinada en las próximas horas.
    """
    
    print("🔄 Generando resumen...")
    start_time = time.time()
    
    try:
        # Probar resumen rápido (debería usar Gemma)
        response = unified_ai_service.generate_fast_summary(
            title=title,
            content=content,
            max_words=100
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Resumen generado en {duration:.2f}s")
        print(f"🤖 Proveedor: {response.provider}")
        print(f"📋 Modelo: {response.model}")
        print(f"📄 Resumen: {response.content}")
        
    except Exception as e:
        print(f"❌ Error generando resumen: {e}")

def test_deep_analysis():
    """Probar análisis profundo con DeepSeek"""
    print("\n🧪 Probando análisis profundo...")
    
    content = """
    La nueva alianza militar representa un cambio significativo en el equilibrio de poder regional.
    Los analistas sugieren que esto podría tener implicaciones de largo plazo para la estabilidad.
    """
    
    question = "¿Cuáles son las implicaciones geopolíticas de esta nueva alianza?"
    
    print("🔄 Realizando análisis profundo...")
    start_time = time.time()
    
    try:
        import asyncio
        response = asyncio.run(unified_ai_service.perform_deep_analysis(
            content=content,
            question=question
        ))
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Análisis profundo completado en {duration:.2f}s")
        print(f"🤖 Proveedor: {response.provider}")
        print(f"📋 Modelo: {response.model}")
        print(f"🧠 Conclusión: {response.content}")
        
        if response.metadata:
            confidence = response.metadata.get('confidence', 0)
            print(f"🎯 Confianza: {confidence:.2f}")
        
    except Exception as e:
        print(f"❌ Error en análisis profundo: {e}")

def test_fallback_stats():
    """Mostrar estadísticas de fallback"""
    print("\n📊 Estadísticas de fallback:")
    
    try:
        stats = get_fallback_stats()
        
        print(f"  - Total requests Groq: {stats['total_groq_requests']}")
        print(f"  - Rate limits Groq: {stats['groq_rate_limits']}")
        print(f"  - Fallbacks Ollama: {stats['ollama_fallbacks']}")
        print(f"  - Tasa éxito Groq: {stats['groq_success_rate']}%")
        print(f"  - Recomendación: {stats['recommended_action']}")
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas del sistema de fallback inteligente")
    print("=" * 60)
    
    # 1. Verificar Ollama
    ollama_ok = test_ollama_availability()
    
    if not ollama_ok:
        print("❌ Ollama no disponible. Instalarlo con: python install_ollama.py")
        return
    
    # 2. Estado del servicio unificado
    test_unified_service()
    
    # 3. Pruebas de funcionalidad
    test_analysis_with_fallback()
    test_summary_generation()
    test_deep_analysis()
    
    # 4. Estadísticas
    test_fallback_stats()
    
    print("\n✅ Pruebas completadas")
    print("💡 El sistema debería usar automáticamente Ollama cuando Groq tenga rate limits")

if __name__ == "__main__":
    main()
