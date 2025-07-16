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
        self._initialize_models()
    
    def _initialize_models(self):
        """Inicializa los modelos de NLP"""
        try:
            # Inicializar NuNER v2.0
            from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
            
            model_name = "numind/NuNER-v2.0"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, grouped_entities=True)
            
            logger.info("✅ NuNER v2.0 model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Could not load NuNER model: {e}")
            # Fallback a spaCy
            try:
                import spacy
                self.ner_model = spacy.load("en_core_web_sm")
                logger.info("✅ Fallback to spaCy model")
            except Exception as e2:
                logger.error(f"Could not load any NER model: {e2}")
        
        try:
            # Inicializar modelo de sentimientos
            from transformers import pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis", 
                model="nlptown/bert-base-multilingual-uncased-sentiment"
            )
            logger.info("✅ Sentiment analysis model loaded")
            
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
        
        for entity_text, entity_label in entities:
            entity_lower = entity_text.lower()
            
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
            geopolitical_entities[key] = list(set(geopolitical_entities[key]))
        
        return geopolitical_entities
    
    def calculate_risk_score_advanced(self, text: str, entities: Dict[str, List[str]]) -> float:
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
            if any(risk_loc in location.lower() for risk_loc in high_risk_locations):
                risk_score += 1.0
        
        # Normalizar entre 0 y 10
        risk_score = min(10.0, max(0.0, risk_score))
        
        return risk_score
    
    def analyze_article_comprehensive(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análisis comprehensivo de un artículo combinando todas las técnicas
        """
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
        title_sentiment = self.analyze_sentiment_multilevel(title) if title else {'score': 0.0}
        title_entities = self.extract_entities(title) if title else []
        
        return {
            'entities': entities,
            'sentiment': sentiment_analysis,
            'title_sentiment': title_sentiment,
            'risk_score': risk_score,
            'title_entities': title_entities,
            'analysis_timestamp': datetime.now().isoformat(),
            'key_persons': entities.get('persons', [])[:5],  # Top 5 personas
            'key_locations': entities.get('locations', [])[:5],  # Top 5 ubicaciones
            'conflict_indicators': entities.get('conflicts', []),
            'total_entities': sum(len(v) for v in entities.values())
        }

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
