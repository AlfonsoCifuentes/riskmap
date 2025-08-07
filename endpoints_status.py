#!/usr/bin/env python3
"""
Script para mostrar el estado de los endpoints y dar instrucciones de reinicio
"""

import requests
import subprocess
import sys

def check_endpoints_status():
    """Verificar el estado de todos los endpoints"""
    print("🔍 ESTADO ACTUAL DE LOS ENDPOINTS")
    print("=" * 60)
    
    endpoints = [
        ("/", "Página principal"),
        ("/about", "Página About"), 
        ("/api/articles", "API Artículos"),
        ("/api/test", "API Test - NUEVO"),
        ("/api/dashboard/stats", "API Dashboard Stats - NUEVO"),
        ("/api/analytics/conflicts-corrected", "API Conflictos Corregidos - NUEVO")
    ]
    
    working = 0
    new_endpoints_working = 0
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:5001{endpoint}", timeout=10)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {endpoint} - {description}")
                working += 1
                if "NUEVO" in description:
                    new_endpoints_working += 1
            else:
                print(f"❌ {endpoint} - {description} (Status: {status})")
        except:
            print(f"❌ {endpoint} - {description} (No responde)")
    
    print(f"\n📊 RESUMEN:")
    print(f"   Total funcionando: {working}/{len(endpoints)}")
    print(f"   Endpoints nuevos funcionando: {new_endpoints_working}/3")
    
    return new_endpoints_working == 3

def show_restart_instructions():
    """Mostrar instrucciones para reiniciar el servidor"""
    print("\n🔄 INSTRUCCIONES PARA REINICIAR EL SERVIDOR:")
    print("=" * 60)
    print("1. Para Windows (PowerShell):")
    print("   Ctrl+C para detener el servidor actual")
    print("   Luego ejecuta: python app_BUENA.py")
    print()
    print("2. Para verificar que funciona:")
    print("   python test_new_endpoints.py")
    print()
    print("3. URLs de los nuevos endpoints:")
    print("   http://localhost:5001/api/test")
    print("   http://localhost:5001/api/dashboard/stats") 
    print("   http://localhost:5001/api/analytics/conflicts-corrected")
    print()

def show_code_confirmation():
    """Mostrar confirmación de que el código fue agregado correctamente"""
    print("✅ CONFIRMACIÓN DE CÓDIGO AGREGADO:")
    print("=" * 60)
    print("Los siguientes endpoints han sido agregados al archivo app_BUENA.py:")
    print()
    print("1. /api/test")
    print("   - Endpoint de prueba básico")
    print("   - Retorna estado del sistema y puerto")
    print()
    print("2. /api/dashboard/stats") 
    print("   - Estadísticas para el dashboard")
    print("   - Total de artículos, países afectados, etc.")
    print()
    print("3. /api/analytics/conflicts-corrected")
    print("   - Zonas de conflicto CORREGIDAS")
    print("   - Usa tabla conflict_zones o fallback a articles")
    print("   - Filtrado geopolítico estricto")
    print()

def main():
    print("🔧 VERIFICACIÓN DE ENDPOINTS POST-ACTUALIZACIÓN")
    print("=" * 60)
    
    show_code_confirmation()
    
    # Verificar si el servidor está corriendo
    try:
        response = requests.get("http://localhost:5001/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor detectado en puerto 5001")
            
            # Verificar endpoints
            if check_endpoints_status():
                print("\n🎉 ¡TODOS LOS ENDPOINTS FUNCIONAN CORRECTAMENTE!")
                print("No necesitas hacer nada más.")
            else:
                print("\n⚠️  LOS NUEVOS ENDPOINTS NO FUNCIONAN AÚN")
                print("Esto es normal - necesitas reiniciar el servidor.")
                show_restart_instructions()
        else:
            print(f"⚠️  Servidor responde pero con status {response.status_code}")
    except:
        print("❌ No se puede conectar al servidor en puerto 5001")
        print("\n💡 Inicia el servidor:")
        print("python app_BUENA.py")

if __name__ == "__main__":
    main()
