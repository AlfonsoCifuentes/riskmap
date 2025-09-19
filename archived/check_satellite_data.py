#!/usr/bin/env python3
"""Script para verificar los datos que envían los endpoints satelitales."""

import requests
import json

def check_satellite_data():
    """Verificar los datos específicos de cada endpoint."""
    base_url = "http://localhost:8050"
    
    endpoints = {
        "Galería": "/api/satellite/gallery-images",
        "Alertas": "/api/satellite/critical-alerts", 
        "Timeline": "/api/satellite/analysis-timeline",
        "Predicciones": "/api/satellite/evolution-predictions"
    }
    
    print("🔍 VERIFICANDO ESTRUCTURA DE DATOS SATELITALES")
    print("=" * 60)
    
    for name, endpoint in endpoints.items():
        print(f"\n📡 {name} ({endpoint}):")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {data.get('success', 'N/A')}")
                
                # Mostrar estructura de datos específica
                if name == "Galería" and 'images' in data:
                    if data['images']:
                        img = data['images'][0]
                        print(f"   🖼️ Primer item: image_path='{img.get('image_path', 'N/A')}', detection.type='{img.get('detection', {}).get('type', 'N/A')}'")
                    else:
                        print("   📭 Sin imágenes")
                        
                elif name == "Alertas" and 'alerts' in data:
                    if data['alerts']:
                        alert = data['alerts'][0]
                        print(f"   ⚠️ Primer item: type='{alert.get('type', 'N/A')}', confidence={alert.get('confidence', 'N/A')}")
                    else:
                        print("   📭 Sin alertas")
                        
                elif name == "Timeline" and 'timeline' in data:
                    if data['timeline']:
                        item = data['timeline'][0]
                        print(f"   📅 Primer item: analysis_id='{item.get('analysis_id', 'N/A')}', status='{item.get('status', 'N/A')}'")
                    else:
                        print("   📭 Sin timeline")
                        
                elif name == "Predicciones" and 'predictions' in data:
                    if data['predictions']:
                        pred = data['predictions'][0]
                        print(f"   🔮 Primer item: type='{pred.get('type', 'N/A')}', trend_percentage={pred.get('trend_percentage', 'N/A')}")
                    else:
                        print("   📭 Sin predicciones")
                        
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("🎯 VERIFICACIÓN COMPLETADA")

if __name__ == "__main__":
    check_satellite_data()
