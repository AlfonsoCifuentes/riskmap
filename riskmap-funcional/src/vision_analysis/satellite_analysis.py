"""
Satellite image analyzer: descarga y análisis de imágenes satelitales usando OpenCV y APIs públicas.
"""
import os
import requests
import cv2
import numpy as np
from pathlib import Path

class SatelliteImageAnalyzer:
    def __init__(self, config):
        self.config = config
        # Directorio para cache de imágenes
        self.cache_dir = Path(self.config.get('satellite.cache_dir', 'data/satellite_images'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download_image(self, lat, lon, date):
        """
        Descarga imagen satelital de NASA Earth API.
        """
        # Obtener API key de NASA desde config api_keys o variable de entorno
        api_key = self.config.get('api_keys.nasa') or os.getenv('NASA_API_KEY', 'DEMO_KEY')
        url = (
            f"https://api.nasa.gov/planetary/earth/imagery?lat={lat}&lon={lon}"
            f"&date={date}&dim=0.10&api_key={api_key}"
        )
        resp = requests.get(url)
        if resp.status_code == 200:
            file_name = f"sat_{lat}_{lon}_{date}.png"
            file_path = self.cache_dir / file_name
            with open(file_path, 'wb') as f:
                f.write(resp.content)
            return str(file_path)
        else:
            raise Exception(f"Error downloading image: {resp.status_code}")

    def analyze_satellite_image(self, lat, lon, date):
        """
        Descarga y analiza la imagen satelital en la ubicación y fecha dadas.
        Devuelve métricas de riesgo y ruta de imagen.
        """
        img_path = self.download_image(lat, lon, date)
        # Leer con OpenCV
        img = cv2.imread(img_path)
        if img is None:
            raise Exception("Error leyendo imagen descargada")

        # Convertir a escala de grises y calcular histograma como ejemplo
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0,256])
        # Riesgo placeholder basado en nivel medio de intensidad (nubes/oscuridad)
        mean_val = float(np.mean(gray))
        risk_score = round(max(0, min(100, (255 - mean_val))) / 100, 2)

        return {
            'image_path': img_path,
            'mean_intensity': mean_val,
            'risk_score': risk_score
        }
