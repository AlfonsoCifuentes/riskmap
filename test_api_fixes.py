#!/usr/bin/env python3
"""
Script de prueba para validar las correcciones de los errores reportados
"""

import requests
import json
import time

def test_analytics_conflicts():
    """Prueba el endpoint /api/analytics/conflicts"""
    print("\n🔍 Probando /api/analytics/conflicts...")
    
    try:
        response = requests.get('http://localhost:5001/api/analytics/conflicts', timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint funcionando correctamente")
            print(f"📊 Conflictos encontrados: {len(data.get('conflicts', []))}")
            print(f"📈 Estadísticas: {data.get('statistics', {})}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return False

def test_translation_api():
    """Prueba el endpoint de traducción"""
    print("\n🔍 Probando /api/translate...")
    
    test_text = "This is a test article about conflicts"
    data = {
        "text": test_text,
        "target_language": "es"
    }
    
    try:
        response = requests.post('http://localhost:5001/api/translate', 
                               json=data, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Endpoint de traducción funcionando")
            print(f"📝 Texto original: {test_text}")
            print(f"📝 Texto traducido: {result.get('translated_text', 'N/A')}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return False

def test_main_dashboard():
    """Prueba que el dashboard principal cargue"""
    print("\n🔍 Probando dashboard principal...")
    
    try:
        response = requests.get('http://localhost:5001/', timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard principal cargando correctamente")
            # Verificar que el HTML contenga las funciones que arreglamos
            html_content = response.text
            if 'applyComputerVisionToMosaic' in html_content:
                print("✅ Función applyComputerVisionToMosaic presente")
            if 'JSON.stringify' in html_content:
                print("✅ Corrección de JSON.stringify aplicada")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return False

def main():
    print("🧪 INICIANDO PRUEBAS DE CORRECCIONES DE ERRORES")
    print("=" * 50)
    
    # Esperar a que el servidor esté listo
    print("⏳ Esperando a que el servidor esté listo...")
    time.sleep(10)
    
    # Probar endpoints
    results = []
    
    results.append(test_main_dashboard())
    results.append(test_analytics_conflicts())
    results.append(test_translation_api())
    
    # Resumen
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE PRUEBAS:")
    print(f"✅ Pruebas exitosas: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 ¡Todas las correcciones funcionando correctamente!")
    else:
        print("⚠️ Algunas pruebas fallaron, revisar logs del servidor")

if __name__ == "__main__":
    main()
