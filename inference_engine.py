"""
Sistema de Análisis e Inferencia Geopolítica
===========================================
Este módulo ejecuta el modelo entrenado para analizar nuevas noticias
y calcular factores de importancia en tiempo real.
"""

import torch
import torch.nn as nn
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import requests
from concurrent.futures import ThreadPoolExecutor
import time

# Importar modelos de computer vision
import cv2
from PIL import Image
from ultralytics import YOLO
import imagehash

# Importar el modelo de entrenamiento
from transformers import AutoTokenizer, AutoModel, AutoConfig
import sys
sys.path.append(str(Path(__file__).parent))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeopoliticalInferenceEngine:
    """Motor de inferencia para análisis geopolítico en tiempo real"""
    
    def __init__(self, model_path: str, db_path: str):
        self.model_path = Path(model_path)
        self.db_path = db_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Cargar modelo entrenado
        self.load_model()
        
        # Cargar modelo de detección de objetos
        self.yolo_model = YOLO('yolov8n.pt')  # Modelo ligero para detección
        
        # Inicializar base de datos de resultados
        self.setup_results_database()
        
        logger.info("✅ Motor de inferencia inicializado")
    
    def load_model(self):
        """Cargar modelo entrenado"""
        try:
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Reconstruir modelo (necesitamos importar la clase)
            from ai_training_bert_lora_geopolitical_intelligence import MultiTaskGeopoliticalModel
            
            # Obtener configuración del checkpoint
            model_config = checkpoint.get('config')
            
            self.model = MultiTaskGeopoliticalModel(
                model_name=model_config.BERT_MODEL,
                num_risk_classes=model_config.RISK_LEVELS,
                num_topic_classes=len(model_config.TOPIC_CLASSES),
                num_location_classes=50  # Ajustar según datos
            )
            
            # Cargar pesos
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            # Cargar tokenizer
            self.tokenizer = checkpoint['tokenizer']
            
            # Mapeos de clases
            self.topic_classes = model_config.TOPIC_CLASSES
            
            logger.info(f"✅ Modelo cargado desde {self.model_path}")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            raise
    
    def setup_results_database(self):
        """Configurar base de datos de resultados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de análisis en tiempo real
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS real_time_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Predicciones del modelo
            predicted_risk_level INTEGER,
            predicted_risk_score REAL,
            predicted_topic TEXT,
            predicted_location TEXT,
            model_confidence REAL,
            
            -- Factor de importancia
            importance_score REAL,
            recency_factor REAL,
            location_risk_factor REAL,
            content_quality_score REAL,
            
            -- Análisis de imagen
            image_analysis_json TEXT,
            visual_risk_indicators TEXT,
            
            -- Metadatos
            processing_time_ms INTEGER,
            model_version TEXT,
            
            FOREIGN KEY (article_id) REFERENCES trained_articles (id)
        )
        ''')
        
        # Tabla de alertas automáticas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS geopolitical_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            alert_type TEXT,  -- 'high_risk', 'escalation', 'breaking'
            alert_level INTEGER,  -- 1-5
            alert_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            acknowledged BOOLEAN DEFAULT 0,
            
            FOREIGN KEY (article_id) REFERENCES trained_articles (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def predict_article(self, title: str, content: str) -> Dict:
        """Predecir riesgo y clasificaciones para un artículo"""
        start_time = time.time()
        
        # Preparar texto
        text = f"{title} [SEP] {content}"
        
        # Tokenizar
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt'
        )
        
        # Mover a GPU
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Inferencia
        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask)
            
            # Obtener predicciones
            risk_probs = torch.softmax(outputs['risk_logits'], dim=1)
            topic_probs = torch.softmax(outputs['topic_logits'], dim=1)
            location_probs = torch.softmax(outputs['location_logits'], dim=1)
            
            # Clases predichas
            risk_pred = torch.argmax(risk_probs, dim=1).item() + 1  # Convertir 0-4 a 1-5
            topic_pred = torch.argmax(topic_probs, dim=1).item()
            location_pred = torch.argmax(location_probs, dim=1).item()
            
            # Confianzas
            risk_confidence = torch.max(risk_probs, dim=1)[0].item()
            topic_confidence = torch.max(topic_probs, dim=1)[0].item()
            location_confidence = torch.max(location_probs, dim=1)[0].item()
            
            # Confianza promedio ponderada
            overall_confidence = (
                0.5 * risk_confidence + 
                0.3 * topic_confidence + 
                0.2 * location_confidence
            )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            'predicted_risk_level': risk_pred,
            'predicted_risk_score': risk_confidence,
            'predicted_topic': self.topic_classes[topic_pred] if topic_pred < len(self.topic_classes) else 'unknown',
            'predicted_location_id': location_pred,
            'model_confidence': overall_confidence,
            'processing_time_ms': processing_time,
            'risk_probabilities': risk_probs.cpu().numpy().tolist(),
            'topic_probabilities': topic_probs.cpu().numpy().tolist()
        }
    
    def analyze_image(self, image_path: str) -> Dict:
        """Analizar imagen para indicadores de riesgo visual"""
        if not image_path or not Path(image_path).exists():
            return {'visual_risk_score': 0.0, 'detected_objects': [], 'risk_indicators': []}
        
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                return {'visual_risk_score': 0.0, 'detected_objects': [], 'risk_indicators': []}
            
            # Detección de objetos con YOLO
            results = self.yolo_model(image)
            
            detected_objects = []
            risk_indicators = []
            visual_risk_score = 0.0
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Obtener clase y confianza
                        class_id = int(box.cls.item())
                        confidence = box.conf.item()
                        class_name = self.yolo_model.names[class_id]
                        
                        detected_objects.append({
                            'class': class_name,
                            'confidence': confidence,
                            'bbox': box.xyxy.cpu().numpy().tolist()[0]
                        })
                        
                        # Evaluar riesgo basado en objetos detectados
                        risk_objects = {
                            'person': 0.1,      # Personas pueden indicar protestas
                            'car': 0.05,        # Vehículos
                            'truck': 0.1,       # Camiones (posibles militares)
                            'airplane': 0.3,    # Aviones (alto riesgo)
                            'tank': 1.0,        # Tanques (riesgo máximo)
                            'weapon': 1.0,      # Armas
                            'fire': 0.8,        # Fuego/explosiones
                            'smoke': 0.6        # Humo
                        }
                        
                        if class_name.lower() in risk_objects:
                            object_risk = risk_objects[class_name.lower()] * confidence
                            visual_risk_score += object_risk
                            
                            if object_risk > 0.3:
                                risk_indicators.append({
                                    'type': 'object_detection',
                                    'object': class_name,
                                    'risk_score': object_risk,
                                    'confidence': confidence
                                })
            
            # Normalizar score visual (máximo 1.0)
            visual_risk_score = min(visual_risk_score, 1.0)
            
            # Análisis adicional de color (rojo = peligro, humo, etc.)
            color_risk = self._analyze_color_indicators(image)
            visual_risk_score += color_risk * 0.2
            
            return {
                'visual_risk_score': min(visual_risk_score, 1.0),
                'detected_objects': detected_objects,
                'risk_indicators': risk_indicators,
                'color_risk': color_risk
            }
            
        except Exception as e:
            logger.error(f"❌ Error analizando imagen {image_path}: {e}")
            return {'visual_risk_score': 0.0, 'detected_objects': [], 'risk_indicators': []}
    
    def _analyze_color_indicators(self, image) -> float:
        """Analizar indicadores de color en la imagen"""
        try:
            # Convertir a HSV para mejor análisis de color
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detectar colores rojos (fuego, sangre, peligro)
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            
            mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = mask_red1 + mask_red2
            
            # Detectar colores negros/grises (humo)
            lower_gray = np.array([0, 0, 0])
            upper_gray = np.array([180, 50, 100])
            gray_mask = cv2.inRange(hsv, lower_gray, upper_gray)
            
            # Calcular porcentajes
            total_pixels = image.shape[0] * image.shape[1]
            red_percentage = np.sum(red_mask > 0) / total_pixels
            gray_percentage = np.sum(gray_mask > 0) / total_pixels
            
            # Calcular score de riesgo basado en colores
            color_risk = min(red_percentage * 2 + gray_percentage * 0.5, 1.0)
            
            return color_risk
            
        except Exception as e:
            logger.warning(f"Error en análisis de color: {e}")
            return 0.0
    
    def calculate_advanced_importance(self, 
                                    risk_level: int, 
                                    published_at: datetime,
                                    location: str,
                                    source: str,
                                    content_length: int,
                                    visual_risk_score: float = 0.0) -> Dict[str, float]:
        """Calcular factor de importancia avanzado"""
        
        if not published_at:
            published_at = datetime.now(timezone.utc)
        
        # 1. Factor de recencia (decaimiento exponencial mejorado)
        now = datetime.now(timezone.utc)
        age_hours = (now - published_at).total_seconds() / 3600
        
        if age_hours <= 1:      # Última hora: máxima importancia
            recency_factor = 1.0
        elif age_hours <= 6:    # Últimas 6 horas: alta importancia
            recency_factor = 0.9
        elif age_hours <= 24:   # Último día: buena importancia
            recency_factor = 0.7
        elif age_hours <= 72:   # Últimos 3 días: media importancia
            recency_factor = 0.5
        elif age_hours <= 168:  # Última semana: baja importancia
            recency_factor = 0.3
        else:                   # Más antiguo: importancia mínima
            recency_factor = 0.1
        
        # 2. Factor de riesgo geográfico
        high_risk_regions = {
            'ukraine': 1.0, 'russia': 0.9, 'syria': 0.95, 'afghanistan': 0.8,
            'iraq': 0.8, 'yemen': 0.9, 'somalia': 0.8, 'sudan': 0.8,
            'myanmar': 0.7, 'north korea': 0.8, 'iran': 0.8, 'israel': 0.7,
            'palestine': 0.8, 'lebanon': 0.6, 'taiwan': 0.7, 'kashmir': 0.7,
            'south china sea': 0.8, 'balkans': 0.5, 'sahel': 0.6
        }
        
        location_risk_factor = 0.3  # Factor base
        location_lower = location.lower()
        for region, risk in high_risk_regions.items():
            if region in location_lower:
                location_risk_factor = max(location_risk_factor, risk)
                break
        
        # 3. Factor de credibilidad de fuente
        source_credibility = {
            'reuters': 0.95, 'bbc': 0.9, 'ap news': 0.9, 'associated press': 0.9,
            'the guardian': 0.85, 'financial times': 0.9, 'wall street journal': 0.85,
            'new york times': 0.8, 'washington post': 0.8, 'cnn': 0.7,
            'al jazeera': 0.75, 'france24': 0.8, 'dw': 0.8,
            'rt': 0.5, 'press tv': 0.4, 'xinhua': 0.6  # Menor credibilidad
        }
        
        source_factor = 0.7  # Factor base
        source_lower = source.lower()
        for src, credibility in source_credibility.items():
            if src in source_lower:
                source_factor = credibility
                break
        
        # 4. Factor de calidad del contenido
        content_quality = min(1.0, max(0.3, content_length / 1000))  # Normalizar por longitud
        
        # 5. Factor de riesgo visual
        visual_factor = min(visual_risk_score * 0.5, 0.3)  # Máximo 30% de contribución
        
        # 6. Factor de riesgo del modelo (normalizado)
        risk_factor = risk_level / 5.0
        
        # Cálculo de importancia final (fórmula mejorada)
        # Combina todos los factores con pesos específicos
        importance_score = (
            0.35 * risk_factor +           # Peso principal al riesgo
            0.25 * recency_factor +        # Recencia muy importante
            0.20 * location_risk_factor +  # Ubicación crítica
            0.10 * source_factor +         # Credibilidad de fuente
            0.05 * content_quality +       # Calidad del contenido
            0.05 * visual_factor           # Indicadores visuales
        )
        
        # Bonus para combinaciones críticas
        if risk_level >= 4 and age_hours <= 6 and location_risk_factor >= 0.8:
            importance_score *= 1.2  # 20% bonus para situaciones críticas
        
        # Penalty para fuentes poco fiables con riesgo alto
        if risk_level >= 4 and source_factor <= 0.6:
            importance_score *= 0.8  # 20% reducción
        
        # Normalizar a rango 0-1
        importance_score = min(importance_score, 1.0)
        
        return {
            'importance_score': importance_score,
            'recency_factor': recency_factor,
            'location_risk_factor': location_risk_factor,
            'source_factor': source_factor,
            'content_quality': content_quality,
            'visual_factor': visual_factor,
            'risk_factor': risk_factor,
            'age_hours': age_hours
        }
    
    def generate_alert(self, article_id: int, analysis_result: Dict) -> Optional[Dict]:
        """Generar alerta automática si es necesario"""
        
        risk_level = analysis_result['predicted_risk_level']
        importance = analysis_result['importance_score']
        confidence = analysis_result['model_confidence']
        
        alert = None
        
        # Alerta de riesgo muy alto
        if risk_level >= 5 and confidence >= 0.8:
            alert = {
                'type': 'high_risk',
                'level': 5,
                'message': f"🚨 ALERTA CRÍTICA: Conflicto de muy alto riesgo detectado (confianza: {confidence:.1%})"
            }
        
        # Alerta de escalamiento rápido
        elif risk_level >= 4 and importance >= 0.8:
            alert = {
                'type': 'escalation',
                'level': 4,
                'message': f"⚠️ ESCALAMIENTO: Situación de alto riesgo en desarrollo (importancia: {importance:.1%})"
            }
        
        # Alerta de noticia en desarrollo
        elif risk_level >= 3 and analysis_result.get('age_hours', 24) <= 2:
            alert = {
                'type': 'breaking',
                'level': 3,
                'message': f"📢 NOTICIA EN DESARROLLO: Situación de riesgo medio reciente"
            }
        
        # Guardar alerta en base de datos
        if alert:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO geopolitical_alerts 
                    (article_id, alert_type, alert_level, alert_message)
                    VALUES (?, ?, ?, ?)
                ''', (article_id, alert['type'], alert['level'], alert['message']))
                
                conn.commit()
                conn.close()
                
                logger.info(f"🚨 Alerta generada: {alert['message']}")
                
            except Exception as e:
                logger.error(f"❌ Error guardando alerta: {e}")
        
        return alert
    
    def analyze_article(self, article_id: int) -> Dict:
        """Análisis completo de un artículo"""
        
        # Obtener datos del artículo
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, url, source, published_at, image_path
            FROM trained_articles
            WHERE id = ?
        ''', (article_id,))
        
        row = cursor.fetchone()
        if not row:
            logger.error(f"❌ Artículo {article_id} no encontrado")
            return {}
        
        article_id, title, content, url, source, published_at, image_path = row
        
        # Parsear fecha
        if published_at:
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except:
                    published_at = datetime.now(timezone.utc)
            elif not published_at.tzinfo:
                published_at = published_at.replace(tzinfo=timezone.utc)
        else:
            published_at = datetime.now(timezone.utc)
        
        # 1. Predicción del modelo
        model_prediction = self.predict_article(title, content)
        
        # 2. Análisis de imagen
        image_analysis = self.analyze_image(image_path) if image_path else {}
        
        # 3. Cálculo de importancia
        importance_metrics = self.calculate_advanced_importance(
            risk_level=model_prediction['predicted_risk_level'],
            published_at=published_at,
            location=model_prediction.get('predicted_location', 'Unknown'),
            source=source,
            content_length=len(content),
            visual_risk_score=image_analysis.get('visual_risk_score', 0.0)
        )
        
        # 4. Combinar resultados
        analysis_result = {
            **model_prediction,
            **importance_metrics,
            'image_analysis': image_analysis,
            'article_url': url,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # 5. Generar alerta si es necesario
        alert = self.generate_alert(article_id, analysis_result)
        if alert:
            analysis_result['alert'] = alert
        
        # 6. Guardar resultados
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO real_time_analysis (
                    article_id, predicted_risk_level, predicted_risk_score,
                    predicted_topic, model_confidence, importance_score,
                    recency_factor, location_risk_factor, content_quality_score,
                    image_analysis_json, processing_time_ms, model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_id, model_prediction['predicted_risk_level'],
                model_prediction['predicted_risk_score'], model_prediction['predicted_topic'],
                model_prediction['model_confidence'], importance_metrics['importance_score'],
                importance_metrics['recency_factor'], importance_metrics['location_risk_factor'],
                importance_metrics['content_quality'], json.dumps(image_analysis),
                model_prediction['processing_time_ms'], "v1.0"
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Error guardando análisis: {e}")
        finally:
            conn.close()
        
        return analysis_result
    
    def batch_analyze(self, limit: int = 100) -> List[Dict]:
        """Analizar múltiples artículos en lote"""
        
        # Obtener artículos sin analizar
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ta.id
            FROM trained_articles ta
            LEFT JOIN real_time_analysis rta ON ta.id = rta.article_id
            WHERE rta.article_id IS NULL
            ORDER BY ta.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        article_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"🔄 Analizando {len(article_ids)} artículos en lote...")
        
        results = []
        
        # Procesar en paralelo (con cuidado de no sobrecargar GPU)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(self.analyze_article, article_id)
                for article_id in article_ids
            ]
            
            for future in futures:
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"❌ Error en análisis paralelo: {e}")
        
        logger.info(f"✅ Análisis en lote completado: {len(results)} artículos procesados")
        
        return results
    
    def get_dashboard_data(self) -> Dict:
        """Obtener datos para dashboard en tiempo real"""
        
        conn = sqlite3.connect(self.db_path)
        
        # Estadísticas generales
        stats_query = '''
            SELECT 
                COUNT(*) as total_articles,
                AVG(predicted_risk_level) as avg_risk,
                AVG(importance_score) as avg_importance,
                COUNT(CASE WHEN predicted_risk_level >= 4 THEN 1 END) as high_risk_count
            FROM real_time_analysis
            WHERE analysis_timestamp >= datetime('now', '-24 hours')
        '''
        
        stats_df = pd.read_sql_query(stats_query, conn)
        
        # Alertas activas
        alerts_query = '''
            SELECT alert_type, alert_level, alert_message, created_at
            FROM geopolitical_alerts
            WHERE acknowledged = 0
            ORDER BY alert_level DESC, created_at DESC
            LIMIT 20
        '''
        
        alerts_df = pd.read_sql_query(alerts_query, conn)
        
        # Tendencias por región
        trends_query = '''
            SELECT 
                predicted_topic,
                COUNT(*) as count,
                AVG(predicted_risk_level) as avg_risk,
                AVG(importance_score) as avg_importance
            FROM real_time_analysis
            WHERE analysis_timestamp >= datetime('now', '-24 hours')
            GROUP BY predicted_topic
            ORDER BY avg_importance DESC
        '''
        
        trends_df = pd.read_sql_query(trends_query, conn)
        
        conn.close()
        
        return {
            'stats': stats_df.to_dict('records')[0] if len(stats_df) > 0 else {},
            'active_alerts': alerts_df.to_dict('records'),
            'topic_trends': trends_df.to_dict('records'),
            'last_updated': datetime.now().isoformat()
        }

def main():
    """Función principal para ejecutar análisis"""
    
    # Rutas
    model_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\models\trained\best_model.pt"
    db_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\trained_analysis.db"
    
    # Verificar que existe el modelo
    if not Path(model_path).exists():
        logger.error(f"❌ Modelo no encontrado en {model_path}")
        logger.info("🔧 Ejecuta primero el notebook de entrenamiento")
        return
    
    # Crear motor de inferencia
    engine = GeopoliticalInferenceEngine(model_path, db_path)
    
    # Ejecutar análisis en lote
    results = engine.batch_analyze(limit=50)
    
    # Obtener datos de dashboard
    dashboard_data = engine.get_dashboard_data()
    
    print(f"\n✅ Análisis completado!")
    print(f"📊 Artículos analizados: {len(results)}")
    print(f"🚨 Alertas activas: {len(dashboard_data['active_alerts'])}")
    print(f"📈 Estadísticas del dashboard: {dashboard_data['stats']}")
    
    # Mostrar alertas más importantes
    if dashboard_data['active_alerts']:
        print(f"\n🚨 Alertas más críticas:")
        for alert in dashboard_data['active_alerts'][:3]:
            print(f"  {alert['alert_message']}")

if __name__ == "__main__":
    main()
