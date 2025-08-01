#!/usr/bin/env python3
"""
Script para probar el endpoint con diferentes tipos de daño
"""

import requests
import json
import os
import glob

def test_all_damage_types():
    """Prueba el endpoint con diferentes tipos de imágenes de daño"""
    
    # URL del endpoint
    url = "http://localhost:5000/damage_analysis"
    
    # Buscar diferentes tipos de imágenes sintéticas
    image_patterns = [
        "data/satellite_images/synthetic_no-damage_*.png",
        "data/satellite_images/synthetic_minor-damage_*.png", 
        "data/satellite_images/synthetic_major-damage_*.png",
        "data/satellite_images/synthetic_destroyed_*.png"
    ]
    
    for pattern in image_patterns:
        images = glob.glob(pattern)
        if images:
            # Tomar la primera imagen de cada tipo
            image_path = images[0]
            
            try:
                with open(image_path, 'rb') as f:
                    files = {'image': ('test_image.png', f, 'image/png')}
                    
                    print(f"\n=== Analizando: {os.path.basename(image_path)} ===")
                    
                    response = requests.post(url, files=files, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        damage_info = result.get('damage_analysis', {})
                        print(f"Clase detectada: {damage_info.get('damage_class', 'unknown')}")
                        print(f"Confianza: {damage_info.get('confidence', 0):.2f}")
                        print(f"Nivel de riesgo: {damage_info.get('risk_level', 'unknown')}")
                        
                        # Mostrar probabilidades
                        probs = damage_info.get('all_probabilities', {})
                        print("Probabilidades:")
                        for damage_type, prob in probs.items():
                            print(f"  {damage_type}: {prob:.3f}")
                    else:
                        print(f"Error {response.status_code}: {response.text}")
                        
            except Exception as e:
                print(f"Error procesando {image_path}: {e}")

if __name__ == "__main__":
    test_all_damage_types()
