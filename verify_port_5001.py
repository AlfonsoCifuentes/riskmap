#!/usr/bin/env python3
"""
Script para verificar que el servidor esté funcionando correctamente en puerto 5001
"""

import requests
import time
import sys

def test_endpoints():
    """Testear endpoints principales en puerto 5001"""
    base_url = "http://localhost:5001"
    
    endpoints_to_test = [
        "/",
        "/api/test",
        "/api/dashboard/stats",
        "/api/analytics/conflicts-corrected",
        "/api/articles",
        "/about"
    ]
    
    print("🔍 Verificando endpoints en puerto 5001...")
    print("=" * 50)
    
    results = {}
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{base_url}{endpoint}"
            print(f"🌐 Probando: {url}")
            
            response = requests.get(url, timeout=10)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {endpoint}: OK (200)")
                results[endpoint] = "OK"
            else:
                print(f"⚠️  {endpoint}: {status}")
                results[endpoint] = f"HTTP {status}"
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: No se puede conectar (¿servidor corriendo?)")
            results[endpoint] = "Connection Error"
        except requests.exceptions.Timeout:
            print(f"⏰ {endpoint}: Timeout")
            results[endpoint] = "Timeout"
        except Exception as e:
            print(f"💥 {endpoint}: Error - {e}")
            results[endpoint] = f"Error: {e}"
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE RESULTADOS:")
    print("=" * 50)
    
    working_endpoints = 0
    
    for endpoint, result in results.items():
        if result == "OK":
            print(f"✅ {endpoint}")
            working_endpoints += 1
        else:
            print(f"❌ {endpoint} - {result}")
    
    print(f"\n📈 Total funcionando: {working_endpoints}/{len(endpoints_to_test)}")
    
    if working_endpoints == len(endpoints_to_test):
        print("🎉 ¡Todos los endpoints funcionan correctamente en puerto 5001!")
    elif working_endpoints == 0:
        print("🚨 NINGÚN endpoint responde. ¿Está corriendo el servidor?")
        print("\n💡 Para iniciar el servidor:")
        print("   python app_BUENA.py")
    else:
        print("⚠️  Algunos endpoints no responden correctamente.")
    
    return results

def test_frontend_config():
    """Verificar configuración del frontend"""
    print("\n🔧 Verificando configuración del frontend...")
    print("=" * 50)
    
    try:
        config_path = "src/web/static/js/riskmap-config.js"
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "5001" in content:
            print("✅ Configuración frontend actualizada para puerto 5001")
        else:
            print("⚠️  Configuración frontend no incluye puerto 5001")
            
        if "window.location.port === '5001'" in content:
            print("✅ Detección automática de puerto configurada")
        else:
            print("⚠️  Detección automática de puerto no configurada")
            
    except FileNotFoundError:
        print("❌ Archivo de configuración frontend no encontrado")
    except Exception as e:
        print(f"💥 Error leyendo configuración: {e}")

def main():
    """Función principal"""
    print("🔧 VERIFICACIÓN DE PUERTO 5001")
    print("=" * 50)
    
    # Verificar configuración frontend
    test_frontend_config()
    
    # Esperar un momento
    time.sleep(1)
    
    # Testear endpoints
    results = test_endpoints()
    
    # Instrucciones finales
    print("\n💡 INSTRUCCIONES:")
    print("=" * 50)
    print("1. Asegúrate de que el servidor esté corriendo:")
    print("   python app_BUENA.py")
    print()
    print("2. Accede al dashboard en:")
    print("   http://localhost:5001")
    print()
    print("3. Prueba el endpoint corregido:")
    print("   http://localhost:5001/api/analytics/conflicts-corrected")
    print()

if __name__ == "__main__":
    main()
