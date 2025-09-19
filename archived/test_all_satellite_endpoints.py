#!/usr/bin/env python3
"""Script para probar todos los endpoints de análisis satelital."""

import requests
import json
import time

def test_all_satellite_endpoints():
    """Probar todos los endpoints de análisis satelital."""
    base_url = "http://localhost:8050"
    
    endpoints = [
        "/api/satellite/statistics",
        "/api/satellite/trigger-analysis", 
        "/api/satellite/gallery-images",
        "/api/satellite/critical-alerts",
        "/api/satellite/analysis-timeline",
        "/api/satellite/evolution-predictions"
    ]
    
    print("🛰️ PROBANDO TODOS LOS ENDPOINTS DE ANÁLISIS SATELITAL")
    print("=" * 70)
    
    for endpoint in endpoints:
        print(f"\n🚀 Probando {endpoint}...")
        try:
            if endpoint == "/api/satellite/trigger-analysis":
                # POST request for trigger
                response = requests.post(f"{base_url}{endpoint}", timeout=10)
            else:
                # GET request for others
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success'):
                        print(f"   ✅ Éxito")
                        
                        # Mostrar algunos detalles específicos
                        if 'statistics' in data or 'stats' in data:
                            stats = data.get('stats', data.get('statistics', {}))
                            print(f"   📊 Estadísticas: {stats}")
                        elif 'images' in data:
                            print(f"   🖼️ Imágenes encontradas: {len(data['images'])}")
                        elif 'alerts' in data:
                            print(f"   ⚠️ Alertas encontradas: {len(data['alerts'])}")
                        elif 'timeline' in data:
                            print(f"   📅 Eventos en timeline: {len(data['timeline'])}")
                        elif 'analysis_id' in data:
                            print(f"   🆔 Analysis ID: {data['analysis_id']}")
                            # Probar progress endpoint
                            progress_url = f"{base_url}/api/satellite/analysis-progress/{data['analysis_id']}"
                            try:
                                progress_response = requests.get(progress_url, timeout=5)
                                if progress_response.status_code == 200:
                                    progress_data = progress_response.json()
                                    print(f"   📈 Progreso: {progress_data.get('progress', 0)}%")
                            except:
                                print("   ⚠️ No se pudo obtener progreso")
                    else:
                        print(f"   ❌ Error en respuesta: {data.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    print(f"   ❌ Respuesta no es JSON válido")
                    print(f"   📄 Contenido: {response.text[:200]}...")
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📄 Error: {error_data.get('error', 'No error message')}")
                except:
                    print(f"   📄 Contenido: {response.text[:200]}...")
                    
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Error de conexión: Backend no disponible")
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout: El endpoint tardó más de 10 segundos")
        except Exception as e:
            print(f"   ❌ Error inesperado: {str(e)}")
    
    print(f"\n{'='*70}")
    print("🏁 PRUEBAS COMPLETADAS")

if __name__ == "__main__":
    # Esperar a que el backend inicie
    print("⏳ Esperando a que el backend inicie...")
    time.sleep(15)
    
    test_all_satellite_endpoints()

def test_endpoint(endpoint, method="GET", data=None):
    """Probar un endpoint específico."""
    try:
        print(f"\n🔍 Testing {method} {endpoint}...")
        
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"   ✅ Success: {json_data.get('success', 'N/A')}")
                if 'message' in json_data:
                    print(f"   📝 Message: {json_data['message']}")
                if 'total' in json_data:
                    print(f"   📊 Total items: {json_data['total']}")
                if 'analysis_id' in json_data:
                    print(f"   🆔 Analysis ID: {json_data['analysis_id']}")
                return json_data
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response")
                print(f"   📄 Response: {response.text[:200]}...")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}...")
        
        return None
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection error - backend not running?")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_all_satellite_endpoints():
    """Probar todos los endpoints de análisis satelital."""
    print("🛰️ TESTING ALL SATELLITE ANALYSIS ENDPOINTS")
    print("=" * 60)
    
    # Test estadísticas
    test_endpoint("/api/satellite/statistics")
    
    # Test galería de imágenes
    test_endpoint("/api/satellite/gallery-images")
    
    # Test alertas críticas
    test_endpoint("/api/satellite/critical-alerts")
    
    # Test línea de tiempo
    test_endpoint("/api/satellite/analysis-timeline")
    
    # Test predicciones de evolución
    test_endpoint("/api/satellite/evolution-predictions")
    
    # Test detecciones recientes
    test_endpoint("/api/satellite/recent-detections")
    
    # Test feed en tiempo real
    test_endpoint("/api/satellite/real-time-feed")
    
    # Test trigger de análisis
    trigger_data = test_endpoint("/api/satellite/trigger-analysis", "POST", {})
    
    # Si se obtuvo un analysis_id, probar el progreso
    if trigger_data and 'analysis_id' in trigger_data:
        analysis_id = trigger_data['analysis_id']
        time.sleep(1)  # Esperar un momento
        test_endpoint(f"/api/satellite/analysis-progress/{analysis_id}")
    
    print("\n🎯 SATELLITE ENDPOINTS TEST COMPLETED")
    print("=" * 60)

def test_basic_endpoints():
    """Probar endpoints básicos para verificar que el backend funciona."""
    print("\n🔧 TESTING BASIC ENDPOINTS")
    print("=" * 40)
    
    # Test endpoint básico
    test_endpoint("/api/statistics")
    
    # Test artículos
    test_endpoint("/api/articles?limit=5")
    
    # Test análisis de conflictos
    test_endpoint("/api/analytics/conflicts")

if __name__ == "__main__":
    print(f"🚀 Starting satellite endpoints test at {datetime.now()}")
    
    # Esperar un poco para que el backend se inicie
    print("⏳ Waiting for backend to start...")
    time.sleep(15)
    
    # Probar endpoints básicos primero
    test_basic_endpoints()
    
    # Probar todos los endpoints satelitales
    test_all_satellite_endpoints()
    
    print(f"\n✅ Test completed at {datetime.now()}")
