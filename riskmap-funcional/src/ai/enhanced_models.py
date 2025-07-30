"""
Enhanced AI Models for Professional Conflict Monitoring
Implements multilingual NER, sentiment analysis, and conflict classification
using state-of-the-art transformer models.
"""

import logging
import torch
from typing import Dict, List, Tuple, Optional, Any
from transformers import (
    AutoTokenizer, AutoModelForTokenClassification,
    AutoModelForSequenceClassification, pipeline,
    XLMRobertaTokenizer, XLMRobertaForTokenClassification,
    XLMRobertaForSequenceClassification
)
from sentence_transformers import SentenceTransformer
import spacy
from spacy import displacy
import numpy as np
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class MultilingualNERProcessor:
    """
    Advanced multilingual Named Entity Recognition processor
    using XLM-RoBERTa for extracting actors, locations, and organizations
    """
    
    def __init__(self):
        self.model_name = "xlm-roberta-large-finetuned-conll03-english"
        self.tokenizer = None
        self.model = None
        self.ner_pipeline = None
        self.sentence_transformer = None
        self.spacy_models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all NER models and pipelines"""
        try:
            logger.info("Initializing multilingual NER models...")
            
            # XLM-RoBERTa for multilingual NER
            self.tokenizer = AutoTokenizer.from_pretrained(
                "xlm-roberta-large-finetuned-conll03-english"
            )
            self.model = AutoModelForTokenClassification.from_pretrained(
                "xlm-roberta-large-finetuned-conll03-english"
            )
            
            # Create NER pipeline
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Sentence transformer for entity embeddings
            self.sentence_transformer = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2'
            )
            
            # Load spaCy models for different languages
            self._load_spacy_models()
            
            logger.info("NER models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing NER models: {e}")
            raise
    
    def _load_spacy_models(self):
        """Load spaCy models for multiple languages"""
        language_models = {
            'en': 'en_core_web_sm',
            'es': 'es_core_news_sm',
            'fr': 'fr_core_news_sm',
            'de': 'de_core_news_sm',
            'zh': 'zh_core_web_sm',
            'ru': 'ru_core_news_sm'
        }
        
        for lang, model_name in language_models.items():
            try:
                self.spacy_models[lang] = spacy.load(model_name)
                logger.info(f"Loaded spaCy model for {lang}")
            except OSError:
                logger.warning(f"spaCy model {model_name} not found for {lang}")
    
    def extract_entities(self, text: str, language: str = 'en') -> Dict[str, List[Dict]]:
        """
        Extract named entities from text using multiple approaches
        
        Args:
            text: Input text to analyze
            language: Language code (en, es, fr, etc.)
            
        Returns:
            Dictionary with extracted entities by category
        """
        try:
            entities = {
                'persons': [],
                'organizations': [],
                'locations': [],
                'countries': [],
                'armed_groups': [],
                'dates': [],
                'events': []
            }
            
            # XLM-RoBERTa NER
            xlm_entities = self.ner_pipeline(text)
            
            # Process XLM-RoBERTa results
            for entity in xlm_entities:
                entity_info = {
                    'text': entity['word'],
                    'label': entity['entity_group'],
                    'confidence': entity['score'],
                    'start': entity['start'],
                    'end': entity['end'],
                    'method': 'xlm-roberta'
                }
                
                # Map to our categories
                if entity['entity_group'] in ['PER', 'PERSON']:
                    entities['persons'].append(entity_info)
                elif entity['entity_group'] in ['ORG', 'ORGANIZATION']:
                    entities['organizations'].append(entity_info)
                elif entity['entity_group'] in ['LOC', 'LOCATION', 'GPE']:
                    entities['locations'].append(entity_info)
            
            # spaCy NER for additional context
            if language in self.spacy_models:
                spacy_entities = self._extract_spacy_entities(text, language)
                self._merge_entities(entities, spacy_entities)
            
            # Conflict-specific entity detection
            conflict_entities = self._detect_conflict_entities(text)
            self._merge_entities(entities, conflict_entities)
            
            # Generate embeddings for entities
            self._add_entity_embeddings(entities)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}
    
    def _extract_spacy_entities(self, text: str, language: str) -> Dict[str, List[Dict]]:
        """Extract entities using spaCy models"""
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'events': []
        }
        
        try:
            nlp = self.spacy_models[language]
            doc = nlp(text)
            
            for ent in doc.ents:
                entity_info = {
                    'text': ent.text,
                    'label': ent.label_,
                    'confidence': 0.8,  # spaCy doesn't provide confidence scores
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'method': 'spacy'
                }
                
                if ent.label_ in ['PERSON', 'PER']:
                    entities['persons'].append(entity_info)
                elif ent.label_ in ['ORG', 'ORGANIZATION']:
                    entities['organizations'].append(entity_info)
                elif ent.label_ in ['GPE', 'LOC', 'LOCATION']:
                    entities['locations'].append(entity_info)
                elif ent.label_ in ['DATE', 'TIME']:
                    entities['dates'].append(entity_info)
                elif ent.label_ in ['EVENT']:
                    entities['events'].append(entity_info)
                    
        except Exception as e:
            logger.error(f"Error in spaCy NER: {e}")
            
        return entities
    
    def _detect_conflict_entities(self, text: str) -> Dict[str, List[Dict]]:
        """Detect conflict-specific entities using pattern matching"""
        entities = {
            'armed_groups': [],
            'countries': [],
            'organizations': []
        }
        
        # Armed groups patterns
        armed_group_patterns = [
            r'\b(?:ISIS|ISIL|Al-Qaeda|Taliban|Hezbollah|Hamas|PKK|ETA|IRA|FARC|Boko Haram)\b',
            r'\b(?:militia|rebel|insurgent|terrorist|guerrilla)\s+(?:group|forces|movement)\b',
            r'\b(?:armed|military)\s+(?:group|wing|faction)\b'
        ]
        
        # Country patterns (major conflict zones)
        country_patterns = [
            r'\b(?:Syria|Iraq|Afghanistan|Yemen|Somalia|Libya|Ukraine|Myanmar|Mali|Sudan)\b',
            r'\b(?:United States|Russia|China|Iran|Israel|Palestine|Turkey|Saudi Arabia)\b'
        ]
        
        import re
        
        # Extract armed groups
        for pattern in armed_group_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['armed_groups'].append({
                    'text': match.group(),
                    'label': 'ARMED_GROUP',
                    'confidence': 0.7,
                    'start': match.start(),
                    'end': match.end(),
                    'method': 'pattern'
                })
        
        # Extract countries
        for pattern in country_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['countries'].append({
                    'text': match.group(),
                    'label': 'COUNTRY',
                    'confidence': 0.8,
                    'start': match.start(),
                    'end': match.end(),
                    'method': 'pattern'
                })
        
        return entities
    
    def _merge_entities(self, main_entities: Dict, new_entities: Dict):
        """Merge entities from different sources, avoiding duplicates"""
        for category, entity_list in new_entities.items():
            if category in main_entities:
                for new_entity in entity_list:
                    # Check for duplicates based on text and position
                    is_duplicate = False
                    for existing_entity in main_entities[category]:
                        if (abs(new_entity['start'] - existing_entity['start']) < 5 and
                            new_entity['text'].lower() == existing_entity['text'].lower()):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        main_entities[category].append(new_entity)
    
    def _add_entity_embeddings(self, entities: Dict):
        """Add semantic embeddings to entities for similarity analysis"""
        try:
            for category, entity_list in entities.items():
                for entity in entity_list:
                    embedding = self.sentence_transformer.encode(entity['text'])
                    entity['embedding'] = embedding.tolist()
        except Exception as e:
            logger.error(f"Error adding embeddings: {e}")


class ConflictClassifier:
    """
    Advanced conflict classification using transformer models
    Classifies text into conflict types, intensity levels, and humanitarian impact
    """
    
    def __init__(self):
        self.conflict_classifier = None
        self.sentiment_analyzer = None
        self.intensity_classifier = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize classification models"""
        try:
            logger.info("Initializing conflict classification models...")
            
            # Multilingual sentiment analysis
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Conflict type classification (using zero-shot classification)
            self.conflict_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("Classification models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing classification models: {e}")
            raise
    
    def classify_conflict_type(self, text: str) -> Dict[str, Any]:
        """
        Classify the type of conflict described in the text
        
        Args:
            text: Input text to classify
            
        Returns:
            Dictionary with conflict classification results
        """
        try:
            conflict_types = [
                "armed conflict",
                "civil war",
                "international war",
                "terrorism",
                "insurgency",
                "ethnic conflict",
                "religious conflict",
                "territorial dispute",
                "cyber warfare",
                "economic conflict",
                "political crisis",
                "humanitarian crisis"
            ]
            
            result = self.conflict_classifier(text, conflict_types)
            
            return {
                'primary_type': result['labels'][0],
                'confidence': result['scores'][0],
                'all_scores': dict(zip(result['labels'], result['scores'])),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error classifying conflict type: {e}")
            return {}
    
    def analyze_intensity(self, text: str) -> Dict[str, Any]:
        """
        Analyze the intensity level of the conflict
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with intensity analysis results
        """
        try:
            intensity_levels = [
                "low intensity",
                "medium intensity", 
                "high intensity",
                "critical intensity"
            ]
            
            result = self.conflict_classifier(text, intensity_levels)
            
            # Calculate intensity score (0-100)
            intensity_mapping = {
                "low intensity": 25,
                "medium intensity": 50,
                "high intensity": 75,
                "critical intensity": 100
            }
            
            primary_intensity = result['labels'][0]
            intensity_score = intensity_mapping.get(primary_intensity, 50)
            
            return {
                'intensity_level': primary_intensity,
                'intensity_score': intensity_score,
                'confidence': result['scores'][0],
                'all_scores': dict(zip(result['labels'], result['scores'])),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing intensity: {e}")
            return {}
    
    def analyze_humanitarian_impact(self, text: str) -> Dict[str, Any]:
        """
        Analyze humanitarian impact mentioned in the text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with humanitarian impact analysis
        """
        try:
            impact_categories = [
                "civilian casualties",
                "displacement",
                "refugee crisis",
                "infrastructure damage",
                "humanitarian aid needed",
                "food insecurity",
                "medical emergency",
                "education disruption",
                "economic impact"
            ]
            
            result = self.conflict_classifier(text, impact_categories)
            
            # Extract numbers related to casualties and displacement
            import re
            casualty_numbers = re.findall(r'(\d+)\s*(?:killed|dead|casualties|deaths)', text, re.IGNORECASE)
            displacement_numbers = re.findall(r'(\d+)\s*(?:displaced|refugees|evacuated)', text, re.IGNORECASE)
            
            return {
                'primary_impact': result['labels'][0],
                'confidence': result['scores'][0],
                'all_impacts': dict(zip(result['labels'], result['scores'])),
                'casualty_numbers': [int(n) for n in casualty_numbers],
                'displacement_numbers': [int(n) for n in displacement_numbers],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing humanitarian impact: {e}")
            return {}
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the text using multilingual model
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            result = self.sentiment_analyzer(text)
            
            return {
                'sentiment': result[0]['label'],
                'confidence': result[0]['score'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {}


class ActorRelationshipMapper:
    """
    Maps relationships between actors in conflicts using graph analysis
    """
    
    def __init__(self):
        self.entity_processor = MultilingualNERProcessor()
        self.relationship_patterns = self._load_relationship_patterns()
    
    def _load_relationship_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for detecting relationships between actors"""
        return {
            'alliance': [
                r'allied with', r'partnership with', r'cooperation with',
                r'joint operation', r'coalition', r'united with'
            ],
            'conflict': [
                r'fighting against', r'war with', r'conflict with',
                r'attacking', r'bombing', r'strikes against'
            ],
            'support': [
                r'supporting', r'backing', r'funding', r'arming',
                r'providing aid to', r'assistance to'
            ],
            'opposition': [
                r'opposing', r'against', r'condemning', r'sanctions on',
                r'embargo on', r'boycotting'
            ]
        }
    
    def extract_relationships(self, text: str, entities: Dict) -> List[Dict]:
        """
        Extract relationships between actors mentioned in the text
        
        Args:
            text: Input text
            entities: Previously extracted entities
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        try:
            # Get all actors (persons, organizations, countries, armed groups)
            actors = []
            for category in ['persons', 'organizations', 'countries', 'armed_groups']:
                if category in entities:
                    actors.extend(entities[category])
            
            # Find relationships between actors
            import re
            
            for i, actor1 in enumerate(actors):
                for j, actor2 in enumerate(actors):
                    if i >= j:  # Avoid duplicates and self-relationships
                        continue
                    
                    # Look for relationship patterns between actors
                    for rel_type, patterns in self.relationship_patterns.items():
                        for pattern in patterns:
                            # Create regex to find pattern between actors
                            regex_pattern = f"{re.escape(actor1['text'])}.*?{pattern}.*?{re.escape(actor2['text'])}"
                            match = re.search(regex_pattern, text, re.IGNORECASE | re.DOTALL)
                            
                            if match:
                                relationships.append({
                                    'actor1': actor1['text'],
                                    'actor2': actor2['text'],
                                    'relationship_type': rel_type,
                                    'confidence': 0.7,
                                    'evidence': match.group(),
                                    'timestamp': datetime.now().isoformat()
                                })
                                break
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
            return []
    
    def build_actor_graph(self, relationships: List[Dict]) -> Dict:
        """
        Build a graph representation of actor relationships
        
        Args:
            relationships: List of relationship dictionaries
            
        Returns:
            Graph representation as dictionary
        """
        try:
            graph = {
                'nodes': {},
                'edges': [],
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'total_actors': 0,
                    'total_relationships': len(relationships)
                }
            }
            
            # Add nodes (actors)
            actors = set()
            for rel in relationships:
                actors.add(rel['actor1'])
                actors.add(rel['actor2'])
            
            for actor in actors:
                graph['nodes'][actor] = {
                    'id': actor,
                    'type': 'actor',
                    'relationships_count': 0
                }
            
            # Add edges (relationships)
            for rel in relationships:
                graph['edges'].append({
                    'source': rel['actor1'],
                    'target': rel['actor2'],
                    'type': rel['relationship_type'],
                    'confidence': rel['confidence'],
                    'evidence': rel['evidence']
                })
                
                # Update relationship counts
                graph['nodes'][rel['actor1']]['relationships_count'] += 1
                graph['nodes'][rel['actor2']]['relationships_count'] += 1
            
            graph['metadata']['total_actors'] = len(actors)
            
            return graph
            
        except Exception as e:
            logger.error(f"Error building actor graph: {e}")
            return {}