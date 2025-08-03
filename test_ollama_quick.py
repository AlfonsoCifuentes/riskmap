#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rápido del sistema de IA unificado con Ollama
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

def test_ollama_integration():
    """Probar integración con Ollama"""
    print("🧪 Probando integración con Ollama...")
    
    try:
        from src.ai.ollama_service import ollama_service, OllamaModel
        
        # Verificar estado
        status = ollama_service.check_ollama_status()
        print(f"📊 Ollama disponible: {status}")
        
        if not status:
            print("❌ Ollama no está corriendo. Inicia con: ollama serve")
            return False
            
        # Listar modelos
        models = ollama_service.get_available_models()
        print(f"🤖 Modelos disponibles: {len(models)}")
        
        specialized_models = {
            'deepseek': False,
            'gemma': False, 
            'qwen': False,
            'llama': False
        }
        
        for model in models:
            name = model.get('name', '').lower()
            print(f"  - {model.get('name', 'Unknown')}")
            
            if 'deepseek' in name:
                specialized_models['deepseek'] = True
            elif 'gemma' in name:
                specialized_models['gemma'] = True
            elif 'qwen' in name:
                specialized_models['qwen'] = True
            elif 'llama' in name:
                specialized_models['llama'] = True
        
        print(f"\n🎯 Modelos especializados disponibles:")
        print(f"  - DeepSeek (análisis profundo): {'✅' if specialized_models['deepseek'] else '❌'}")
        print(f"  - Gemma (resúmenes rápidos): {'✅' if specialized_models['gemma'] else '❌'}")
        print(f"  - Qwen (multiidioma): {'✅' if specialized_models['qwen'] else '❌'}")
        print(f"  - Llama (propósito general): {'✅' if specialized_models['llama'] else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando Ollama: {e}")
        return False

def test_unified_service():
    """Probar servicio unificado"""
    print("\n🧪 Probando servicio unificado...")
    
    try:
        from src.ai.unified_ai_service import unified_ai_service
        
        # Obtener estado
        status = unified_ai_service.get_service_status()
        
        print(f"📊 Estado general:")
        print(f"  - Ollama: {'✅' if status['ollama']['available'] else '❌'}")
        print(f"  - Groq: {'✅' if status['groq']['available'] else '❌'}")
        print(f"  - Proveedor preferido: {status['preferred_provider']}")
        
        capabilities = status['capabilities']
        print(f"\n🚀 Capacidades avanzadas:")
        print(f"  - Razonamiento profundo: {'✅' if capabilities['deep_reasoning'] else '❌'}")
        print(f"  - Procesamiento rápido: {'✅' if capabilities['fast_processing'] else '❌'}")
        print(f"  - Soporte multiidioma: {'✅' if capabilities['multilingual'] else '❌'}")
        print(f"  - IA de propósito general: {'✅' if capabilities['general_purpose'] else '❌'}")
        
        return status['ollama']['available']
        
    except Exception as e:
        print(f"❌ Error probando servicio unificado: {e}")
        return False

def test_simple_analysis():
    """Probar análisis simple con Ollama"""
    print("\n🧪 Probando análisis simple...")
    
    try:
        from src.ai.ollama_service import ollama_service, OllamaModel
        
        test_content = "Escalada de tensiones diplomáticas entre países vecinos por disputas territoriales"
        
        print("🔄 Ejecutando análisis con DeepSeek...")
        
        # Análisis con DeepSeek
        result = ollama_service.analyze_geopolitical_content(
            content=test_content,
            model=OllamaModel.DEEPSEEK_R1_7B
        )
        
        if result:
            print("✅ Análisis completado")
            print(f"📄 Resumen: {result.get('summary', 'N/A')[:150]}...")
            print(f"🎯 Nivel de riesgo: {result.get('risk_level', 'N/A')}")
            print(f"📊 Relevancia geopolítica: {result.get('geopolitical_relevance', 'N/A')}")
        else:
            print("❌ No se pudo completar el análisis")
            
        return bool(result)
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        return False

def test_summary_generation():
    """Probar generación de resúmenes"""
    print("\n🧪 Probando generación de resúmenes...")
    
    try:
        from src.ai.ollama_service import ollama_service, OllamaModel
        
        title = "Crisis económica global"
        content = """
        Los mercados financieros mundiales han experimentado una volatilidad significativa.
        Los bancos centrales están considerando medidas de emergencia.
        Los indicadores económicos sugieren una desaceleración generalizada.
        Las empresas reportan dificultades en las cadenas de suministro.
        """
        
        print("🔄 Generando resumen con Gemma...")
        
        # Resumen con Gemma (rápido)
        summary = ollama_service.generate_lightweight_summary(
            title=title,
            content=content,
            model=OllamaModel.GEMMA2_2B
        )
        
        if summary and "error" not in summary.lower():
            print("✅ Resumen generado")
            print(f"📄 Resumen: {summary}")
        else:
            print(f"❌ Error generando resumen: {summary}")
            
        return bool(summary and "error" not in summary.lower())
        
    except Exception as e:
        print(f"❌ Error generando resumen: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Test Rápido del Sistema de IA Unificado")
    print("=" * 50)
    
    # 1. Probar Ollama
    ollama_ok = test_ollama_integration()
    
    if not ollama_ok:
        print("\n❌ Ollama no disponible. Asegúrate de que esté corriendo:")
        print("   - ollama serve")
        print("   - python install_ollama.py")
        return
    
    # 2. Probar servicio unificado
    unified_ok = test_unified_service()
    
    # 3. Probar funcionalidades
    if unified_ok:
        analysis_ok = test_simple_analysis()
        summary_ok = test_summary_generation()
        
        print(f"\n{'='*50}")
        print("📊 Resumen de Pruebas:")
        print(f"  - Ollama: {'✅' if ollama_ok else '❌'}")
        print(f"  - Servicio unificado: {'✅' if unified_ok else '❌'}")
        print(f"  - Análisis geopolítico: {'✅' if analysis_ok else '❌'}")
        print(f"  - Generación de resúmenes: {'✅' if summary_ok else '❌'}")
        
        if all([ollama_ok, unified_ok, analysis_ok, summary_ok]):
            print("\n🎉 ¡Sistema completamente funcional!")
            print("💡 El sistema puede manejar automáticamente los rate limits de Groq")
            print("🤖 Usando DeepSeek, Gemma, Qwen y Llama según la tarea")
        else:
            print("\n⚠️ Algunas funcionalidades no están disponibles")
    
    print(f"\n✅ Test completado")

if __name__ == "__main__":
    main()
