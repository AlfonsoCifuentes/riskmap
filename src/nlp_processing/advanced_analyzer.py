"""
Analizador avanzado de NLP basado en técnicas del notebook de análisis político
Integra NuNER, análisis de sentimientos y modelado de temas
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import re
import string
from datetime import datetime

logger = logging.getLogger(__name__)


class AdvancedNLPAnalyzer:
    """
    Analizador avanzado que combina múltiples técnicas de NLP
    """

    def __init__(self):
        self.ner_pipeline = None
        self.sentiment_pipeline = None
        self.lda_model = None
        self.vectorizer = None
        self.version = "2.1.0"  # Version tracking for model updates
        self.processing_stats = {
            'total_processed': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'processing_times': []
        }
        self._initialize_models()

    def _initialize_models(self):
        """Inicializa los modelos de NLP"""
        try:
            # Inicializar NuNER v2.0
            from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

            model_name = "numind/NuNER-v2.0"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.ner_pipeline = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                grouped_entities=True)

            logger.info("NuNER v2.0 model loaded successfully")

        except Exception as e:
            logger.warning(f"Could not load NuNER model: {e}")
            # Fallback a spaCy
            try:
                import spacy
                self.ner_model = spacy.load("en_core_web_sm")
                logger.info("Fallback to spaCy model")
            except Exception as e2:
                logger.error(f"Could not load any NER model: {e2}")

        try:
            # Inicializar modelo de sentimientos
            from transformers import pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment"
            )
            logger.info("Sentiment analysis model loaded")

        except Exception as e:
            logger.warning(f"Could not load sentiment model: {e}")

    def extract_entities_nuner(self, text: str) -> List[Tuple[str, str]]:
        """
        Extrae entidades usando NuNER v2.0
        """
        if not text or not self.ner_pipeline:
            return []

        try:
            # Limitar texto a longitud manejable
            text = text[:2000]
            ner_results = self.ner_pipeline(text)

            entities = []
            for entity in ner_results:
                entity_text = entity['word'].strip()
                entity_label = entity['entity_group']
                confidence = entity.get('score', 0.0)

                # Filtrar entidades con baja confianza
                if confidence > 0.7 and len(entity_text) > 2:
                    entities.append((entity_text, entity_label))

            return entities

        except Exception as e:
            logger.error(f"Error in NuNER extraction: {e}")
            return []

    def extract_entities_spacy(self, text: str) -> List[Tuple[str, str]]:
        """
        Fallback usando spaCy
        """
        if not text or not hasattr(self, 'ner_model'):
            return []

        try:
            doc = self.ner_model(text[:2000])
            entities = []

            for ent in doc.ents:
                if len(ent.text.strip()) > 2:
                    entities.append((ent.text.strip(), ent.label_))

            return entities

        except Exception as e:
            logger.error(f"Error in spaCy extraction: {e}")
            return []

    def extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """
        Extrae entidades usando el mejor modelo disponible
        """
        if self.ner_pipeline:
            return self.extract_entities_nuner(text)
        else:
            return self.extract_entities_spacy(text)

    def analyze_sentiment_multilevel(self, text: str) -> Dict[str, Any]:
        """
        Análisis de sentimiento multinivel como en el notebook
        """
        if not text or not self.sentiment_pipeline:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}

        try:
            # Dividir texto en fragmentos manejables
            chunks = self._split_text(text, max_length=500)
            sentiments = []

            for chunk in chunks:
                if chunk.strip():
                    results = self.sentiment_pipeline(chunk)
                    for res in results:
                        label = res['label']
                        confidence = res['score']

                        # Convertir etiquetas de estrellas a score numérico
                        if label.startswith('1') or label.startswith('2'):
                            score = -1.0  # Negativo
                        elif label.startswith('4') or label.startswith('5'):
                            score = 1.0   # Positivo
                        else:
                            score = 0.0   # Neutral

                        sentiments.append({
                            'score': score,
                            'confidence': confidence,
                            'raw_label': label
                        })

            if sentiments:
                avg_score = np.mean([s['score'] for s in sentiments])
                avg_confidence = np.mean([s['confidence'] for s in sentiments])

                # Determinar etiqueta final
                if avg_score > 0.3:
                    label = 'positive'
                elif avg_score < -0.3:
                    label = 'negative'
                else:
                    label = 'neutral'

                return {
                    'score': float(avg_score),
                    'label': label,
                    'confidence': float(avg_confidence),
                    'num_fragments': len(sentiments)
                }

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")

        return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}

    def _split_text(self, text: str, max_length: int = 500) -> List[str]:
        """
        Divide texto en fragmentos manejables manteniendo oraciones completas
        """
        sentences = text.split('.')
        chunks = []
        current_chunk = ''

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def extract_geopolitical_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae entidades específicamente relevantes para análisis geopolítico
        """
        try:
            entities = self.extract_entities(text)

            geopolitical_entities = {
                'persons': [],
                'organizations': [],
                'locations': [],
                'events': [],
                'conflicts': []
            }

            # Palabras clave para identificar conflictos y eventos
            conflict_keywords = [
                'war', 'conflict', 'crisis', 'attack', 'invasion', 'strike',
                'protest', 'revolution', 'coup', 'terrorism', 'violence'
            ]

            # Asegurar que entities es una lista válida
            if not entities or not isinstance(entities, list):
                return geopolitical_entities

            for entity_data in entities:
                # Validar que entity_data es una tupla válida
                if not isinstance(entity_data, (tuple, list)) or len(entity_data) < 2:
                    continue
                    
                entity_text, entity_label = entity_data[0], entity_data[1]
                
                # Validar que los valores no son None
                if not entity_text or not entity_label:
                    continue
                    
                entity_lower = str(entity_text).lower()

                # Clasificar entidades según tipo
                if entity_label in ['PERSON', 'PER']:
                    geopolitical_entities['persons'].append(entity_text)
                elif entity_label in ['ORG', 'ORGANIZATION']:
                    geopolitical_entities['organizations'].append(entity_text)
                elif entity_label in ['LOC', 'LOCATION', 'GPE']:
                    geopolitical_entities['locations'].append(entity_text)
                elif entity_label in ['EVENT', 'MISC']:
                    geopolitical_entities['events'].append(entity_text)

                # Identificar conflictos por palabras clave
                if any(keyword in entity_lower for keyword in conflict_keywords):
                    geopolitical_entities['conflicts'].append(entity_text)

            # Eliminar duplicados y ordenar
            for key in geopolitical_entities:
                if geopolitical_entities[key]:  # Solo procesar si no está vacía
                    geopolitical_entities[key] = list(set(geopolitical_entities[key]))
                else:
                    geopolitical_entities[key] = []  # Asegurar que es una lista vacía

            return geopolitical_entities
            
        except Exception as e:
            logger.error(f"Error in extract_geopolitical_entities: {e}")
            # Retornar estructura básica válida en caso de error
            return {
                'persons': [],
                'organizations': [],
                'locations': [],
                'events': [],
                'conflicts': []
            }

    def calculate_risk_score_advanced(
            self, text: str, entities: Dict[str, List[str]]) -> float:
        """
        Calcula puntaje de riesgo avanzado basado en entidades y contenido
        """
        risk_score = 1.0  # Score base

        # Factores de riesgo por palabras clave
        high_risk_keywords = [
            'war', 'guerra', 'conflict', 'conflicto', 'attack', 'ataque',
            'bomb', 'explosion', 'terror', 'violence', 'violencia',
            'invasion', 'military', 'missile', 'nuclear', 'weapons',
            'crisis', 'emergency', 'threat', 'amenaza'
        ]

        medium_risk_keywords = [
            'protest', 'manifestation', 'riot', 'strike', 'election',
            'diplomatic', 'sanction', 'embargo', 'tension', 'dispute'
        ]

        text_lower = text.lower()

        # Incrementar por palabras clave
        for keyword in high_risk_keywords:
            if keyword in text_lower:
                risk_score += 2.0

        for keyword in medium_risk_keywords:
            if keyword in text_lower:
                risk_score += 1.0

        # Incrementar por tipos de entidades
        risk_score += len(entities.get('conflicts', [])) * 1.5
        risk_score += len(entities.get('persons', [])) * 0.3
        risk_score += len(entities.get('organizations', [])) * 0.2

        # Factores de ubicación (algunos países/regiones más volátiles)
        high_risk_locations = [
            'ukraine', 'russia', 'syria', 'afghanistan', 'iraq',
            'palestine', 'israel', 'iran', 'north korea', 'china'
        ]

        for location in entities.get('locations', []):
            if any(risk_loc in location.lower()
                   for risk_loc in high_risk_locations):
                risk_score += 1.0

        # Normalizar entre 0 y 10
        risk_score = min(10.0, max(0.0, risk_score))

        return risk_score

    def analyze_article_comprehensive(
            self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análisis comprehensivo de un artículo combinando todas las técnicas
        """
        start_time = datetime.now()
        processing_timestamp = start_time.isoformat()
        
        try:
            self.processing_stats['total_processed'] += 1
            
            title = article_data.get('title', '')
            description = article_data.get('description', '')
            content = article_data.get('content', '')

            # Combinar todo el texto
            full_text = f"{title} {description} {content}"

            # Extraer entidades
            entities = self.extract_geopolitical_entities(full_text)

            # Análisis de sentimiento
            sentiment_analysis = self.analyze_sentiment_multilevel(full_text)

            # Calcular score de riesgo
            risk_score = self.calculate_risk_score_advanced(full_text, entities)

            # Análisis específico del título (más peso)
            title_sentiment = self.analyze_sentiment_multilevel(title) if title else {
                'score': 0.0}
            title_entities = self.extract_entities(title) if title else []
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            self.processing_stats['processing_times'].append(processing_time)
            self.processing_stats['successful_analyses'] += 1

            return {
                'entities': entities,
                'sentiment': sentiment_analysis,
                'title_sentiment': title_sentiment,
                'risk_score': risk_score,
                'title_entities': title_entities,
                'analysis_timestamp': processing_timestamp,
                'processing_time_seconds': processing_time,
                'nlp_version': self.version,
                'key_persons': entities.get('persons', [])[:5] if entities.get('persons') else [],  # Top 5 personas
                'key_locations': entities.get('locations', [])[:5] if entities.get('locations') else [],  # Top 5 ubicaciones
                'conflict_indicators': entities.get('conflicts', []) if entities.get('conflicts') else [],
                'total_entities': sum(len(v) for v in entities.values() if v is not None and isinstance(v, list))
            }
            
        except Exception as e:
            self.processing_stats['failed_analyses'] += 1
            logger.error(f"Error in comprehensive analysis: {e}")
            return {
                'error': str(e),
                'analysis_timestamp': processing_timestamp,
                'processing_time_seconds': 0.0,
                'nlp_version': self.version
            }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get current processing statistics for monitoring
        """
        avg_processing_time = (
            sum(self.processing_stats['processing_times']) / 
            len(self.processing_stats['processing_times'])
        ) if self.processing_stats['processing_times'] else 0.0
        
        return {
            'total_processed': self.processing_stats['total_processed'],
            'successful_analyses': self.processing_stats['successful_analyses'],
            'failed_analyses': self.processing_stats['failed_analyses'],
            'success_rate': (
                self.processing_stats['successful_analyses'] / 
                self.processing_stats['total_processed'] * 100
            ) if self.processing_stats['total_processed'] > 0 else 0.0,
            'average_processing_time': avg_processing_time,
            'nlp_version': self.version,
            'models_loaded': {
                'ner_pipeline': self.ner_pipeline is not None,
                'sentiment_pipeline': self.sentiment_pipeline is not None
            }
        }
    
    def analyze_batch(self, articles_data: List[Dict[str, Any]], 
                     batch_size: int = 50) -> List[Dict[str, Any]]:
        """
        Process articles in batches for better performance and memory management
        """
        results = []
        total_articles = len(articles_data)
        
        logger.info(f"Starting batch processing of {total_articles} articles in batches of {batch_size}")
        
        for i in range(0, total_articles, batch_size):
            batch = articles_data[i:i + batch_size]
            batch_start_time = datetime.now()
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_articles + batch_size - 1)//batch_size}")
            
            batch_results = []
            for article_data in batch:
                result = self.analyze_article_comprehensive(article_data)
                batch_results.append(result)
            
            results.extend(batch_results)
            
            batch_time = (datetime.now() - batch_start_time).total_seconds()
            logger.info(f"Batch processed in {batch_time:.2f} seconds")
            
            # Alert if processing is taking too long
            if batch_time > 60:  # More than 1 minute per batch
                logger.warning(f"⚠️ SLOW PROCESSING ALERT: Batch took {batch_time:.2f}s")
        
        return results
    
    def check_processing_health(self) -> Dict[str, Any]:
        """
        Check processing health and trigger alerts if needed
        """
        stats = self.get_processing_stats()
        health_status = {
            'status': 'healthy',
            'alerts': [],
            'recommendations': []
        }
        
        # Check success rate
        if stats['success_rate'] < 80:
            health_status['status'] = 'warning'
            health_status['alerts'].append(f"Low success rate: {stats['success_rate']:.1f}%")
            health_status['recommendations'].append("Check model loading and input data quality")
        
        # Check processing time
        if stats['average_processing_time'] > 5.0:
            health_status['status'] = 'warning' 
            health_status['alerts'].append(f"Slow processing: {stats['average_processing_time']:.2f}s avg")
            health_status['recommendations'].append("Consider using batch processing or model optimization")
        
        # Check if models are loaded
        if not all(stats['models_loaded'].values()):
            health_status['status'] = 'error'
            health_status['alerts'].append("Some NLP models failed to load")
            health_status['recommendations'].append("Check model dependencies and initialization")
        
        return health_status


def preprocess_text_advanced(text: str) -> str:
    """
    Preprocesamiento avanzado de texto basado en el notebook
    """
    if not text:
        return ""

    # Convertir a minúsculas
    text = text.lower()

    # Remover URLs
    text = re.sub(r'http\S+|www.\S+', '', text)

    # Remover caracteres especiales y números, pero mantener espacios
    text = re.sub(f'[{re.escape(string.punctuation)}0-9]', ' ', text)

    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def get_nlp_analyzer() -> AdvancedNLPAnalyzer:
    """
    Obtiene una instancia del analizador NLP avanzado
    """
    return AdvancedNLPAnalyzer()
