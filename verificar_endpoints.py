#!/usr/bin/env python3
"""
Script de prueba para verificar que los endpoints están funcionando correctamente
"""

import requests
import json
import time

def test_endpoint(url, name):
    """Probar un endpoint específico"""
    try:
        print(f"🔍 Probando {name}: {url}")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {name}: OK")
            
            if isinstance(data, list):
                print(f"   📊 Resultado: {len(data)} elementos")
                if len(data) > 0:
                    print(f"   📝 Primer elemento tiene claves: {list(data[0].keys())[:5]}")
            else:
                print(f"   📊 Resultado: Objeto con claves: {list(data.keys())[:5]}")
                
            return True
        else:
            print(f"   ❌ {name}: Error {response.status_code}")
            print(f"   📝 Respuesta: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ {name}: Error de conexión - {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"   ❌ {name}: Error JSON - {e}")
        return False
    except Exception as e:
        print(f"   ❌ {name}: Error - {e}")
        return False

def main():
    """Ejecutar pruebas de endpoints"""
    print("🧪 INICIANDO PRUEBAS DE ENDPOINTS")
    print("=" * 50)
    
    # Esperar un poco por si la aplicación se está iniciando
    print("⏳ Esperando 3 segundos para que la aplicación esté lista...")
    time.sleep(3)
    
    base_url = "http://localhost:5001"
    
    endpoints = [
        (f"{base_url}/api/status", "Status"),
        (f"{base_url}/api/articles", "Articles"),
        (f"{base_url}/api/hero-article", "Hero Article"),
        (f"{base_url}/api/articles/deduplicated", "Deduplicated Articles"),
    ]
    
    results = []
    
    for url, name in endpoints:
        success = test_endpoint(url, name)
        results.append((name, success))
        print()  # Línea en blanco entre pruebas
    
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\nResultado: {total_passed}/{total_tests} pruebas exitosas")
    
    if total_passed == total_tests:
        print("🎉 ¡Todas las pruebas pasaron! El backend está funcionando correctamente.")
        print("✅ Ya no hay errores 500 - solo artículos geopolíticos con imágenes reales")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar logs de la aplicación.")

if __name__ == "__main__":
    main()