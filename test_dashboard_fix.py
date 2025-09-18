#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TEST RÁPIDO DE CORRECCIÓN DE DASHBOARDS
==========================================
Probar rápidamente si la corrección de dashboards funciona
"""

import requests
import time

def test_dashboard_routes():
    """Probar las rutas de dashboard"""
    print("🧪 TESTANDO CORRECCIÓN DE DASHBOARDS")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    
    routes_to_test = [
        ("/dashboard", "Dashboard Principal"),
        ("/multivariate", "Dashboard Multivariable"), 
        ("/dash/historical/", "Dash Histórico"),
        ("/dash/multivariate/", "Dash Multivariable")
    ]
    
    results = []
    
    for route, name in routes_to_test:
        print(f"\n🔍 Testing: {name} ({route})")
        try:
            response = requests.get(f"{base_url}{route}", timeout=10, allow_redirects=True)
            status = response.status_code
            size = len(response.content)
            
            if status == 200:
                print(f"   ✅ Status: {status} - Size: {size} bytes")
                results.append((route, "SUCCESS", status, size))
            else:
                print(f"   ❌ Status: {status} - Size: {size} bytes")
                results.append((route, "FAILED", status, size))
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout")
            results.append((route, "TIMEOUT", 0, 0))
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection Error")
            results.append((route, "CONNECTION_ERROR", 0, 0))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((route, "ERROR", 0, 0))
    
    # Resumen
    print(f"\n📊 RESUMEN DE RESULTADOS:")
    print("-" * 40)
    
    successful = [r for r in results if r[1] == "SUCCESS"]
    failed = [r for r in results if r[1] != "SUCCESS"]
    
    print(f"✅ Exitosas: {len(successful)}/{len(results)}")
    print(f"❌ Fallidas: {len(failed)}/{len(results)}")
    
    if successful:
        print("\n✅ RUTAS FUNCIONANDO:")
        for route, status, code, size in successful:
            print(f"   • {route} ({code} - {size} bytes)")
            
    if failed:
        print("\n❌ RUTAS CON PROBLEMAS:")
        for route, status, code, size in failed:
            print(f"   • {route} ({status})")
    
    # Análisis específico
    print(f"\n🎯 ANÁLISIS:")
    
    dashboard_redirect = next((r for r in results if r[0] == "/dashboard"), None)
    multivariate_redirect = next((r for r in results if r[0] == "/multivariate"), None)
    
    if dashboard_redirect and dashboard_redirect[1] == "SUCCESS":
        print("   ✅ Redirección /dashboard funciona")
    else:
        print("   ❌ Redirección /dashboard falla")
        
    if multivariate_redirect and multivariate_redirect[1] == "SUCCESS":
        print("   ✅ Redirección /multivariate funciona")
    else:
        print("   ❌ Redirección /multivariate falla")
    
    dash_historical = next((r for r in results if r[0] == "/dash/historical/"), None)
    dash_multivariate = next((r for r in results if r[0] == "/dash/multivariate/"), None)
    
    if dash_historical and dash_historical[1] == "SUCCESS":
        print("   ✅ Dashboard histórico Dash funciona")
    else:
        print("   ❌ Dashboard histórico Dash requiere reinicio del servidor")
        
    if dash_multivariate and dash_multivariate[1] == "SUCCESS":
        print("   ✅ Dashboard multivariable Dash funciona") 
    else:
        print("   ❌ Dashboard multivariable Dash requiere reinicio del servidor")
    
    return results

def main():
    results = test_dashboard_routes()
    
    print(f"\n💡 RECOMENDACIÓN:")
    print("=" * 30)
    
    # Verificar si hay rutas Dash que fallan
    dash_routes = [r for r in results if r[0].startswith("/dash/")]
    failing_dash = [r for r in dash_routes if r[1] != "SUCCESS"]
    
    if failing_dash:
        print("🔄 REINICIAR SERVIDOR para aplicar correcciones de Dash")
        print("   Las modificaciones en app_BUENA.py requieren reinicio")
    else:
        print("✅ Todas las correcciones aplicadas exitosamente")
        print("   No se requiere reinicio del servidor")

if __name__ == "__main__":
    main()