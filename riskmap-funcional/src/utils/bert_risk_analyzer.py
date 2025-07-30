#!/usr/bin/env python3
"""
BERT-powered Risk Analyzer for Geopolitical Intelligence System
Uses specialized BERT models for geopolitical risk classification
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config

logger = logging.getLogger(__name__)

class BERTRiskAnalyzer:
    """BERT-powered geopolitical risk analyzer using specialized models."""
    
    def __init__(self):
        self.models = [
            "joeddav/xlm-roberta-large-xnli",  # Multilingual classification (working)
            "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli",  # Lightweight multilingual
            "facebook/bart-large-mnli"  # Alternative classification model
        ]
        self.current_model = None
        self.pipeline = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the first available model."""
        for model_name in self.models:
            try:
                from transformers import pipeline
                logger.info(f"Attempting to load model: {model_name}")
                
                # Create zero-shot classification pipeline
                self.pipeline = pipeline(
                    "zero-shot-classification",
                    model=model_name,
                    device=0 if model_name == self.models[0] else -1  # Use GPU for crisis-bert if available, CPU for others
                )
                self.current_model = model_name
                logger.info(f"Successfully loaded model: {model_name}")
                break
                
            except Exception as e:
                logger.warning(f"Failed to load {model_name}: {e}")
                continue
        
        if not self.pipeline:
            logger.error("Failed to load any specialized models, will use basic analysis")
    
    def analyze_risk(self, title: str, content: str, country: str = None) -> Dict[str, any]:
        """
        Analyze geopolitical risk using specialized BERT models.
        
        Args:
            title: Article title
            content: Full article content
            country: Country/region if known
            
        Returns:
            Dict with risk analysis results
        """
        try:
            # Prepare the text for analysis
            full_text = f"{title}. {content}"
            if country:
                full_text = f"[{country}] {full_text}"
            
            # Truncate if too long (BERT models have token limits)
            if len(full_text) > 2000:
                full_text = full_text[:2000] + "..."
            
            # Try BERT-based analysis first
            if self.pipeline:
                bert_result = self._analyze_with_bert(full_text, title, content)
                if bert_result:
                    return bert_result
            
            # Fallback to basic keyword analysis
            logger.warning("BERT analysis failed, using keyword analysis")
            return self._basic_keyword_analysis(title, content)
            
        except Exception as e:
            logger.error(f"AI risk analysis error: {e}")
            return self._basic_keyword_analysis(title, content)
    
    def _analyze_with_bert(self, text: str, title: str, content: str) -> Optional[Dict]:
        """Analyze risk using BERT-based zero-shot classification."""
        try:
            # Define risk categories with detailed descriptions
            risk_labels = [
                "high geopolitical risk - war, military conflict, terrorism, nuclear threats, coups, major crises",
                "medium geopolitical risk - diplomatic tensions, protests, sanctions, political instability, border disputes", 
                "low geopolitical risk - cooperation, agreements, routine politics, economic news, cultural events"
            ]
            
            # Perform zero-shot classification
            result = self.pipeline(text, risk_labels)
            
            # Extract the results
            labels = result['labels']
            scores = result['scores']
            
            # Map the top prediction to our risk levels
            top_label = labels[0]
            top_score = scores[0]
            
            if "high geopolitical risk" in top_label:
                risk_level = "high"
                base_score = 0.8
            elif "medium geopolitical risk" in top_label:
                risk_level = "medium" 
                base_score = 0.5
            else:
                risk_level = "low"
                base_score = 0.2
            
            # Adjust score based on model confidence
            final_score = base_score * top_score
            
            # Enhanced analysis for high-confidence predictions
            reasoning = self._generate_reasoning(text, title, content, risk_level, top_score)
            key_factors = self._extract_key_factors(text, title, content, risk_level)
            
            # Geographic impact assessment
            geographic_impact = self._assess_geographic_impact(text, content)
            
            # Escalation potential
            escalation_potential = self._assess_escalation_potential(text, content, risk_level)
            
            return {
                'level': risk_level,
                'score': round(final_score, 3),
                'confidence': round(top_score, 3),
                'reasoning': reasoning,
                'key_factors': key_factors,
                'potential_escalation': escalation_potential,
                'geographic_impact': geographic_impact,
                'model_used': self.current_model,
                'ai_powered': True,
                'all_scores': {
                    'high': scores[labels.index([l for l in labels if "high" in l][0])] if any("high" in l for l in labels) else 0,
                    'medium': scores[labels.index([l for l in labels if "medium" in l][0])] if any("medium" in l for l in labels) else 0,
                    'low': scores[labels.index([l for l in labels if "low" in l][0])] if any("low" in l for l in labels) else 0
                }
            }
            
        except Exception as e:
            logger.error(f"BERT analysis failed: {e}")
            return None
    
    def _generate_reasoning(self, text: str, title: str, content: str, risk_level: str, confidence: float) -> str:
        """Generate human-readable reasoning for the risk assessment."""
        text_lower = text.lower()
        
        # Key indicators found
        high_risk_indicators = []
        medium_risk_indicators = []
        
        # Check for specific high-risk terms
        high_risk_terms = {
            'war': ['war', 'guerra', 'guerre'],
            'conflict': ['conflict', 'conflicto', 'fighting', 'combat'],
            'attack': ['attack', 'ataque', 'bombing', 'missile', 'strike'],
            'terrorism': ['terrorism', 'terrorist', 'bomb', 'explosion'],
            'nuclear': ['nuclear', 'atomic'],
            'crisis': ['crisis', 'emergency', 'threat'],
            'military': ['military', 'army', 'forces', 'troops'],
            'violence': ['violence', 'violent', 'killing', 'death']
        }
        
        medium_risk_terms = {
            'tension': ['tension', 'dispute', 'disagreement'],
            'protest': ['protest', 'demonstration', 'rally'],
            'political': ['political', 'government', 'election'],
            'diplomatic': ['diplomatic', 'negotiation', 'talks'],
            'economic': ['sanctions', 'embargo', 'trade war']
        }
        
        for category, terms in high_risk_terms.items():
            if any(term in text_lower for term in terms):
                high_risk_indicators.append(category)
        
        for category, terms in medium_risk_terms.items():
            if any(term in text_lower for term in terms):
                medium_risk_indicators.append(category)
        
        # Generate reasoning based on findings
        if risk_level == 'high':
            reasoning = f"Classified as HIGH risk (confidence: {confidence:.2f}) due to presence of serious geopolitical threats."
            if high_risk_indicators:
                reasoning += f" Key indicators: {', '.join(high_risk_indicators)}."
        elif risk_level == 'medium':
            reasoning = f"Classified as MEDIUM risk (confidence: {confidence:.2f}) due to political tensions or instability."
            if medium_risk_indicators:
                reasoning += f" Key indicators: {', '.join(medium_risk_indicators)}."
        else:
            reasoning = f"Classified as LOW risk (confidence: {confidence:.2f}) - appears to be routine news or positive developments."
        
        return reasoning
    
    def _extract_key_factors(self, text: str, title: str, content: str, risk_level: str) -> List[str]:
        """Extract key factors contributing to the risk assessment."""
        factors = []
        text_lower = text.lower()
        
        # Geographic factors
        regions = ['ukraine', 'russia', 'israel', 'gaza', 'iran', 'syria', 'china', 'taiwan', 'north korea']
        found_regions = [region for region in regions if region in text_lower]
        if found_regions:
            factors.extend([f"High-risk region: {region}" for region in found_regions[:2]])
        
        # Event type factors
        if risk_level == 'high':
            if any(term in text_lower for term in ['war', 'attack', 'bombing', 'missile']):
                factors.append("Active military conflict")
            if any(term in text_lower for term in ['nuclear', 'atomic']):
                factors.append("Nuclear implications")
            if any(term in text_lower for term in ['terrorism', 'terrorist']):
                factors.append("Terrorism threat")
            if any(term in text_lower for term in ['crisis', 'emergency']):
                factors.append("Crisis situation")
        
        elif risk_level == 'medium':
            if any(term in text_lower for term in ['protest', 'demonstration']):
                factors.append("Civil unrest")
            if any(term in text_lower for term in ['sanctions', 'embargo']):
                factors.append("Economic pressure")
            if any(term in text_lower for term in ['diplomatic', 'negotiation']):
                factors.append("Diplomatic tensions")
        
        return factors[:5]  # Limit to top 5 factors
    
    def _assess_geographic_impact(self, text: str, content: str) -> str:
        """Assess the geographic scope of impact."""
        text_lower = text.lower()
        
        # Global indicators
        global_terms = ['global', 'international', 'worldwide', 'nato', 'un', 'united nations']
        if any(term in text_lower for term in global_terms):
            return "Global"
        
        # Regional indicators
        regional_terms = ['europe', 'middle east', 'asia', 'africa', 'americas']
        if any(term in text_lower for term in regional_terms):
            return "Regional"
        
        # Multiple countries
        countries = ['usa', 'china', 'russia', 'iran', 'israel', 'ukraine', 'syria', 'north korea']
        found_countries = [country for country in countries if country in text_lower]
        if len(found_countries) > 1:
            return "Multi-national"
        
        return "Local"
    
    def _assess_escalation_potential(self, text: str, content: str, risk_level: str) -> str:
        """Assess the potential for escalation."""
        text_lower = text.lower()
        
        if risk_level == 'high':
            if any(term in text_lower for term in ['escalate', 'escalation', 'spread', 'expand']):
                return "High escalation risk"
            elif any(term in text_lower for term in ['ceasefire', 'peace', 'negotiation', 'talks']):
                return "De-escalation efforts ongoing"
            else:
                return "Situation remains critical"
        
        elif risk_level == 'medium':
            if any(term in text_lower for term in ['tension', 'dispute', 'disagreement']):
                return "Potential for escalation"
            else:
                return "Situation being monitored"
        
        return "Low escalation risk"
    
    def _basic_keyword_analysis(self, title: str, content: str) -> Dict:
        """Basic keyword-based analysis as fallback when BERT fails."""
        text = f"{title} {content}".lower()
        
        high_risk_keywords = [
            'war', 'guerra', 'attack', 'ataque', 'bombing', 'missile', 'nuclear',
            'terrorism', 'terrorist', 'coup', 'invasion', 'crisis', 'emergency',
            'hamas', 'israel', 'gaza', 'ukraine', 'russia', 'putin', 'zelensky',
            'iran', 'syria', 'north korea', 'china', 'taiwan', 'conflict',
            'military', 'bomb', 'explosion', 'threat', 'sanctions', 'embargo',
            'ceasefire', 'fighting', 'combat', 'strike', 'forces'
        ]
        
        medium_risk_keywords = [
            'tension', 'dispute', 'protest', 'demonstration', 'diplomatic',
            'negotiation', 'border', 'election', 'political', 'government',
            'minister', 'parliament', 'trade war', 'economic pressure'
        ]
        
        high_matches = sum(1 for keyword in high_risk_keywords if keyword in text)
        medium_matches = sum(1 for keyword in medium_risk_keywords if keyword in text)
        
        # More aggressive classification for geopolitical content
        if high_matches >= 2:
            level = 'high'
            score = 0.8
        elif high_matches >= 1:
            level = 'medium'  # Promote single high-risk keywords to medium
            score = 0.6
        elif medium_matches >= 2:
            level = 'medium'
            score = 0.5
        else:
            level = 'low'
            score = 0.2
        
        return {
            'level': level,
            'score': score,
            'confidence': 0.7,  # Higher confidence for keyword analysis
            'reasoning': f'Keyword-based analysis: {high_matches} high-risk, {medium_matches} medium-risk keywords found',
            'key_factors': [f"{high_matches} high-risk keywords", f"{medium_matches} medium-risk keywords"],
            'potential_escalation': 'Unknown',
            'geographic_impact': 'Unknown',
            'model_used': 'keyword_fallback',
            'ai_powered': False
        }

def main():
    """Test the BERT risk analyzer."""
    analyzer = BERTRiskAnalyzer()
    
    # Test cases
    test_articles = [
        {
            'title': 'Hamas envía propuesta de cese al fuego a Israel mientras la hambruna se extiende en Gaza',
            'content': 'Un oficial israelí dice que la última versión del grupo es factible mientras que las dos partes se preparan para nuevas negociaciones. La situación humanitaria en Gaza continúa deteriorándose con miles de civiles afectados por la falta de alimentos y suministros médicos.',
            'country': 'Israel'
        },
        {
            'title': 'Ucranianos protestan por segundo día por ley de lucha contra la corrupción',
            'content': 'Miles de ucranianos se reunieron por segundo día en Kiev y Lviv manifestando contra una nueva ley considerada insuficiente para combatir la corrupción. Los manifestantes exigen reformas más profundas.',
            'country': 'Ukraine'
        },
        {
            'title': 'Cumbre económica internacional busca fortalecer cooperación comercial',
            'content': 'Líderes de 20 países se reúnen para discutir nuevos acuerdos comerciales y fortalecer la cooperación económica internacional en un ambiente de diálogo constructivo.',
            'country': 'Global'
        },
        {
            'title': 'Explosión en base militar causa múltiples víctimas',
            'content': 'Una explosión en una base militar ha causado múltiples víctimas. Las autoridades investigan si se trata de un ataque terrorista o un accidente. La zona ha sido evacuada.',
            'country': 'Unknown'
        }
    ]
    
    for article in test_articles:
        print(f"\n{'='*60}")
        print(f"TESTING: {article['title'][:50]}...")
        print(f"{'='*60}")
        
        result = analyzer.analyze_risk(
            title=article['title'],
            content=article['content'],
            country=article['country']
        )
        
        print(f"Risk Level: {result['level'].upper()}")
        print(f"Score: {result['score']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Model Used: {result['model_used']}")
        print(f"AI Powered: {result['ai_powered']}")
        print(f"Reasoning: {result['reasoning']}")
        if result['key_factors']:
            print(f"Key Factors: {', '.join(result['key_factors'])}")
        print(f"Geographic Impact: {result['geographic_impact']}")
        print(f"Escalation Potential: {result['potential_escalation']}")
        
        if 'all_scores' in result:
            print(f"All Scores: High={result['all_scores']['high']:.3f}, Medium={result['all_scores']['medium']:.3f}, Low={result['all_scores']['low']:.3f}")

if __name__ == "__main__":
    main()