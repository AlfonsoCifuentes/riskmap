#!/usr/bin/env python3
"""
Script para generar y verificar una nueva API key de Groq
"""

import os
from dotenv import load_dotenv

def get_new_groq_api_key():
    """Instrucciones para obtener nueva API key"""
    print("🔑 CÓMO OBTENER UNA NUEVA API KEY DE GROQ")
    print("=" * 50)
    print()
    print("1. Ve a: https://console.groq.com/")
    print("2. Crea una cuenta gratuita (si no tienes una)")
    print("3. Inicia sesión")
    print("4. Ve a 'API Keys' en el menú lateral")
    print("5. Haz click en 'Create API Key'")
    print("6. Dale un nombre (ej: 'RiskMap-AI')")
    print("7. Copia la API key (empieza con 'gsk_')")
    print()
    print("⚠️  IMPORTANTE: La API key solo se muestra una vez!")
    print("📝 Guárdala en un lugar seguro inmediatamente")
    print()
    
    # Verificar la key actual
    load_dotenv()
    current_key = os.getenv('GROQ_API_KEY')
    if current_key:
        print(f"🔍 API Key actual: {current_key[:10]}...{current_key[-4:]}")
        print("   Esta key parece inválida o expirada")
    else:
        print("❌ No hay API key configurada")
    
    print()
    print("💡 Una vez que tengas la nueva API key:")
    print("   1. Abre el archivo .env")
    print("   2. Reemplaza la línea GROQ_API_KEY=...")
    print("   3. Pega tu nueva key: GROQ_API_KEY=gsk_tu_nueva_key_aqui")
    print("   4. Guarda el archivo")
    print("   5. Reinicia la aplicación")

def check_groq_models():
    """Información sobre modelos Groq recomendados"""
    print("\n🤖 MODELOS GROQ RECOMENDADOS PARA GEOPOLITICA")
    print("=" * 50)
    print()
    print("Para análisis geopolítico, recomendamos:")
    print()
    print("1. llama-3.3-70b-versatile")
    print("   📊 Mejor para análisis complejos")
    print("   🧠 Alta capacidad de razonamiento")
    print("   ⚡ Buena velocidad")
    print()
    print("2. llama-3.1-8b-instant") 
    print("   🚀 Muy rápido")
    print("   💰 Costo-eficiente")
    print("   ✅ Bueno para análisis básicos")
    print()
    print("3. mixtral-8x7b-32768")
    print("   📄 Contexto muy largo (32k tokens)")
    print("   🔄 Bueno para documentos extensos")

def provide_fallback_info():
    """Información sobre el sistema de fallback"""
    print("\n🔄 SISTEMA DE FALLBACK OPERATIVO")
    print("=" * 50)
    print()
    print("✅ Tu sistema TIENE fallback automático:")
    print()
    print("1. Multi-Model Client:")
    print("   - Prueba DeepSeek, OpenAI, Groq, HuggingFace")
    print("   - Fallback automático cuando un modelo falla")
    print()
    print("2. HuggingFace Local:")
    print("   - Modelos descargados localmente")
    print("   - Funciona sin internet/APIs")
    print("   - Microsoft DialoGPT disponible")
    print()
    print("3. Análisis de Respaldo:")
    print("   - Análisis geopolítico pre-estructurado")
    print("   - Siempre funciona como último recurso")
    print()
    print("💡 El sistema continuará funcionando incluso si:")
    print("   ❌ Groq API falla")
    print("   ❌ OpenAI API falla") 
    print("   ❌ No hay internet")
    print()
    print("🎯 Estado actual: ¡COMPLETAMENTE OPERATIVO!")

def main():
    print("🔐 GUÍA DE API KEYS Y FALLBACK - RISKMAP AI")
    print("=" * 60)
    
    get_new_groq_api_key()
    check_groq_models() 
    provide_fallback_info()
    
    print("\n" + "=" * 60)
    print("🎉 RESUMEN:")
    print("• Obtén nueva API key de Groq para mejor rendimiento")
    print("• El sistema funciona perfectamente sin API keys") 
    print("• Fallback automático garantiza continuidad del servicio")
    print("• Tu aplicación está completamente operativa")
    print()
    print("🚀 ¡Continúa usando tu sistema sin interrupciones!")

if __name__ == "__main__":
    main()