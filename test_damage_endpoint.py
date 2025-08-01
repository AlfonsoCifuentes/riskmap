#!/usr/bin/env python3
"""
Script para probar el endpoint de análisis de daños
"""

import requests
import json
import os

def test_damage_analysis():
    """Prueba el endpoint de análisis de daños"""
    
    # Ruta de imagen de prueba
    image_path = "data/satellite_images/synthetic_destroyed_000_-19.3970_1.4008_2025-08-01.png"
    
    if not os.path.exists(image_path):
        print(f"Error: No se encontró la imagen en {image_path}")
        return
    
    # URL del endpoint
    url = "http://localhost:5000/damage_analysis"
    
    try:
        # Abrir la imagen
        with open(image_path, 'rb') as f:
            files = {'image': ('test_image.png', f, 'image/png')}
            
            print(f"Enviando imagen: {image_path}")
            print(f"URL: {url}")
            
            # Hacer la petición POST
            response = requests.post(url, files=files, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("Respuesta exitosa:")
                print(json.dumps(result, indent=2))
            else:
                print("Error en la respuesta:")
                print(response.text)
                
    except Exception as e:
        print(f"Error durante la petición: {e}")

if __name__ == "__main__":
    test_damage_analysis()
