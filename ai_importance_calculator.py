"""
AI-powered importance calculator for news articles using Transformers and Groq
"""

import os
import torch
import logging
try:
    from peft import PeftModel
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    logging.warning("PEFT not available, loading LORA adapter will fail")
from datetime import datetime, timezone
import re
import logging
from typing import Dict, Any, Optional
import json

# AI/ML imports
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from transformers import pipeline as hf_pipeline_helper
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available, using fallback")

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logging.warning("Groq not available, using fallback")

class AIImportanceCalculator:
    def __init__(self):
        self.groq_client = None
        self.sentiment_analyzer = None
        self.risk_classifier = None
        self.fine_tuned_model = None
        self.fine_tuned_tokenizer = None
        
        # Initialize Groq client if available and API key is set
        if GROQ_AVAILABLE and os.getenv('GROQ_API_KEY'):
            try:
                self.groq_client = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))
                logging.info("Groq client initialized successfully")
            except Exception as e:
                logging.warning(f"Failed to initialize Groq client: {e}")
        
        # Initialize Transformers models if available
        if TRANSFORMERS_AVAILABLE:
            # Direct load of base-head model
            try:
                self.base_tokenizer = AutoTokenizer.from_pretrained(
                    "leroyrr/bert-base-head"
                )
                self.base_model = AutoModelForSequenceClassification.from_pretrained(
                    "leroyrr/bert-base-head"
                )
                logging.info("Loaded HF base-head model directly")
            except Exception as e:
                logging.warning(f"Failed to load HF base-head model: {e}")
                self.base_tokenizer = None
                self.base_model = None
            # Load base-head model and apply LORA adapter
            self.base_tokenizer = AutoTokenizer.from_pretrained("leroyrr/bert-base-head")
            base = AutoModelForSequenceClassification.from_pretrained("leroyrr/bert-base-head")
            if PEFT_AVAILABLE:
                try:
                    self.lora_model = PeftModel.from_pretrained(
                        base,
                        "leroyrr/bert-for-political-news-sentiment-analysis-lora"
                    )
                    logging.info("Loaded LORA adapter model successfully")
                except Exception as e:
                    logging.warning(f"Failed to load LORA adapter: {e}")
                    self.lora_model = base
            else:
                self.lora_model = base
                logging.warning("PEFT unavailable, using base model only")
            # Setup high-level HF pipeline for importance classification
            try:
                self.hf_pipeline = hf_pipeline_helper(
                    "text-classification",
                    model="leroyrr/bert-for-political-news-sentiment-analysis-lora"
                )
                logging.info("HF text-classification pipeline loaded for importance")
            except Exception as e:
                logging.warning(f"Failed to init HF pipeline: {e}")
                self.hf_pipeline = None
            
            # Fallback to default pipelines
            try:
                # Load sentiment analysis model
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    return_all_scores=True
                )
                logging.info("Sentiment analyzer loaded successfully")
            except Exception as e:
                logging.warning(f"Failed to load sentiment analyzer: {e}")
                
            try:
                # Load a general text classification model for risk assessment
                self.risk_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
                logging.info("Risk classifier loaded successfully")
            except Exception as e:
                logging.warning(f"Failed to load risk classifier: {e}")
    
    def calculate_importance(self, article_data: Dict[str, Any]) -> float:
        """
        Calculate article importance using AI models
        Returns a score from 0-100
        """
        try:
            # Get basic article info
            title = article_data.get('title', '')
            content = article_data.get('content', '') or article_data.get('summary', '')
            location = article_data.get('location', '')
            risk_level = article_data.get('risk_level', 'low')
            published_date = article_data.get('published_date', '')
            source = article_data.get('source', '')
            
            # Combine text for analysis
            text_for_analysis = f"{title}. {content}".strip()
            
            # Start with base importance score
            importance_score = 0.0
            
            # 1. Use HF pipeline if available (100% weight)
            if hasattr(self, 'hf_pipeline') and self.hf_pipeline:
                try:
                    results = self.hf_pipeline(text_for_analysis)
                    # results: list of {'label', 'score'}
                    neg = next((r['score'] for r in results if r['label'].lower()=='negative'), None)
                    score = neg if neg is not None else results[0]['score']
                    importance = max(0, min(100, score * 100))
                    logging.info(f"HF pipeline importance: {importance:.2f}")
                    return importance
                except Exception as e:
                    logging.warning(f"HF pipeline inference failed: {e}")
            # 1. Use LORA-adapted model for inference (if loaded)
            if getattr(self, 'lora_model', None) and getattr(self, 'base_tokenizer', None):
                try:
                    inputs = self.base_tokenizer(
                        text_for_analysis, truncation=True, padding=True, return_tensors='pt'
                    )
                    outputs = self.lora_model(**inputs)
                    logits = outputs.logits.squeeze()
                    probs = torch.softmax(logits, dim=-1).tolist()
                    importance = max(0, min(100, probs[0] * 100))
                    logging.info(f"LORA model importance: {importance:.2f}")
                    return importance
                except Exception as e:
                    logging.warning(f"LORA model inference failed: {e}")
            # 2. Use Groq for advanced semantic analysis (40% weight)
            groq_score = self._analyze_with_groq(text_for_analysis, location)
            importance_score += groq_score * 0.4
            
            # 2. Use Transformers for sentiment and risk analysis (35% weight)
            transformers_score = self._analyze_with_transformers(text_for_analysis, location)
            importance_score += transformers_score * 0.35
            
            # 3. Risk level assessment (15% weight)
            risk_score = self._calculate_risk_score(risk_level)
            importance_score += risk_score * 0.15
            
            # 4. Recency factor (10% weight)
            recency_score = self._calculate_recency_score(published_date)
            importance_score += recency_score * 0.1
            
            # Ensure score is within bounds
            final_score = max(0, min(100, importance_score))
            
            logging.info(f"Article importance calculated: {final_score:.2f} for '{title[:50]}...'")
            return final_score
            
        except Exception as e:
            logging.error(f"Error calculating importance: {e}")
            return self._fallback_importance_calculation(article_data)
    
    def _analyze_with_groq(self, text: str, location: str) -> float:
        """Use Groq for advanced semantic analysis"""
        if not self.groq_client or not text.strip():
            return self._fallback_semantic_analysis(text, location)
        
        try:
            prompt = f"""
            Analyze this news article for geopolitical importance and urgency. 
            Consider factors like:
            - Global impact potential
            - Conflict escalation risk
            - Economic implications
            - Political instability indicators
            - Human rights concerns
            - Natural disaster severity
            
            Article: "{text[:1000]}"
            Location: "{location}"
            
            Rate importance from 0-100 where:
            - 90-100: Global crisis, immediate international attention
            - 70-89: Major regional event, significant global implications
            - 50-69: Important national event, moderate global interest
            - 30-49: Notable local event, limited global impact
            - 0-29: Minor news, minimal significance
            
            Respond with only a number between 0 and 100.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=0.1,
                max_tokens=10
            )
            
            score_text = response.choices[0].message.content.strip()
            score = float(re.search(r'\d+', score_text).group())
            return max(0, min(100, score))
            
        except Exception as e:
            logging.warning(f"Groq analysis failed: {e}")
            return self._fallback_semantic_analysis(text, location)
    
    def _analyze_with_transformers(self, text: str, location: str) -> float:
        """Use Transformers models for sentiment and risk analysis"""
        if not text.strip():
            return 30.0
        
        total_score = 0.0
        
        # Sentiment analysis
        if self.sentiment_analyzer:
            try:
                sentiment_result = self.sentiment_analyzer(text[:512])
                
                # Extract scores for different sentiments
                negative_score = 0
                neutral_score = 0
                positive_score = 0
                
                for result in sentiment_result:
                    if result['label'].lower() in ['negative', 'neg']:
                        negative_score = result['score']
                    elif result['label'].lower() in ['neutral', 'neu']:
                        neutral_score = result['score']
                    elif result['label'].lower() in ['positive', 'pos']:
                        positive_score = result['score']
                
                # Higher negative sentiment often indicates more newsworthy events
                sentiment_importance = (negative_score * 80 + neutral_score * 40 + positive_score * 60)
                total_score += sentiment_importance * 0.6
                
            except Exception as e:
                logging.warning(f"Sentiment analysis failed: {e}")
                total_score += 40.0 * 0.6
        
        # Risk classification
        if self.risk_classifier:
            try:
                risk_labels = [
                    "international conflict",
                    "natural disaster", 
                    "political crisis",
                    "economic crisis",
                    "terrorism",
                    "health emergency",
                    "social unrest",
                    "routine news"
                ]
                
                classification = self.risk_classifier(text[:512], risk_labels)
                
                # Score based on classified risk type
                risk_scores = {
                    "international conflict": 95,
                    "terrorism": 90,
                    "natural disaster": 85,
                    "political crisis": 80,
                    "economic crisis": 70,
                    "health emergency": 75,
                    "social unrest": 65,
                    "routine news": 20
                }
                
                top_label = classification['labels'][0]
                confidence = classification['scores'][0]
                risk_score = risk_scores.get(top_label, 40) * confidence
                total_score += risk_score * 0.4
                
            except Exception as e:
                logging.warning(f"Risk classification failed: {e}")
                total_score += 50.0 * 0.4
        
        return max(0, min(100, total_score))
    
    def _fallback_semantic_analysis(self, text: str, location: str) -> float:
        """Fallback semantic analysis using keyword matching"""
        if not text:
            return 30.0
        
        text_lower = text.lower()
        location_lower = location.lower()
        
        # High-impact keywords with weights
        keyword_scores = {
            # Conflict and violence
            'guerra': 90, 'war': 90, 'conflicto': 85, 'conflict': 85,
            'ataque': 80, 'attack': 80, 'bomba': 85, 'bomb': 85,
            'explosión': 80, 'explosion': 80, 'terrorista': 90, 'terrorist': 90,
            
            # Political events
            'golpe': 85, 'coup': 85, 'elecciones': 60, 'election': 60,
            'gobierno': 50, 'government': 50, 'presidente': 55, 'president': 55,
            
            # Disasters
            'terremoto': 80, 'earthquake': 80, 'tsunami': 85, 'hurricane': 80,
            'incendio': 70, 'fire': 70, 'inundación': 75, 'flood': 75,
            
            # Economic
            'crisis económica': 75, 'economic crisis': 75, 'recession': 70,
            'inflación': 60, 'inflation': 60,
            
            # Health
            'pandemia': 85, 'pandemic': 85, 'brote': 70, 'outbreak': 70,
            
            # Death and casualties
            'muertos': 75, 'dead': 75, 'víctimas': 70, 'victims': 70,
            'heridos': 65, 'injured': 65
        }
        
        # Calculate keyword-based score
        max_score = 0
        for keyword, score in keyword_scores.items():
            if keyword in text_lower:
                max_score = max(max_score, score)
        
        # Location-based adjustments
        high_risk_locations = [
            'ucrania', 'ukraine', 'gaza', 'israel', 'siria', 'syria',
            'afganistán', 'afghanistan', 'yemen', 'myanmar', 'venezuela',
            'colombia', 'méxico', 'mexico'
        ]
        
        location_bonus = 0
        for location_name in high_risk_locations:
            if location_name in location_lower:
                location_bonus = 20
                break
        
        return min(100, max_score + location_bonus)
    
    def _calculate_risk_score(self, risk_level: str) -> float:
        """Convert risk level to numeric score"""
        risk_scores = {
            'high': 100,
            'medium': 60,
            'low': 30,
            'critical': 100,
            'moderate': 50,
            'minimal': 20
        }
        return risk_scores.get(risk_level.lower(), 40)
    
    def _calculate_recency_score(self, published_date: str) -> float:
        """Calculate recency score based on publication date"""
        if not published_date:
            return 40.0  # Default for unknown date
        
        try:
            # Parse various date formats
            if isinstance(published_date, str):
                # Try different date formats
                date_formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                ]
                
                article_date = None
                for fmt in date_formats:
                    try:
                        article_date = datetime.strptime(published_date, fmt)
                        break
                    except ValueError:
                        continue
                
                if not article_date:
                    return 40.0
            else:
                article_date = published_date
            
            # Make timezone-aware if needed
            if article_date.tzinfo is None:
                article_date = article_date.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            hours_diff = (now - article_date).total_seconds() / 3600
            
            # Recency scoring
            if hours_diff < 1:
                return 100  # Very fresh
            elif hours_diff < 6:
                return 85   # Recent
            elif hours_diff < 24:
                return 70   # Today
            elif hours_diff < 72:
                return 50   # This week
            elif hours_diff < 168:  # 1 week
                return 30
            else:
                return 10   # Old news
                
        except Exception as e:
            logging.warning(f"Error parsing date {published_date}: {e}")
            return 40.0
    
    def _fallback_importance_calculation(self, article_data: Dict[str, Any]) -> float:
        """Fallback calculation when AI models fail"""
        risk_level = article_data.get('risk_level', 'low')
        published_date = article_data.get('published_date', '')
        title = article_data.get('title', '')
        
        # Basic scoring
        risk_score = self._calculate_risk_score(risk_level) * 0.5
        recency_score = self._calculate_recency_score(published_date) * 0.3
        semantic_score = self._fallback_semantic_analysis(title, article_data.get('location', '')) * 0.2
        
        return max(0, min(100, risk_score + recency_score + semantic_score))

# Global instance
ai_calculator = AIImportanceCalculator()

def calculate_article_importance(article_data: Dict[str, Any]) -> float:
    """
    Main function to calculate article importance using AI
    """
    return ai_calculator.calculate_importance(article_data)

if __name__ == "__main__":
    # Test the calculator
    test_article = {
        "title": "Escalating Conflict in Eastern Europe Raises Global Security Concerns",
        "content": "Military tensions continue to rise as international diplomats struggle to find peaceful resolution.",
        "location": "Ukraine",
        "risk_level": "high",
        "published_date": "2024-01-15 10:30:00",
        "source": "Reuters"
    }
    
    score = calculate_article_importance(test_article)
    print(f"Test article importance score: {score:.2f}")
