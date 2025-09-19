#!/usr/bin/env python3
"""
Script de prueba para verificar la integración de Groq
"""

import os
import json
import requests
from dotenv import load_dotenv

def test_groq_configuration():
    """Prueba la configuración de Groq"""
    print("🧪 PRUEBA DE CONFIGURACIÓN GROQ")
    print("=" * 40)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar API key
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        print("❌ GROQ_API_KEY no encontrada en archivo .env")
        return False
    
    print(f"✅ GROQ_API_KEY encontrada: {groq_api_key[:20]}...")
    
    # Verificar que groq esté instalado
    try:
        from groq import Groq
        print("✅ Biblioteca Groq instalada correctamente")
    except ImportError:
        print("❌ Biblioteca Groq no instalada. Ejecuta: pip install groq")
        return False
    
    # Probar conexión con Groq
    try:
        client = Groq(api_key=groq_api_key)
        
        # Prueba simple
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente que responde en formato JSON."
                },
                {
                    "role": "user", 
                    "content": "Responde con un JSON que contenga: {\"status\": \"ok\", \"message\": \"Prueba exitosa\"}"
                }
            ],
            model="llama-3.1-8b-instant",  # Modelo actualizado
            temperature=0.1,
            max_tokens=100
        )
        
        result = response.choices[0].message.content
        print(f"✅ Conexión con Groq exitosa")
        print(f"📝 Respuesta: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando con Groq: {e}")
        return False

def test_groq_analysis():
    """
    Prueba la funcionalidad de análisis geopolítico
    """
    print("🧪 Iniciando prueba del análisis geopolítico con Groq\n")
    
    # Datos de prueba
    test_articles = [
        {
            "title": "Escalada militar en conflicto internacional",
            "content": "Las tensiones militares han aumentado significativamente en la región con movilización de tropas",
            "location": "Europa Oriental",
            "risk_level": "high",
            "risk_score": 0.85,
            "country": "Ukraine",
            "importance": 90
        },
        {
            "title": "Amenaza nuclear en Asia Pacific aumenta tensiones",
            "content": "Expertos en seguridad expresan preocupación por el desarrollo de armas nucleares en la región",
            "location": "Asia Pacific", 
            "risk_level": "critical",
            "risk_score": 0.95,
            "country": "Multiple",
            "importance": 95
        }
    ]
    
    # URL del endpoint
    url = "http://localhost:5003/api/generate-ai-analysis"
    
    # Payload
    payload = {
        "articles": test_articles,
        "analysis_type": "geopolitical_journalistic",
        "language": "spanish"
    }
    
    try:
        print("📡 Enviando petición al servidor...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            print("✅ Respuesta exitosa del servidor")
            data = response.json()
            
            print(f"\n📰 TITULAR: {data.get('title', 'N/A')}")
            print(f"📝 SUBTÍTULO: {data.get('subtitle', 'N/A')}")
            print(f"📊 FUENTES: {data.get('sources_count', 'N/A')}")
            print(f"📅 FECHA: {data.get('analysis_date', 'N/A')}")
            
            content = data.get('content', '')
            if content:
                print(f"\n📄 CONTENIDO (primeros 200 caracteres):")
                print(content[:200] + "..." if len(content) > 200 else content)
            
            print("\n✅ Prueba completada exitosamente")
            
        else:
            print(f"❌ Error del servidor: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print("💡 Asegúrate de que el servidor esté ejecutándose en localhost:5003")
        print("   Ejecuta: python app_bert_fixed.py")
        
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout - El servidor tardó demasiado en responder")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def check_environment():
    """
    Verifica la configuración del entorno
    """
    print("🔍 Verificando configuración del entorno...\n")
    
    # Verificar API Key de Groq
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        print(f"✅ GROQ_API_KEY configurada: {groq_key[:20]}...")
    else:
        print("⚠️  GROQ_API_KEY no encontrada")
        print("💡 Para configurarla:")
        print("   PowerShell: $env:GROQ_API_KEY = 'tu_api_key'")
        print("   CMD: set GROQ_API_KEY=tu_api_key")
        print("   Bash: export GROQ_API_KEY='tu_api_key'")
    
    # Verificar dependencias
    try:
        import groq
        print("✅ Librería Groq instalada")
    except ImportError:
        print("❌ Librería Groq no encontrada")
        print("💡 Para instalarla: pip install groq")
    
    try:
        import flask
        print("✅ Flask instalado")
    except ImportError:
        print("❌ Flask no encontrado")
        print("💡 Para instalarlo: pip install flask")
    
    print()

def main():
    """
    Función principal
    """
    print("=" * 60)
    print("🧠 PRUEBA DE ANÁLISIS GEOPOLÍTICO CON GROQ")
    print("=" * 60)
    print()
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Paso 1: Verificar configuración
    config_ok = test_groq_configuration()
    
    if not config_ok:
        print("\n⚠️ La configuración de Groq falló. No se puede continuar.")
        print("🔧 Revisa la API key y las dependencias.")
        return
    
    print("\n" + "=" * 40)
    
    # Paso 2: Probar análisis vía servidor (si está disponible)
    print("🌐 Probando análisis vía servidor Flask...")
    test_groq_analysis()
    
    print("\n" + "=" * 60)
    print("🏁 Prueba finalizada")
    print("💡 Si todo funcionó, puedes ejecutar: python app_bert_fixed.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
