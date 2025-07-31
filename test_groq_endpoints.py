#!/usr/bin/env python3
"""
Test directo de endpoints Groq sin iniciar la aplicación completa
"""
import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import requests
import time

def test_groq_endpoints():
    """Test de endpoints Groq"""
    print("🧪 Test de Endpoints Groq")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    base_url = "http://localhost:5000"
    
    # Esperar a que el servidor esté disponible
    print("⏳ Esperando que el servidor esté disponible...")
    for i in range(30):  # Esperar hasta 30 segundos
        try:
            response = requests.get(f"{base_url}/api/system/status", timeout=2)
            if response.status_code == 200:
                print("✅ Servidor disponible")
                break
        except:
            pass
        time.sleep(1)
        print(f"   Intentando... {i+1}/30")
    else:
        print("❌ Servidor no disponible después de 30 segundos")
        return
    
    # Test 1: Test básico de Groq
    print("\n1. Probando endpoint de test Groq...")
    try:
        response = requests.get(f"{base_url}/api/groq/test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Test exitoso: {data.get('message')}")
                print(f"   🤖 Respuesta: {data.get('test_response')}")
            else:
                print(f"   ❌ Test falló: {data.get('error')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Análisis Groq
    print("\n2. Probando endpoint de análisis Groq...")
    try:
        response = requests.get(f"{base_url}/api/groq/analysis", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                analysis = data.get('analysis', {})
                print(f"   ✅ Análisis generado exitosamente")
                print(f"   📝 Título: {analysis.get('title', 'N/A')}")
                print(f"   📊 Artículos analizados: {data.get('articles_count', 0)}")
                print(f"   📄 Contenido (preview): {str(analysis.get('content', ''))[:100]}...")
            else:
                print(f"   ❌ Análisis falló: {data.get('error')}")
                if data.get('fallback_analysis'):
                    print("   🔄 Análisis de respaldo disponible")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test de endpoints completado")

if __name__ == "__main__":
    test_groq_endpoints()
