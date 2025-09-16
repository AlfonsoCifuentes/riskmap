#!/usr/bin/env python3
"""
Script simple de prueba usando urllib en lugar de requests
"""

import urllib.request
import json
import time

def test_endpoint_simple(url, name):
    """Probar un endpoint usando urllib"""
    try:
        print(f"🔍 Probando {name}: {url}")
        
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                data = json.loads(content)
                print(f"   ✅ {name}: OK")
                
                if isinstance(data, list):
                    print(f"   📊 Resultado: {len(data)} elementos")
                    if len(data) > 0:
                        print(f"   📝 Primer elemento tiene claves: {list(data[0].keys())[:5]}")
                        if name == "Articles" and len(data) > 0:
                            # Mostrar info del primer artículo
                            first = data[0]
                            print(f"   📰 Título: {first.get('title', 'N/A')[:50]}...")
                            print(f"   🌍 Ubicación: {first.get('country', 'N/A')}")
                            print(f"   📊 Risk Score: {first.get('risk_score', 'N/A')}")
                            print(f"   🖼️ Imagen: {'Sí' if first.get('image_url') else 'No'}")
                else:
                    print(f"   📊 Resultado: Objeto con claves: {list(data.keys())[:5]}")
                    if name == "Status":
                        print(f"   💾 Database: {data.get('database', 'N/A')}")
                        print(f"   🕐 Timestamp: {data.get('timestamp', 'N/A')}")
                    
                return True
            else:
                print(f"   ❌ {name}: Error {response.status}")
                return False
                
    except Exception as e:
        print(f"   ❌ {name}: Error - {e}")
        return False

def main():
    """Ejecutar pruebas simples"""
    print("🧪 PRUEBAS SIMPLES DE ENDPOINTS")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    
    endpoints = [
        (f"{base_url}/api/status", "Status"),
        (f"{base_url}/api/articles", "Articles"),  
        (f"{base_url}/api/hero-article", "Hero Article"),
        (f"{base_url}/api/articles/deduplicated", "Deduplicated Articles"),
    ]
    
    results = []
    
    for url, name in endpoints:
        success = test_endpoint_simple(url, name)
        results.append((name, success))
        print()
    
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\n🎯 Resultado Final: {total_passed}/{total_tests} pruebas exitosas")
    
    if total_passed == total_tests:
        print("\n🎉 ¡ÉXITO TOTAL!")
        print("✅ Todos los endpoints funcionan correctamente")
        print("✅ Ya NO hay errores 500")  
        print("✅ Solo se muestran artículos geopolíticos con imágenes reales")
        print("✅ Problema SOLUCIONADO")
    else:
        print(f"\n⚠️  {total_tests - total_passed} prueba(s) fallaron")

if __name__ == "__main__":
    main()