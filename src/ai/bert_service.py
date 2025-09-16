"""
BERT Service - Servicio independiente para análisis de sentimientos con BERT
Maneja la carga del modelo, análisis de texto y cálculo de importancia
"""

import logging
import threading
from typing import Dict, Optional, Any
from datetime import datetime
import torch
import os

logger = logging.getLogger(__name__)

class BERTService:
    """Servicio para análisis de sentimientos con BERT"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(BERTService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.model = None
        self.tokenizer = None
        self.sentiment_pipeline = None
        self.model_loaded = False
        self.device = self._get_optimal_device()
        self._model_lock = threading.Lock()
        
        logger.info(f"🧠 BERTService inicializado. Dispositivo: {self.device}")
    
    def _get_optimal_device(self) -> str:
        """Determina el mejor dispositivo disponible"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"  # Apple Silicon
        else:
            return "cpu"
    
    def initialize_model(self, model_name: str = None) -> bool:
        """
        Inicializa el modelo BERT de forma thread-safe
        
        Args:
            model_name: Nombre del modelo a cargar
            
        Returns:
            bool: True si el modelo se carga exitosamente
        """
        if self.model_loaded:
            return True
        
        with self._model_lock:
            if self.model_loaded:  # Double-check locking
                return True
            
            try:
                logger.info("🧠 Iniciando carga del modelo BERT...")
                
                from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
                
                # Seleccionar modelo
                if model_name is None:
                    model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
                
                logger.info(f"📥 Cargando modelo: {model_name}")
                
                # Cargar tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    use_fast=True,
                    trust_remote_code=False
                )
                logger.info("✅ Tokenizer cargado")
                
                # Cargar modelo
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    trust_remote_code=False
                )
                logger.info("✅ Modelo cargado")
                
                # Mover a dispositivo óptimo
                if self.device != "cpu":
                    try:
                        self.model = self.model.to(self.device)
                        logger.info(f"✅ Modelo movido a {self.device}")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo mover a {self.device}, usando CPU: {e}")
                        self.device = "cpu"
                
                # Crear pipeline
                device_id = 0 if self.device == "cuda" else -1
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    top_k=None,
                    device=device_id
                )
                
                # Test del modelo
                test_result = self.sentiment_pipeline("This is a test")
                logger.info(f"🧪 Test exitoso: {len(test_result)} resultados")
                
                self.model_loaded = True
                logger.info("✅ Modelo BERT cargado y listo")
                return True
                
            except ImportError as e:
                logger.error(f"❌ Transformers no instalado: {e}")
                return False
            except Exception as e:
                logger.error(f"❌ Error cargando modelo BERT: {e}")
                return False
    
    def is_available(self) -> bool:
        """Verifica si el modelo está disponible"""
        return self.model_loaded and self.sentiment_pipeline is not None
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analiza el sentimiento de un texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con análisis de sentimiento
        """
        if not self.is_available():
            raise RuntimeError("Modelo BERT no está disponible")
        
        if not text or not text.strip():
            raise ValueError("Texto vacío para análisis")
        
        try:
            # Limpiar y preparar texto
            cleaned_text = str(text).strip()
            
            # Limitar longitud para BERT (512 tokens max)
            if len(cleaned_text) > 512:
                cleaned_text = cleaned_text[:512]
            
            # Análisis con BERT
            with self._model_lock:
                results = self.sentiment_pipeline(cleaned_text)
            
            if not results:
                raise ValueError("No se obtuvieron resultados del modelo")
            
            # Procesar resultados
            sentiment_scores = self._process_sentiment_results(results)
            
            return {
                'negative_sentiment': sentiment_scores.get('negative', 0.0),
                'positive_sentiment': sentiment_scores.get('positive', 0.0),
                'neutral_sentiment': sentiment_scores.get('neutral', 0.0),
                'confidence': max(sentiment_scores.values()) if sentiment_scores else 0.0,
                'dominant_sentiment': max(sentiment_scores, key=sentiment_scores.get) if sentiment_scores else 'neutral',
                'raw_results': results,
                'model_info': {
                    'model_name': 'BERT Sentiment Analysis',
                    'device': self.device,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis BERT: {e}")
            raise
    
    def _process_sentiment_results(self, results: list) -> Dict[str, float]:
        """Procesa los resultados del pipeline de sentimientos"""
        sentiment_scores = {'negative': 0.0, 'positive': 0.0, 'neutral': 0.0}
        
        for result in results:
            if isinstance(result, dict) and 'label' in result and 'score' in result:
                label = result['label'].upper()
                score = result['score']
                
                # Mapear diferentes formatos de labels
                if label in ['NEGATIVE', 'NEG', 'LABEL_0']:
                    sentiment_scores['negative'] = score
                elif label in ['POSITIVE', 'POS', 'LABEL_1']:
                    sentiment_scores['positive'] = score
                elif label in ['NEUTRAL', 'NEU', 'LABEL_2']:
                    sentiment_scores['neutral'] = score
        
        # Si no hay neutral explícito, calcularlo
        if sentiment_scores['neutral'] == 0.0:
            total = sentiment_scores['negative'] + sentiment_scores['positive']
            if total < 1.0:
                sentiment_scores['neutral'] = 1.0 - total
        
        return sentiment_scores
    
    def calculate_importance(self, text: str, location: str = "", risk_level: str = "medium") -> Dict[str, Any]:
        """
        Calcula la importancia de un artículo usando BERT
        
        Args:
            text: Texto del artículo
            location: Ubicación geográfica
            risk_level: Nivel de riesgo del artículo
            
        Returns:
            Dict con análisis de importancia
        """
        try:
            # Análisis de sentimiento
            sentiment_analysis = self.analyze_sentiment(text)
            
            # Calcular importancia base
            negative_score = sentiment_analysis['negative_sentiment']
            positive_score = sentiment_analysis['positive_sentiment']
            
            # En noticias geopolíticas, el sentimiento negativo indica mayor importancia
            base_importance = (negative_score * 0.7) + (positive_score * 0.3)
            base_importance = base_importance * 100  # Escalar a 0-100
            
            # Aplicar multiplicadores geopolíticos
            geo_multiplier = self._calculate_geo_multiplier(location.lower())
            risk_multiplier = self._calculate_risk_multiplier(risk_level.lower())
            
            # Importancia final
            final_importance = base_importance * geo_multiplier * risk_multiplier
            final_importance = max(10, min(100, final_importance))
            
            return {
                'importance_score': round(final_importance, 2),
                'base_importance': round(base_importance, 2),
                'sentiment_analysis': sentiment_analysis,
                'multipliers': {
                    'geo_multiplier': geo_multiplier,
                    'risk_multiplier': risk_multiplier
                },
                'metadata': {
                    'location': location,
                    'risk_level': risk_level,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'model_used': 'BERT + Geopolitical Factors'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculando importancia: {e}")
            raise
    
    def _calculate_geo_multiplier(self, location: str) -> float:
        """Calcula multiplicador geopolítico basado en ubicación"""
        high_risk_regions = [
            'ukraine', 'gaza', 'israel', 'syria', 'afghanistan', 
            'iran', 'iraq', 'taiwan', 'korea', 'yemen', 'lebanon'
        ]
        
        medium_risk_regions = [
            'russia', 'china', 'venezuela', 'cuba', 'belarus',
            'myanmar', 'ethiopia', 'sudan', 'mali', 'niger'
        ]
        
        for region in high_risk_regions:
            if region in location:
                return 1.3
        
        for region in medium_risk_regions:
            if region in location:
                return 1.15
        
        return 1.0
    
    def _calculate_risk_multiplier(self, risk_level: str) -> float:
        """Calcula multiplicador basado en nivel de riesgo"""
        risk_multipliers = {
            'critical': 1.4,
            'high': 1.2,
            'medium': 1.0,
            'low': 0.8,
            'minimal': 0.6
        }
        return risk_multipliers.get(risk_level, 1.0)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información del modelo cargado"""
        return {
            'model_loaded': self.model_loaded,
            'device': self.device,
            'model_available': self.is_available(),
            'supports_gpu': torch.cuda.is_available(),
            'supports_mps': hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
            'torch_version': torch.__version__
        }

# Instancia singleton global
bert_service = BERTService()
