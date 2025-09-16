#!/usr/bin/env python3
"""
Verificador de versión del servidor
"""
import requests
import json
from datetime import datetime

def check_server_methods():
    """Verifica qué métodos están disponibles en el servidor corriente"""
    
    print("🔍 VERIFICANDO VERSIÓN DEL SERVIDOR")
    print("=" * 60)
    
    # Probar endpoint de status personalizado para verificar versión
    try:
        print("🧪 Probando endpoint /api/status...")
        response = requests.get("http://localhost:5001/api/status", timeout=10)
        
        if response.status_code == 200:
            print("✅ Endpoint /api/status DISPONIBLE")
            data = response.json()
            print(f"📊 Status: {data.get('status', 'unknown')}")
            print(f"🕒 Timestamp: {data.get('timestamp', 'unknown')}")
            print("🔄 SERVIDOR EJECUTANDO VERSIÓN ACTUALIZADA (app_BUENA.py)")
        elif response.status_code == 404:
            print("❌ Endpoint /api/status NO DISPONIBLE (404)")
            print("🔄 SERVIDOR EJECUTANDO VERSIÓN ANTERIOR")
        else:
            print(f"❌ Endpoint /api/status error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error conectando a servidor: {e}")
    
    # Probar algunos endpoints para ver errores específicos
    endpoints_to_test = [
        "/api/articles?limit=1",
        "/api/hero-article"
    ]
    
    print("\n🧪 PROBANDO ENDPOINTS PRINCIPALES:")
    print("-" * 40)
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\n🔍 Probando {endpoint}...")
            response = requests.get(f"http://localhost:5001{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK")
                data = response.json()
                if 'articles' in data and data['articles']:
                    print(f"📰 Artículos retornados: {len(data['articles'])}")
                elif 'article' in data:
                    print("📰 Artículo principal disponible")
                    
            elif response.status_code == 500:
                print(f"❌ {endpoint}: ERROR 500")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Sin detalles de error')
                    print(f"💥 Error: {error_msg}")
                    
                    if "_get_real_articles_from_db" in error_msg:
                        print("🔍 PROBLEMA: Método _get_real_articles_from_db no existe")
                        print("💡 SOLUCIÓN: Reiniciar servidor con versión actualizada")
                        
                except:
                    print("💥 Error parsing JSON response")
                    
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error en {endpoint}: {e}")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE DIAGNÓSTICO")
    print("=" * 60)
    
    try:
        # Verificar disponibilidad de endpoint status
        status_response = requests.get("http://localhost:5001/api/status", timeout=5)
        if status_response.status_code == 200:
            print("✅ Servidor ejecutando VERSIÓN ACTUALIZADA")
            print("🔄 Cambios aplicados correctamente")
        else:
            print("❌ Servidor ejecutando VERSIÓN ANTERIOR")
            print("🔄 NECESITA REINICIAR para aplicar cambios")
            
    except:
        print("❌ No se pudo verificar versión del servidor")
    
    print(f"\n🕒 Verificación completada: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    check_server_methods()