#!/usr/bin/env python3
"""
Test final de cache - probar el endpoint con timeout muy corto
"""

import requests
import time

def test_instant_response():
    """Probar respuesta instantánea"""
    
    print("🧪 Probando respuesta instantánea del endpoint...")
    
    try:
        url = "http://localhost:8050/api/analytics/conflicts"
        
        start_time = time.time()
        response = requests.get(url, timeout=3)  # Solo 3 segundos
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱️ Tiempo de respuesta: {duration:.2f} segundos")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                conflicts = data.get('conflicts', [])
                analysis_type = data.get('analysis_type', 'unknown')
                cache_used = data.get('cache_used', False)
                
                print(f"✅ Respuesta exitosa!")
                print(f"📊 Conflictos: {len(conflicts)}")
                print(f"📊 Tipo de análisis: {analysis_type}")
                print(f"📊 Cache usado: {cache_used}")
                print(f"⚡ Respuesta {'INSTANTÁNEA' if duration < 1.0 else 'LENTA'}")
                
                if duration < 1.0:
                    print("🎉 ¡CACHE FUNCIONANDO!")
                else:
                    print("❌ Todavía muy lento")
                
                # Mostrar algunos conflictos
                for i, conflict in enumerate(conflicts[:3]):
                    location = conflict.get('location', 'N/A')
                    risk = conflict.get('risk_level', 'N/A')
                    conf = conflict.get('confidence', 0)
                    print(f"   {i+1}. {location}: {risk} (conf: {conf:.2f})")
                
                return duration < 1.0
            else:
                print(f"❌ Error en respuesta: {data}")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - El endpoint aún tarda más de 3 segundos")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test final de velocidad de respuesta...")
    
    success = test_instant_response()
    
    if success:
        print("\n🎉 ¡ÉXITO! El endpoint está funcionando instantáneamente")
        print("✅ Cache funcionando correctamente")
        print("✅ Respuesta en menos de 1 segundo")
    else:
        print("\n❌ El endpoint aún no está optimizado")
        print("💡 Recomendación: Revisar la lógica del cache")
