#!/usr/bin/env python3
"""
Test simple y directo de los endpoints problemáticos
"""

import requests
import json
from datetime import datetime

def test_endpoints():
    """Test de endpoints críticos"""
    print("🔍 DIAGNÓSTICO DE ENDPOINTS FRONTEND")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    
    # Endpoints críticos
    endpoints_to_test = [
        ("/api/articles", "Artículos normales"),
        ("/api/articles/deduplicated?hours=24", "Artículos deduplicados"),
        ("/api/hero-article", "Artículo hero"),
        ("/favicon.ico", "Favicon"),
        ("/static/favicon.ico", "Favicon estático")
    ]
    
    for endpoint, description in endpoints_to_test:
        test_single_endpoint(base_url + endpoint, description)
    
    # Test específico del problema reportado
    print("\n" + "🚨 DIAGNÓSTICO ESPECÍFICO DEL ERROR REPORTADO" + "🚨")
    print("-" * 60)
    
    # Test artículos deduplicados
    try:
        print("📞 Llamando /api/articles/deduplicated...")
        response = requests.get(f"{base_url}/api/articles/deduplicated?hours=24", timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            
            if data.get('success'):
                mosaic = data.get('mosaic', [])
                print(f"📰 Artículos en mosaico: {len(mosaic)}")
                
                if len(mosaic) == 0:
                    print("⚠️ El mosaico está vacío - esto explica el error")
                    print("Mensaje: 'No hay artículos deduplicados disponibles'")
                
                # Ver el error específico
                error_msg = data.get('error', '')
                if error_msg:
                    print(f"❌ Error en respuesta: {error_msg}")
                    
            else:
                print(f"❌ Success=false: {data.get('error', 'No error message')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

def test_single_endpoint(url, description):
    """Test un endpoint individual"""
    print(f"\n🔍 {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"Content-Type: {content_type}")
            
            if 'json' in content_type:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"JSON keys: {list(data.keys())}")
                        if 'success' in data:
                            print(f"Success: {data['success']}")
                        if 'error' in data:
                            print(f"Error: {data['error']}")
                    print("✅ JSON válido")
                except Exception as e:
                    print(f"❌ JSON inválido: {e}")
            else:
                size = len(response.content)
                print(f"Content size: {size} bytes")
                if size > 0:
                    print("✅ Contenido recibido")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT")
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR - ¿Está corriendo la aplicación en puerto 5001?")
    except Exception as e:
        print(f"💥 ERROR: {e}")

def check_application_status():
    """Verificar si la aplicación está corriendo"""
    print("\n🔍 VERIFICANDO ESTADO DE LA APLICACIÓN")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:5001/", timeout=5)
        if response.status_code == 200:
            print("✅ Aplicación respondiendo en puerto 5001")
            return True
        else:
            print(f"⚠️ Aplicación responde con código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No hay aplicación corriendo en puerto 5001")
        return False
    except Exception as e:
        print(f"❌ Error verificando aplicación: {e}")
        return False

def main():
    print("🚀 DIAGNÓSTICO DE PROBLEMAS FRONTEND")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Verificar que la app esté corriendo
    if not check_application_status():
        print("\n❌ La aplicación no está corriendo.")
        print("💡 Para solucionar:")
        print("   1. Ejecuta: python app_BUENA.py")
        print("   2. Espera a que inicie completamente")
        print("   3. Vuelve a ejecutar este test")
        return
    
    # Ejecutar tests
    test_endpoints()
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO:")
    print("• Si hay errores 404 en favicon: necesitas crear/copiar favicon.ico")
    print("• Si 'No hay artículos deduplicados': el sistema de deduplicación")
    print("  no encuentra artículos que cumplan criterios específicos")
    print("• Esto es normal si tienes pocos artículos o todos son similares")
    print("• La aplicación debería usar fallback automáticamente")
    
    print("\n🔧 POSIBLES SOLUCIONES:")
    print("1. Crear favicon.ico en static/")
    print("2. Verificar que hay artículos en la base de datos")
    print("3. Ajustar criterios de deduplicación si es necesario")
    print("4. Verificar que el JavaScript maneja correctamente los fallbacks")

if __name__ == "__main__":
    main()