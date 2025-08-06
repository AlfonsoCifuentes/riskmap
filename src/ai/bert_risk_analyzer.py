"""
BERT Risk Analyzer - Sistema Unificado para Análisis de Riesgo
============================================================
Este módulo reemplaza completamente el análisis de riesgo basado en Ollama/Groq 
y usa exclusivamente BERT para un análisis más consistente y confiable.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import traceback

# NLP and ML imports
try:
    import torch
    from transformers import (
        AutoTokenizer, AutoModelForSequenceClassification,
        pipeline, AutoModel
    )
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    BERT_AVAILABLE = True
except ImportError as e:
    BERT_AVAILABLE = False
    logging.warning(f"BERT no disponible: {e}")

logger = logging.getLogger(__name__)

class BertRiskAnalyzer:
    """
    Analizador de riesgo unificado usando BERT.
    Reemplaza completamente Ollama/Groq para análisis de riesgo.
    """

    def __init__(self):
        """Inicializar el analizador BERT."""
        self.models_loaded = False
        self.sentiment_analyzer = None
        self.classifier = None
        self.tokenizer = None
        self.embedding_model = None
        
        if BERT_AVAILABLE:
            self._load_models()
        else:
            logger.error("❌ BERT no está disponible. Análisis de riesgo será limitado.")

    def _load_models(self):
        """Cargar todos los modelos BERT necesarios."""
        try:
            logger.info("🤖 Cargando modelos BERT...")
            
            # Sentiment analysis model
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Zero-shot classification model
            self.classifier = pipeline(
                "zero-shot-classification",
                model="microsoft/DialoGPT-medium",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Embedding model for semantic analysis
            self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            self.embedding_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            
            self.models_loaded = True
            logger.info("✅ Modelos BERT cargados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelos BERT: {e}")
            self.models_loaded = False

    def analyze_risk_level(self, title: str, content: str, country: str = None) -> Dict[str, Any]:
        """
        Analizar el nivel de riesgo de un artículo usando BERT.
        
        Args:
            title: Título del artículo
            content: Contenido del artículo
            country: País relacionado (opcional)
            
        Returns:
            Dict con nivel de riesgo, score, confianza y análisis detallado
        """
        if not self.models_loaded:
            return self._fallback_keyword_analysis(title, content)
        
        try:
            # Combinar título y contenido para análisis
            full_text = f"{title}. {content[:500]}"  # Limitar para BERT
            
            # 1. Análisis de sentimiento
            sentiment_result = self.sentiment_analyzer(full_text)[0]
            sentiment_score = sentiment_result['score']
            sentiment_label = sentiment_result['label']
            
            # 2. Clasificación de riesgo por categorías
            risk_categories = [
                "guerra y conflicto armado",
                "terrorismo y violencia",
                "crisis política",
                "desastre natural",
                "crisis económica",
                "noticia rutinaria"
            ]
            
            classification_result = self.classifier(full_text, risk_categories)
            top_category = classification_result['labels'][0]
            category_confidence = classification_result['scores'][0]
            
            # 3. Análisis de palabras clave de alto riesgo
            keyword_score = self._calculate_keyword_risk_score(full_text)
            
            # 4. Análisis geográfico si hay país
            geographic_score = self._analyze_geographic_risk(country) if country else 0.5
            
            # 5. Análisis de escalamiento potencial
            escalation_score = self._analyze_escalation_potential(full_text)
            
            # 6. Combinar todos los scores
            final_risk_score = self._calculate_final_risk_score(
                sentiment_score, sentiment_label, category_confidence, 
                keyword_score, geographic_score, escalation_score, top_category
            )
            
            # 7. Determinar nivel de riesgo final
            risk_level = self._score_to_risk_level(final_risk_score)
            
            # 8. Generar explicación
            reasoning = self._generate_reasoning(
                sentiment_label, top_category, category_confidence,
                keyword_score, geographic_score, escalation_score, country
            )
            
            return {
                'level': risk_level,
                'score': final_risk_score,
                'confidence': category_confidence,
                'reasoning': reasoning,
                'sentiment': {
                    'label': sentiment_label,
                    'score': sentiment_score
                },
                'category': top_category,
                'keyword_score': keyword_score,
                'geographic_score': geographic_score,
                'escalation_score': escalation_score,
                'ai_powered': True,
                'model_used': 'bert_unified',
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis BERT: {e}")
            logger.error(traceback.format_exc())
            return self._fallback_keyword_analysis(title, content)

    def _calculate_keyword_risk_score(self, text: str) -> float:
        """Calcular score de riesgo basado en palabras clave."""
        text_lower = text.lower()
        
        # Palabras clave de alto riesgo con pesos
        high_risk_keywords = {
            # Guerra y conflicto (peso alto)
            'guerra': 1.0, 'war': 1.0, 'conflicto': 0.9, 'conflict': 0.9,
            'batalla': 0.9, 'battle': 0.9, 'invasión': 1.0, 'invasion': 1.0,
            'bombardeo': 0.95, 'bombing': 0.95, 'ataque': 0.9, 'attack': 0.9,
            'militar': 0.8, 'military': 0.8, 'ejército': 0.8, 'army': 0.8,
            'soldados': 0.8, 'soldiers': 0.8, 'tropas': 0.8, 'troops': 0.8,
            
            # Terrorismo y violencia
            'terrorismo': 1.0, 'terrorism': 1.0, 'terrorista': 1.0, 'terrorist': 1.0,
            'bomba': 0.95, 'bomb': 0.95, 'explosión': 0.9, 'explosion': 0.9,
            'secuestro': 0.9, 'kidnapping': 0.9, 'asesinato': 0.95, 'murder': 0.95,
            'violencia': 0.8, 'violence': 0.8, 'amenaza': 0.7, 'threat': 0.7,
            
            # Crisis política
            'golpe': 0.9, 'coup': 0.9, 'revolución': 0.85, 'revolution': 0.85,
            'crisis': 0.8, 'disturbios': 0.8, 'riots': 0.8, 'protesta': 0.6, 'protest': 0.6,
            'manifestación': 0.5, 'demonstration': 0.5, 'oposición': 0.6, 'opposition': 0.6,
            
            # Armas y tecnología militar
            'nuclear': 0.95, 'misil': 0.9, 'missile': 0.9, 'armas': 0.8, 'weapons': 0.8,
            'química': 0.9, 'chemical': 0.9, 'biológica': 0.9, 'biological': 0.9,
            
            # Geografía conflictiva
            'frontera': 0.7, 'border': 0.7, 'territorio': 0.7, 'territory': 0.7,
            'zona': 0.6, 'zone': 0.6, 'región': 0.6, 'region': 0.6,
            
            # Instituciones y organizaciones
            'otan': 0.8, 'nato': 0.8, 'onu': 0.7, 'un': 0.7, 'consejo': 0.7, 'council': 0.7,
            'sanciones': 0.8, 'sanctions': 0.8, 'embargo': 0.8,
            
            # Impacto humanitario
            'refugiados': 0.8, 'refugees': 0.8, 'desplazados': 0.8, 'displaced': 0.8,
            'víctimas': 0.8, 'victims': 0.8, 'muertos': 0.9, 'dead': 0.9,
            'heridos': 0.8, 'wounded': 0.8, 'casualties': 0.9,
            
            # Emergencias y desastres
            'emergencia': 0.7, 'emergency': 0.7, 'evacuación': 0.8, 'evacuation': 0.8,
            'desastre': 0.8, 'disaster': 0.8, 'catástrofe': 0.9, 'catastrophe': 0.9,
        }
        
        # Calcular score basado en palabras encontradas
        total_score = 0.0
        words_found = 0
        
        for keyword, weight in high_risk_keywords.items():
            if keyword in text_lower:
                total_score += weight
                words_found += 1
        
        # Normalizar score (máximo 1.0)
        if words_found > 0:
            normalized_score = min(total_score / words_found, 1.0)
        else:
            normalized_score = 0.1  # Score base mínimo
        
        return normalized_score

    def _analyze_geographic_risk(self, country: str) -> float:
        """Analizar riesgo geográfico basado en el país."""
        if not country:
            return 0.5
        
        country_lower = country.lower()
        
        # Países de alto riesgo
        high_risk_countries = {
            'ukraine', 'ucrania', 'russia', 'rusia', 'china', 'iran', 'irán',
            'north korea', 'corea del norte', 'afghanistan', 'afganistán',
            'syria', 'siria', 'yemen', 'somalia', 'libya', 'libia',
            'myanmar', 'venezuela', 'belarus', 'bielorrusia'
        }
        
        # Países de riesgo medio-alto
        medium_high_risk = {
            'israel', 'palestine', 'palestina', 'turkey', 'turquía',
            'pakistan', 'pakistán', 'india', 'taiwan', 'formosa',
            'south korea', 'corea del sur', 'japan', 'japón'
        }
        
        # Países de riesgo medio
        medium_risk = {
            'usa', 'united states', 'estados unidos', 'uk', 'reino unido',
            'france', 'francia', 'germany', 'alemania', 'poland', 'polonia'
        }
        
        if any(c in country_lower for c in high_risk_countries):
            return 0.9
        elif any(c in country_lower for c in medium_high_risk):
            return 0.7
        elif any(c in country_lower for c in medium_risk):
            return 0.6
        else:
            return 0.5

    def _analyze_escalation_potential(self, text: str) -> float:
        """Analizar potencial de escalamiento."""
        text_lower = text.lower()
        
        escalation_indicators = [
            'escalada', 'escalation', 'intensifica', 'intensifies',
            'aumenta', 'increases', 'empeora', 'worsens',
            'crisis', 'critica', 'critical', 'urgente', 'urgent',
            'inmediato', 'immediate', 'rápido', 'rapid'
        ]
        
        found_indicators = sum(1 for indicator in escalation_indicators if indicator in text_lower)
        return min(found_indicators / len(escalation_indicators) * 2, 1.0)

    def _calculate_final_risk_score(self, sentiment_score: float, sentiment_label: str,
                                  category_confidence: float, keyword_score: float,
                                  geographic_score: float, escalation_score: float,
                                  top_category: str) -> float:
        """Calcular el score final de riesgo combinando todos los factores."""
        
        # Convertir sentimiento a score de riesgo
        if sentiment_label == 'LABEL_2':  # Negativo
            sentiment_risk = sentiment_score
        elif sentiment_label == 'LABEL_0':  # Positivo
            sentiment_risk = 1 - sentiment_score
        else:  # Neutral
            sentiment_risk = 0.5
        
        # Peso de categorías de riesgo
        category_weights = {
            'guerra y conflicto armado': 1.0,
            'terrorismo y violencia': 0.95,
            'crisis política': 0.8,
            'desastre natural': 0.7,
            'crisis económica': 0.6,
            'noticia rutinaria': 0.2
        }
        
        category_risk = category_weights.get(top_category, 0.5) * category_confidence
        
        # Combinar scores con pesos
        final_score = (
            sentiment_risk * 0.15 +      # 15% sentimiento
            category_risk * 0.35 +       # 35% categorización
            keyword_score * 0.25 +       # 25% palabras clave
            geographic_score * 0.15 +    # 15% geografía
            escalation_score * 0.10      # 10% escalamiento
        )
        
        return min(max(final_score, 0.0), 1.0)

    def _score_to_risk_level(self, score: float) -> str:
        """Convertir score numérico a nivel de riesgo."""
        if score >= 0.8:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        else:
            return 'low'

    def _generate_reasoning(self, sentiment_label: str, top_category: str,
                          category_confidence: float, keyword_score: float,
                          geographic_score: float, escalation_score: float,
                          country: str) -> str:
        """Generar explicación del análisis."""
        reasoning_parts = []
        
        # Sentimiento
        sentiment_map = {
            'LABEL_2': 'negativo',
            'LABEL_1': 'neutral', 
            'LABEL_0': 'positivo'
        }
        sentiment_text = sentiment_map.get(sentiment_label, 'neutral')
        reasoning_parts.append(f"Sentimiento: {sentiment_text}")
        
        # Categoría
        reasoning_parts.append(f"Categoría: {top_category} (confianza: {category_confidence:.2f})")
        
        # Palabras clave
        if keyword_score > 0.7:
            reasoning_parts.append("Alto contenido de palabras clave de riesgo")
        elif keyword_score > 0.4:
            reasoning_parts.append("Contenido moderado de palabras clave de riesgo")
        else:
            reasoning_parts.append("Bajo contenido de palabras clave de riesgo")
        
        # Geografía
        if country and geographic_score > 0.8:
            reasoning_parts.append(f"País de alto riesgo: {country}")
        elif country and geographic_score > 0.6:
            reasoning_parts.append(f"País de riesgo moderado: {country}")
        
        # Escalamiento
        if escalation_score > 0.6:
            reasoning_parts.append("Alto potencial de escalamiento")
        
        return ". ".join(reasoning_parts)

    def _fallback_keyword_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """Análisis de respaldo usando solo palabras clave cuando BERT no está disponible."""
        full_text = f"{title}. {content}"
        keyword_score = self._calculate_keyword_risk_score(full_text)
        
        # Convertir a nivel de riesgo
        if keyword_score >= 0.7:
            risk_level = 'high'
        elif keyword_score >= 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'level': risk_level,
            'score': keyword_score,
            'confidence': 0.6,  # Confianza reducida para análisis de respaldo
            'reasoning': f"Análisis basado en palabras clave (score: {keyword_score:.3f})",
            'ai_powered': False,
            'model_used': 'keyword_fallback',
            'analysis_timestamp': datetime.now().isoformat()
        }

    def analyze_risk(self, title: str, content: str, country: str = None) -> Dict[str, Any]:
        """Método principal para análisis de riesgo (alias para compatibilidad)."""
        return self.analyze_risk_level(title, content, country)

# Instancia global para uso en el sistema
bert_risk_analyzer = BertRiskAnalyzer()

def analyze_article_risk(title: str, content: str, country: str = None) -> Dict[str, Any]:
    """Función de conveniencia para análisis de riesgo de artículos."""
    return bert_risk_analyzer.analyze_risk_level(title, content, country)
