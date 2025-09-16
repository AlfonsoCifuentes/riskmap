
import cv2
import numpy as np
from pathlib import Path
import json
import sqlite3
from datetime import datetime
import logging

class SatelliteImageAnalysis:
    """Análisis automático de imágenes satelitales"""
    
    def __init__(self):
        self.images_dir = Path('src/satellite/images')
        self.db_path = 'geopolitical_intelligence.db'
    
    def analyze_all_images(self):
        """Analizar todas las imágenes satelitales"""
        try:
            image_files = list(self.images_dir.glob('*.jpg'))
            results = []
            
            for image_file in image_files:
                analysis_result = self.analyze_single_image(image_file)
                if analysis_result:
                    results.append(analysis_result)
                    self.save_analysis_to_database(analysis_result)
            
            print(f"Analizadas {len(results)} imágenes satelitales")
            return results
            
        except Exception as e:
            print(f"Error en análisis masivo: {e}")
            return []
    
    def analyze_single_image(self, image_path):
        """Analizar una imagen satelital individual"""
        try:
            # Cargar imagen
            image = cv2.imread(str(image_path))
            if image is None:
                return None
            
            # Convertir a RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Análisis básico
            analysis = {
                'image_path': str(image_path),
                'filename': image_path.name,
                'analysis_date': datetime.now().isoformat(),
                'dimensions': image.shape,
                'file_size': image_path.stat().st_size
            }
            
            # Detección de cambios en vegetación (NDVI simplificado)
            analysis['vegetation_index'] = self.calculate_vegetation_index(image_rgb)
            
            # Detección de agua
            analysis['water_detection'] = self.detect_water_bodies(image_rgb)
            
            # Detección de infraestructura
            analysis['infrastructure_detection'] = self.detect_infrastructure(image_rgb)
            
            # Score de riesgo general
            analysis['risk_score'] = self.calculate_risk_score(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"Error analizando imagen {image_path}: {e}")
            return None
    
    def calculate_vegetation_index(self, image):
        """Calcular índice de vegetación simplificado"""
        try:
            # Separar canales RGB
            red = image[:, :, 0].astype(float)
            green = image[:, :, 1].astype(float)
            blue = image[:, :, 2].astype(float)
            
            # NDVI simplificado (usando verde como proxy de NIR)
            ndvi = np.divide(green - red, green + red + 1e-8)
            
            return {
                'mean_ndvi': float(np.mean(ndvi)),
                'vegetation_coverage': float(np.sum(ndvi > 0.2) / ndvi.size),
                'healthy_vegetation': float(np.sum(ndvi > 0.5) / ndvi.size)
            }
            
        except Exception as e:
            print(f"Error calculando índice vegetación: {e}")
            return {}
    
    def detect_water_bodies(self, image):
        """Detectar cuerpos de agua"""
        try:
            # Convertir a HSV para mejor detección de agua
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Rangos para detectar agua (azules)
            lower_water = np.array([100, 50, 50])
            upper_water = np.array([130, 255, 255])
            
            # Crear máscara de agua
            water_mask = cv2.inRange(hsv, lower_water, upper_water)
            
            # Calcular estadísticas
            water_pixels = np.sum(water_mask > 0)
            total_pixels = water_mask.size
            water_percentage = (water_pixels / total_pixels) * 100
            
            return {
                'water_coverage_percent': float(water_percentage),
                'water_pixels': int(water_pixels),
                'has_significant_water': water_percentage > 5.0
            }
            
        except Exception as e:
            print(f"Error detectando agua: {e}")
            return {}
    
    def detect_infrastructure(self, image):
        """Detectar infraestructura (simplicado)"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Detectar bordes (infraestructura suele tener líneas rectas)
            edges = cv2.Canny(gray, 50, 150)
            
            # Detectar líneas usando transformada de Hough
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
            
            infrastructure_score = 0
            if lines is not None:
                infrastructure_score = min(len(lines) / 100.0, 1.0)  # Normalizar
            
            return {
                'edge_density': float(np.sum(edges > 0) / edges.size),
                'detected_lines': len(lines) if lines is not None else 0,
                'infrastructure_score': float(infrastructure_score)
            }
            
        except Exception as e:
            print(f"Error detectando infraestructura: {e}")
            return {}
    
    def calculate_risk_score(self, analysis):
        """Calcular score de riesgo basado en análisis"""
        try:
            risk_score = 0.0
            
            # Factor vegetación (menos vegetación = más riesgo)
            veg_data = analysis.get('vegetation_index', {})
            if veg_data.get('vegetation_coverage', 1.0) < 0.3:
                risk_score += 0.3
            
            # Factor agua (sequía o inundación)
            water_data = analysis.get('water_detection', {})
            water_coverage = water_data.get('water_coverage_percent', 0)
            if water_coverage < 2 or water_coverage > 30:  # Muy poca o mucha agua
                risk_score += 0.2
            
            # Factor infraestructura (mucha infraestructura = más población en riesgo)
            infra_data = analysis.get('infrastructure_detection', {})
            if infra_data.get('infrastructure_score', 0) > 0.7:
                risk_score += 0.4
            
            # Normalizar entre 0 y 1
            return min(risk_score, 1.0)
            
        except Exception as e:
            print(f"Error calculando risk score: {e}")
            return 0.0
    
    def save_analysis_to_database(self, analysis):
        """Guardar análisis en base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            cursor = conn.execute("""
                INSERT OR REPLACE INTO satellite_analysis
                (image_path, filename, analysis_date, vegetation_index, 
                 water_detection, infrastructure_detection, risk_score, raw_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis['image_path'],
                analysis['filename'],
                analysis['analysis_date'],
                json.dumps(analysis.get('vegetation_index', {})),
                json.dumps(analysis.get('water_detection', {})),
                json.dumps(analysis.get('infrastructure_detection', {})),
                analysis.get('risk_score', 0.0),
                json.dumps(analysis)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error guardando análisis en BD: {e}")
            