"""
Satellite image analyzer: descarga y análisis de imágenes satelitales usando OpenCV y APIs públicas.
Integra xView2 para evaluación de daños en edificios.
"""
import os
import sys
import json
import requests
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SatelliteImageAnalyzer:
    def __init__(self, config):
        self.config = config
        # Directorio para cache de imágenes
        self.cache_dir = Path(self.config.get('satellite.cache_dir', 'data/satellite_images'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize xView2 damage classifier
        self.damage_classifier = None
        self._init_damage_classifier()
    
    def _init_damage_classifier(self):
        """Initialize damage assessment classifier"""
        try:
            # Try to use the simple damage classifier first
            from .simple_damage_classifier import SimpleDamageClassifier
            
            # Create config for damage classifier
            damage_config = {
                'cache_dir': self.config.get('satellite.cache_dir', 'data/satellite_images'),
                'model_dir': 'models/simple_damage',
                'random_seed': 42
            }
            
            self.damage_classifier = SimpleDamageClassifier(damage_config)
            
            # Try to load pre-trained model
            if not self.damage_classifier.load_model():
                logger.warning("No pre-trained damage model found. Run training first.")
            else:
                logger.info("Simple damage classifier loaded successfully")
                
        except ImportError as e:
            logger.warning(f"Damage classifier not available: {e}")
        except Exception as e:
            logger.error(f"Error initializing damage classifier: {e}")

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
        Incluye evaluación de daños usando xView2 si está disponible.
        Devuelve métricas de riesgo y ruta de imagen.
        """
        img_path = self.download_image(lat, lon, date)
        
        # Leer con OpenCV
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError("Error leyendo imagen descargada")

        # Análisis básico de imagen
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_val = float(np.mean(gray))
        std_val = float(np.std(gray))
        
        # Detección de bordes para análisis de estructura
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Riesgo básico basado en intensidad y textura
        basic_risk_score = round(max(0, min(100, (255 - mean_val))) / 100, 2)
        
        # Análisis de daños con clasificador simplificado si está disponible
        damage_analysis = None
        if self.damage_classifier:
            try:
                damage_analysis = self.damage_classifier.predict(img_path)
                logger.info(f"Damage analysis completed: {damage_analysis['damage_class']}")
            except Exception as e:
                logger.warning(f"Error in damage analysis: {e}")
        
        # Combinar análisis básico y de daños
        analysis_result = {
            'image_path': img_path,
            'coordinates': {'lat': lat, 'lon': lon, 'date': date},
            'basic_analysis': {
                'mean_intensity': mean_val,
                'std_intensity': std_val,
                'edge_density': edge_density,
                'risk_score': basic_risk_score
            },
            'damage_analysis': damage_analysis,
            'combined_risk_level': self._calculate_combined_risk(basic_risk_score, damage_analysis),
            'timestamp': datetime.now().isoformat()
        }

        return analysis_result
    
    def _calculate_combined_risk(self, basic_risk: float, damage_analysis: Optional[Dict]) -> str:
        """Calcula el nivel de riesgo combinado"""
        if not damage_analysis:
            # Solo análisis básico disponible
            if basic_risk < 0.3:
                return 'low'
            elif basic_risk < 0.7:
                return 'medium'
            else:
                return 'high'
        
        # Combinar análisis básico y de daños
        damage_class = damage_analysis.get('damage_class', 'no-damage')
        confidence = damage_analysis.get('confidence', 0.0)
        
        # Mapeo de clases de daño a nivel de riesgo
        damage_risk_mapping = {
            'no-damage': 0.1,
            'minor-damage': 0.4,
            'major-damage': 0.7,
            'destroyed': 1.0
        }
        
        damage_risk = damage_risk_mapping.get(damage_class, 0.1)
        
        # Combinar con peso basado en confianza
        combined_risk = (basic_risk * 0.3) + (damage_risk * 0.7 * confidence)
        
        if combined_risk < 0.3:
            return 'low'
        elif combined_risk < 0.6:
            return 'medium'
        elif combined_risk < 0.8:
            return 'high'
        else:
            return 'critical'
    
    def train_damage_model(self) -> bool:
        """Entrena el modelo de evaluación de daños simplificado"""
        if not self.damage_classifier:
            logger.error("Damage classifier not initialized")
            return False
        
        try:
            logger.info("Starting damage model training...")
            success = self.damage_classifier.train()
            
            if success:
                logger.info("Damage model training completed successfully")
                return True
            else:
                logger.error("Training failed")
                return False
                
        except Exception as e:
            logger.error(f"Error training damage model: {e}")
            return False
    
    def get_damage_model_info(self) -> Dict[str, Any]:
        """Obtiene información sobre el modelo de evaluación de daños"""
        if not self.damage_classifier:
            return {'status': 'not_available', 'message': 'Damage classifier not initialized'}
        
        return self.damage_classifier.get_model_info()
    
    def analyze_damage(self, image_path: str) -> Dict[str, Any]:
        """Analyze damage in a satellite image using the trained model"""
        if not self.damage_classifier:
            return {'error': 'Damage classifier not initialized'}
        
        try:
            result = self.damage_classifier.predict(image_path)
            return result
        except Exception as e:
            logger.error(f"Error analyzing damage: {e}")
            return {'error': str(e)}
