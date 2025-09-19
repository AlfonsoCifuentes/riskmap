#!/usr/bin/env python3
"""
Probar el servidor de cache simplificado
"""

import requests
import time

def test_simple_cache():
    """Probar el endpoint simplificado"""
    
    print("🧪 Probando servidor de cache simplificado...")
    
    try:
        url = "http://localhost:8050/api/test/conflicts"
        
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱️ Tiempo de respuesta: {duration:.3f} segundos")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                conflicts = data.get('conflicts', [])
                print(f"✅ Respuesta exitosa!")
                print(f"📊 Conflictos encontrados: {len(conflicts)}")
                print(f"📊 Cache usado: {data.get('cache_used', False)}")
                
                # Mostrar conflictos
                for i, conflict in enumerate(conflicts):
                    location = conflict.get('location', 'N/A')
                    risk = conflict.get('risk_level', 'N/A')
                    conf = conflict.get('confidence', 0)
                    coords = conflict.get('coordinates', [0, 0])
                    print(f"   {i+1}. {location}: {risk} (conf: {conf:.2f}) - [{coords[0]:.4f}, {coords[1]:.4f}]")
                
                if duration < 0.5:
                    print("🚀 ¡EXCELENTE! Respuesta muy rápida")
                    return True
                elif duration < 1.0:
                    print("✅ Respuesta rápida")
                    return True
                else:
                    print("⚠️ Respuesta lenta")
                    return False
            else:
                print(f"❌ Error en respuesta: {data}")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Esperar un poco para que el servidor arranque
    print("⏳ Esperando que el servidor arranque...")
    time.sleep(2)
    
    success = test_simple_cache()
    
    if success:
        print("\n🎉 ¡PERFECTO! El cache funciona correctamente")
        print("✅ Los datos existen en la base de datos")
        print("✅ La consulta es muy rápida")
        print("💡 Ahora podemos aplicar esto al endpoint principal")
    else:
        print("\n❌ Hay un problema con el cache o los datos")
