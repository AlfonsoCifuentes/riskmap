#!/usr/bin/env python3
"""
Script para testear los endpoints específicos que acabamos de agregar
"""

import requests
import json
import time

def test_specific_endpoints():
    """Testear solo los endpoints que acabamos de agregar"""
    base_url = "http://localhost:5001"
    
    endpoints_to_test = [
        "/api/test",
        "/api/dashboard/stats", 
        "/api/analytics/conflicts-corrected"
    ]
    
    print("🔍 Testando endpoints recién agregados...")
    print("=" * 60)
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n🌐 Probando: {url}")
            
            response = requests.get(url, timeout=15)
            status = response.status_code
            
            print(f"📊 Status: {status}")
            
            if status == 200:
                data = response.json()
                print(f"✅ Respuesta exitosa:")
                if endpoint == "/api/test":
                    print(f"   - Mensaje: {data.get('message')}")
                    print(f"   - Puerto: {data.get('server_port')}")
                    print(f"   - Sistema: {data.get('system_status')}")
                elif endpoint == "/api/dashboard/stats":
                    stats = data.get('stats', {})
                    print(f"   - Total artículos: {stats.get('total_articles')}")
                    print(f"   - Alto riesgo: {stats.get('high_risk_articles')}")
                    print(f"   - Países afectados: {stats.get('countries_affected')}")
                elif endpoint == "/api/analytics/conflicts-corrected":
                    print(f"   - Zonas de conflicto: {data.get('statistics', {}).get('total_zones')}")
                    print(f"   - Fuente de datos: {data.get('statistics', {}).get('data_source')}")
                    print(f"   - Timeframe: {data.get('statistics', {}).get('timeframe')}")
                    
            elif status == 404:
                print(f"❌ Error 404: Endpoint no encontrado")
                print("   ⚠️  Es posible que necesites reiniciar el servidor")
            elif status == 500:
                try:
                    error_data = response.json()
                    print(f"💥 Error 500: {error_data.get('error')}")
                except:
                    print(f"💥 Error 500: Error interno del servidor")
            else:
                print(f"⚠️  Status inesperado: {status}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ No se puede conectar al servidor")
            print(f"   💡 ¿Está corriendo en puerto 5001?")
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout - el servidor tardó mucho en responder")
        except Exception as e:
            print(f"💥 Error inesperado: {e}")
    
    print("\n" + "=" * 60)
    print("💡 DIAGNÓSTICO:")
    print("Si los endpoints devuelven 404:")
    print("1. Verifica que el servidor esté corriendo: python app_BUENA.py")
    print("2. Si ya está corriendo, reinícialo para cargar los nuevos endpoints")
    print("3. Los endpoints están en la función _setup_flask_routes()")
    print("\nSi funcionan correctamente:")
    print("✅ Los endpoints han sido agregados exitosamente")

def check_server_running():
    """Verificar si el servidor está corriendo"""
    try:
        response = requests.get("http://localhost:5001/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor corriendo en puerto 5001")
            return True
        else:
            print(f"⚠️  Servidor responde pero con status {response.status_code}")
            return False
    except:
        print("❌ Servidor no responde en puerto 5001")
        return False

def main():
    print("🔧 TEST DE ENDPOINTS ESPECÍFICOS")
    print("=" * 60)
    
    # Verificar servidor
    if check_server_running():
        test_specific_endpoints()
    else:
        print("\n💡 INICIA EL SERVIDOR:")
        print("python app_BUENA.py")

if __name__ == "__main__":
    main()
