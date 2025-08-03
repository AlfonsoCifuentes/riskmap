#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demostración del Sistema de Fallback Inteligente
Muestra cómo el sistema maneja automáticamente los rate limits de Groq
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

def check_api_status():
    """Verificar si la API está corriendo"""
    try:
        response = requests.get('http://localhost:5000/api/system/status', timeout=5)
        return response.status_code == 200
    except:
        return False

def get_fallback_status():
    """Obtener estado del sistema de fallback"""
    try:
        response = requests.get('http://localhost:5000/api/ai/fallback-status', timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"❌ Error obteniendo estado: {e}")
        return None

def test_analysis_endpoints():
    """Probar diferentes endpoints de análisis"""
    
    test_content = """
    TÍTULO: Crisis diplomática en Europa Oriental
    CONTENIDO: Las tensiones han escalado significativamente en los últimos días. 
    Varios países han expresado preocupación por las acciones militares recientes.
    Los analistas sugieren que esto podría tener implicaciones regionales importantes.
    Las organizaciones internacionales están monitoreando la situación de cerca.
    """
    
    endpoints = [
        {
            'name': 'Análisis Rápido (Gemma)',
            'url': 'http://localhost:5000/api/ai/fast-summary',
            'data': {
                'title': 'Crisis diplomática en Europa Oriental',
                'content': test_content,
                'max_words': 100
            }
        },
        {
            'name': 'Análisis Profundo (DeepSeek)',
            'url': 'http://localhost:5000/api/ai/deep-analysis',
            'data': {
                'content': test_content,
                'question': '¿Cuáles son las implicaciones geopolíticas?'
            }
        },
        {
            'name': 'Análisis Unificado (Auto)',
            'url': 'http://localhost:5000/api/ai/unified-analysis',
            'data': {
                'content': test_content,
                'analysis_type': 'geopolitical'
            }
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n🧪 Probando: {endpoint['name']}")
        print("=" * 50)
        
        try:
            start_time = time.time()
            response = requests.post(
                endpoint['url'],
                json=endpoint['data'],
                timeout=30
            )
            end_time = time.time()
            
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Éxito en {duration:.2f}s")
                
                # Extraer información del proveedor usado
                if 'analysis' in result:
                    analysis = result['analysis']
                    provider = analysis.get('provider', 'unknown')
                    model = analysis.get('model', 'unknown')
                    print(f"🤖 Proveedor: {provider}")
                    print(f"📋 Modelo: {model}")
                    
                    # Mostrar contenido truncado
                    content = analysis.get('content', '')
                    if content:
                        content_preview = content[:150] + "..." if len(content) > 150 else content
                        print(f"📄 Resultado: {content_preview}")
                else:
                    provider = result.get('provider', 'unknown')
                    model = result.get('model', 'unknown')
                    print(f"🤖 Proveedor: {provider}")
                    print(f"📋 Modelo: {model}")
                
                results.append({
                    'endpoint': endpoint['name'],
                    'success': True,
                    'duration': duration,
                    'provider': provider,
                    'model': model
                })
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"📄 Respuesta: {response.text}")
                
                results.append({
                    'endpoint': endpoint['name'],
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'endpoint': endpoint['name'],
                'success': False,
                'error': str(e)
            })
    
    return results

def force_ollama_mode():
    """Forzar modo Ollama para demostración"""
    try:
        response = requests.post(
            'http://localhost:5000/api/ai/force-ollama-mode',
            json={'duration_minutes': 15},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            return True
        else:
            print(f"❌ Error forzando modo Ollama: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def restore_normal_mode():
    """Restaurar modo normal"""
    try:
        response = requests.post(
            'http://localhost:5000/api/ai/restore-normal-mode',
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            return True
        else:
            print(f"❌ Error restaurando modo: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def display_summary(results):
    """Mostrar resumen de resultados"""
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE PRUEBAS DEL SISTEMA DE FALLBACK")
    print(f"{'='*60}")
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"✅ Pruebas exitosas: {len(successful_tests)}/{len(results)}")
    print(f"❌ Pruebas fallidas: {len(failed_tests)}")
    
    if successful_tests:
        print(f"\n🎯 Proveedores utilizados:")
        providers = {}
        for result in successful_tests:
            provider = result.get('provider', 'unknown')
            if provider not in providers:
                providers[provider] = 0
            providers[provider] += 1
            
        for provider, count in providers.items():
            print(f"  - {provider}: {count} usos")
        
        avg_time = sum(r['duration'] for r in successful_tests) / len(successful_tests)
        print(f"\n⏱️  Tiempo promedio: {avg_time:.2f}s")
    
    print(f"\n💡 CONCLUSIONES:")
    
    ollama_used = any(r.get('provider', '').startswith('ollama') for r in successful_tests)
    groq_used = any(r.get('provider') == 'groq' for r in successful_tests)
    
    if ollama_used and not groq_used:
        print("  🎯 Sistema funcionando completamente con Ollama")
        print("  🚀 DeepSeek manejando análisis complejos")
        print("  ⚡ Gemma optimizando resúmenes rápidos")
        print("  🔄 Fallback automático exitoso")
    elif ollama_used and groq_used:
        print("  🔄 Sistema usando ambos proveedores balanceadamente")
        print("  📊 Fallback funcionando correctamente")
    elif groq_used and not ollama_used:
        print("  ☁️ Sistema usando principalmente Groq")
        print("  ⚠️ Ollama podría no estar disponible")
    else:
        print("  ❌ Problemas con ambos proveedores")

def main():
    """Función principal"""
    print("🚀 DEMOSTRACIÓN DEL SISTEMA DE FALLBACK INTELIGENTE")
    print("=" * 60)
    print("Este script demuestra cómo el sistema maneja automáticamente")
    print("los rate limits de Groq usando modelos locales de Ollama")
    print()
    
    # 1. Verificar que la API esté corriendo
    print("🔍 Verificando API del sistema...")
    if not check_api_status():
        print("❌ La API no está corriendo.")
        print("   Inicia el sistema con: python app_BUENA.py")
        return
    
    print("✅ API del sistema disponible")
    
    # 2. Mostrar estado inicial del fallback
    print("\n📊 Estado inicial del sistema:")
    print("-" * 40)
    status = get_fallback_status()
    
    if status and status.get('success'):
        service_status = status['service_status']
        print(f"  Ollama: {'✅' if service_status['ollama']['available'] else '❌'}")
        print(f"  Groq: {'✅' if service_status['groq']['available'] else '❌'}")
        
        models = status['models_status']
        print(f"  DeepSeek: {'✅' if models['deepseek_available'] else '❌'}")
        print(f"  Gemma: {'✅' if models['gemma_available'] else '❌'}")
        print(f"  Qwen: {'✅' if models['qwen_available'] else '❌'}")
        print(f"  Llama: {'✅' if models['llama_available'] else '❌'}")
        
        system_health = status['system_health']
        if system_health['rate_limits_detected']:
            print(f"  🔴 Rate limits detectados - Fallback activo")
        else:
            print(f"  🟢 Sin rate limits detectados")
    else:
        print("❌ No se pudo obtener estado del sistema")
    
    # 3. Opcionalmente forzar modo Ollama para demostrar
    print(f"\n{'='*60}")
    demo_mode = input("¿Forzar modo Ollama para demostración? (y/N): ")
    
    if demo_mode.lower() in ['y', 'yes', 's', 'si']:
        print("\n🔒 Forzando modo Ollama...")
        force_ollama_mode()
    
    # 4. Ejecutar pruebas de endpoints
    print(f"\n🧪 Ejecutando pruebas de análisis...")
    results = test_analysis_endpoints()
    
    # 5. Mostrar resumen
    display_summary(results)
    
    # 6. Restaurar modo normal si se forzó Ollama
    if demo_mode.lower() in ['y', 'yes', 's', 'si']:
        print(f"\n🔄 Restaurando modo normal...")
        restore_normal_mode()
    
    # 7. Estado final
    print(f"\n📊 Estado final del sistema:")
    print("-" * 40)
    final_status = get_fallback_status()
    
    if final_status and final_status.get('success'):
        recent_activity = final_status['recent_activity']
        print(f"  Artículos enriquecidos (10 min): {recent_activity['articles_enriched_10min']}")
        print(f"  Total artículos enriquecidos: {recent_activity['total_articles_enriched']}")
    
    print(f"\n✅ Demostración completada")
    print("💡 El sistema está configurado para manejar automáticamente")
    print("   los rate limits usando los modelos locales especializados")

if __name__ == "__main__":
    main()
