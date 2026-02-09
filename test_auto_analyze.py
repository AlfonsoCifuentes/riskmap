#!/usr/bin/env python3
"""
Script de prueba para el endpoint automático de análisis satelital
"""
import requests
import json
import time

def test_auto_analyze_endpoint():
    """Probar el endpoint automático de análisis satelital"""
    try:
        print("🚀 Probando endpoint automático de análisis satelital...")
        print("📡 Enviando solicitud POST a /api/satellite/auto-analyze")

        # URL del endpoint
        url = "http://localhost:5001/api/satellite/auto-analyze"

        # Headers
        headers = {
            'Content-Type': 'application/json'
        }

        # Enviar solicitud POST
        start_time = time.time()
        response = requests.post(url, headers=headers, timeout=300)  # 5 minutos timeout
        end_time = time.time()

        print(f"⏱️  Tiempo de respuesta: {end_time - start_time:.2f} segundos")
        print(f"📊 Status Code: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Respuesta exitosa!")
                print("📈 Estadísticas del análisis:")
                print(f"   • Artículos analizados: {data.get('articles_analyzed', 0)}")
                print(f"   • Zonas de conflicto encontradas: {data.get('conflict_zones_found', 0)}")
                print(f"   • Coincidencias GDELT: {data.get('gdelt_matches', 0)}")
                print(f"   • Imágenes satelitales generadas: {data.get('satellite_images_generated', 0)}")
                print(f"   • Detecciones YOLO aplicadas: {data.get('yolo_detections_applied', 0)}")

                # Verificar galerías
                galleries = data.get('galleries', {})
                satellite_images = galleries.get('satellite_images', [])
                detections = galleries.get('detections', [])

                print("
🛰️  Galería de imágenes satelitales:"                print(f"   • {len(satellite_images)} imágenes disponibles")

                print("
🎯 Galería de detecciones YOLO:"                print(f"   • {len(detections)} detecciones disponibles")

                if detections:
                    print("   📋 Top detecciones:")
                    for i, det in enumerate(detections[:3]):  # Mostrar top 3
                        print(f"      {i+1}. {det.get('region', 'Unknown')} - {det.get('total_detections', 0)} objetos detectados")

                return True

            except json.JSONDecodeError as e:
                print(f"❌ Error parseando respuesta JSON: {e}")
                print(f"📄 Respuesta cruda: {response.text[:500]}...")
                return False

        else:
            print(f"❌ Error HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Error message: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"📄 Respuesta cruda: {response.text[:500]}...")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión - ¿Está corriendo el servidor en localhost:5001?")
        return False
    except requests.exceptions.Timeout:
        print("⏰ Timeout - El análisis automático tardó demasiado tiempo")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBA DEL ENDPOINT AUTOMÁTICO DE ANÁLISIS SATELITAL")
    print("=" * 60)

    success = test_auto_analyze_endpoint()

    print("\n" + "=" * 60)
    if success:
        print("✅ PRUEBA EXITOSA - El sistema funciona correctamente!")
    else:
        print("❌ PRUEBA FALLIDA - Revisar configuración y logs")
    print("=" * 60)