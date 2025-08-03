#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la integración de Ollama con DeepSeek-R1 y Gemma
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ai.ollama_service import ollama_service, OllamaModel
from src.ai.unified_ai_service import unified_ai_service

async def test_ollama_integration():
    """
    Prueba completa de la integración de Ollama
    """
    print("🚀 INICIANDO PRUEBAS DE INTEGRACIÓN OLLAMA")
    print("=" * 60)
    
    # 1. Verificar estado de Ollama
    print("1️⃣ Verificando estado de Ollama...")
    ollama_running = ollama_service.check_ollama_status()
    print(f"   Ollama ejecutándose: {'✅' if ollama_running else '❌'}")
    
    if not ollama_running:
        print("❌ Ollama no está ejecutándose. Por favor, inicia Ollama primero.")
        return False
    
    # 2. Obtener modelos disponibles
    print("\n2️⃣ Verificando modelos disponibles...")
    available_models = ollama_service.get_available_models()
    model_names = [model.get('name', '') for model in available_models]
    
    print(f"   Total de modelos: {len(available_models)}")
    for model in model_names[:5]:  # Mostrar primeros 5
        print(f"   📦 {model}")
    
    if len(available_models) > 5:
        print(f"   ... y {len(available_models) - 5} más")
    
    # 3. Verificar modelos específicos
    print("\n3️⃣ Verificando modelos especializados...")
    target_models = {
        'DeepSeek-R1': ['deepseek-r1:7b', 'deepseek-r1:1.5b'],
        'Gemma': ['gemma2:2b', 'gemma2:9b'],
        'Qwen': ['qwen:7b', 'qwen2.5-coder:7b'],
        'Llama': ['llama3.1:8b', 'llama3:8b']
    }
    
    available_specialized = {}
    for category, models in target_models.items():
        found = [model for model in models if model in model_names]
        available_specialized[category] = found
        status = '✅' if found else '❌'
        print(f"   {status} {category}: {found if found else 'No disponible'}")
    
    # 4. Probar servicio unificado
    print("\n4️⃣ Probando servicio unificado...")
    service_status = unified_ai_service.get_service_status()
    
    print(f"   Ollama disponible: {'✅' if service_status['ollama']['available'] else '❌'}")
    print(f"   Groq disponible: {'✅' if service_status['groq']['available'] else '❌'}")
    print(f"   Proveedor preferido: {service_status['preferred_provider']}")
    
    capabilities = service_status.get('capabilities', {})
    print(f"   🧠 Razonamiento profundo: {'✅' if capabilities.get('deep_reasoning') else '❌'}")
    print(f"   ⚡ Procesamiento rápido: {'✅' if capabilities.get('fast_processing') else '❌'}")
    print(f"   🌍 Multiidioma: {'✅' if capabilities.get('multilingual') else '❌'}")
    
    # 5. Pruebas funcionales
    print("\n5️⃣ Ejecutando pruebas funcionales...")
    
    test_content = """
    Ucrania ha solicitado oficialmente el ingreso a la OTAN, lo que ha generado 
    tensiones con Rusia. El presidente Putin ha declarado que esto constituye 
    una amenaza directa a la seguridad nacional rusa y ha movilizado tropas 
    hacia la frontera occidental.
    """
    
    # Prueba 1: Análisis estándar
    try:
        print("   🧪 Probando análisis geopolítico...")
        response = await unified_ai_service.analyze_geopolitical_content(
            content=test_content,
            prefer_local=True
        )
        
        if response.success:
            print(f"   ✅ Análisis exitoso con {response.provider} ({response.model})")
            print(f"      Resumen: {response.content[:100]}...")
        else:
            print(f"   ❌ Error en análisis: {response.error}")
    except Exception as e:
        print(f"   ❌ Excepción en análisis: {e}")
    
    # Prueba 2: Resumen rápido (si Gemma está disponible)
    if available_specialized.get('Gemma'):
        try:
            print("   🧪 Probando resumen rápido con Gemma...")
            response = unified_ai_service.generate_fast_summary(
                title="Tensiones OTAN-Rusia",
                content=test_content,
                max_words=50
            )
            
            if response.success:
                print(f"   ✅ Resumen rápido exitoso con {response.provider}")
                print(f"      Resumen: {response.content}")
            else:
                print(f"   ❌ Error en resumen: {response.error}")
        except Exception as e:
            print(f"   ❌ Excepción en resumen: {e}")
    
    # Prueba 3: Análisis profundo (si DeepSeek está disponible)
    if available_specialized.get('DeepSeek-R1'):
        try:
            print("   🧪 Probando análisis profundo con DeepSeek-R1...")
            response = await unified_ai_service.perform_deep_analysis(
                content=test_content,
                question="¿Cuáles son las implicaciones geopolíticas de esta situación?"
            )
            
            if response.success:
                print(f"   ✅ Análisis profundo exitoso")
                print(f"      Conclusión: {response.content[:100]}...")
                if response.metadata:
                    confidence = response.metadata.get('confidence', 'N/A')
                    print(f"      Confianza: {confidence}")
            else:
                print(f"   ❌ Error en análisis profundo: {response.error}")
        except Exception as e:
            print(f"   ❌ Excepción en análisis profundo: {e}")
    
    # 6. Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    total_models = len(available_models)
    specialized_count = sum(len(models) for models in available_specialized.values())
    
    print(f"✅ Ollama: {'Funcionando' if ollama_running else 'No disponible'}")
    print(f"📦 Modelos totales: {total_models}")
    print(f"🎯 Modelos especializados: {specialized_count}")
    print(f"🔧 Servicio unificado: {'Funcionando' if service_status['ollama']['available'] else 'Error'}")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    
    if not available_specialized.get('DeepSeek-R1'):
        print("   📥 Instalar DeepSeek-R1 para análisis profundo: ollama pull deepseek-r1:7b")
    
    if not available_specialized.get('Gemma'):
        print("   📥 Instalar Gemma para procesamiento rápido: ollama pull gemma2:2b")
    
    if total_models < 3:
        print("   📥 Se recomienda instalar más modelos para mayor versatilidad")
    
    if ollama_running and total_models >= 3:
        print("   🎉 Sistema listo para producción!")
    
    return ollama_running and total_models >= 1

def test_model_specific_features():
    """
    Probar características específicas de cada modelo
    """
    print("\n🔬 PRUEBAS ESPECÍFICAS POR MODELO")
    print("=" * 60)
    
    # Prueba con Qwen (si está disponible)
    available_models = [model.get('name', '') for model in ollama_service.get_available_models()]
    
    if 'qwen:7b' in available_models:
        print("1️⃣ Probando Qwen 7B...")
        try:
            response = ollama_service.generate_completion(
                prompt="Explica en español las relaciones geopolíticas entre China y Estados Unidos",
                model=OllamaModel.QWEN_7B,
                max_tokens=200
            )
            
            if response:
                print(f"   ✅ Qwen respuesta: {response[:150]}...")
            else:
                print("   ❌ Qwen no respondió")
        except Exception as e:
            print(f"   ❌ Error con Qwen: {e}")
    
    # Prueba con Gemma (si está disponible)
    if 'gemma2:2b' in available_models:
        print("\n2️⃣ Probando Gemma 2B...")
        try:
            response = ollama_service.generate_lightweight_summary(
                title="Prueba Gemma",
                content="Este es un texto de prueba para verificar que Gemma puede generar resúmenes rápidos y eficientes.",
                model=OllamaModel.GEMMA2_2B
            )
            
            if response and "error" not in response.lower():
                print(f"   ✅ Gemma resumen: {response}")
            else:
                print("   ❌ Gemma falló")
        except Exception as e:
            print(f"   ❌ Error con Gemma: {e}")
    
    # Prueba con DeepSeek-R1 (si está disponible)
    if 'deepseek-r1:7b' in available_models:
        print("\n3️⃣ Probando DeepSeek-R1...")
        try:
            response = ollama_service.perform_deep_reasoning(
                question="¿Cuál es la importancia de la IA en la geopolítica moderna?",
                context="La inteligencia artificial está transformando el panorama geopolítico global.",
                model=OllamaModel.DEEPSEEK_R1_7B
            )
            
            if response and response.get('confidence', 0) > 0:
                print(f"   ✅ DeepSeek razonamiento exitoso")
                print(f"      Confianza: {response.get('confidence', 'N/A')}")
                print(f"      Conclusión: {response.get('conclusion', 'N/A')[:100]}...")
            else:
                print("   ❌ DeepSeek falló")
        except Exception as e:
            print(f"   ❌ Error con DeepSeek: {e}")

async def main():
    """
    Función principal de pruebas
    """
    print("🧪 SUITE DE PRUEBAS - OLLAMA + DEEPSEEK-R1 + GEMMA")
    print("=" * 70)
    
    try:
        # Pruebas principales
        success = await test_ollama_integration()
        
        if success:
            # Pruebas específicas
            test_model_specific_features()
            
            print("\n" + "=" * 70)
            print("🎉 PRUEBAS COMPLETADAS EXITOSAMENTE")
            print("   El sistema Ollama está listo para usar con RiskMap")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("❌ PRUEBAS FALLARON")
            print("   Revisa la instalación de Ollama y los modelos")
            print("=" * 70)
    
    except Exception as e:
        print(f"\n❌ Error inesperado en las pruebas: {e}")

if __name__ == "__main__":
    # Ejecutar pruebas
    asyncio.run(main())
