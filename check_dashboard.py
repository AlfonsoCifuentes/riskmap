#!/usr/bin/env python3
"""
Script para verificar que el dashboard está funcionando correctamente
"""
import requests
import time
import sys

def check_dashboard():
    """Verificar que el dashboard responde correctamente"""
    base_url = "http://localhost:8081"
    
    endpoints_to_check = [
        "/",
        "/events",
        "/risk_json",
        "/keywords_json",
        "/static/css/modern_dashboard.css",
        "/favicon.ico"
    ]
    
    print("🔍 Verificando el estado del dashboard...")
    print(f"📍 URL base: {base_url}")
    print("-" * 50)
    
    all_ok = True
    
    for endpoint in endpoints_to_check:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            status = "✅ OK" if response.status_code == 200 else f"❌ Error {response.status_code}"
            print(f"{endpoint:<30} {status}")
            
            if response.status_code != 200:
                all_ok = False
                
        except requests.exceptions.ConnectionError:
            print(f"{endpoint:<30} ❌ No se puede conectar")
            all_ok = False
        except requests.exceptions.Timeout:
            print(f"{endpoint:<30} ❌ Timeout")
            all_ok = False
        except Exception as e:
            print(f"{endpoint:<30} ❌ Error: {e}")
            all_ok = False
    
    print("-" * 50)
    
    if all_ok:
        print("🎉 ¡Dashboard funcionando correctamente!")
        print(f"🌐 Accede a: {base_url}")
    else:
        print("⚠️  Algunos endpoints tienen problemas")
        print("💡 Verifica que el dashboard esté ejecutándose en el puerto 8081")
    
    return all_ok

if __name__ == "__main__":
    # Esperar un poco para que el servidor se inicie
    print("⏳ Esperando que el dashboard se inicie...")
    time.sleep(3)
    
    success = check_dashboard()
    sys.exit(0 if success else 1)