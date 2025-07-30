#!/usr/bin/env python3
"""
AI-powered Risk Analyzer for Geopolitical Intelligence System
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

class AIRiskAnalyzer:
    """AI-powered geopolitical risk analyzer using specialized BERT models."""
    
    def __init__(self):
        self.models = [
            "joeddav/crisis-bert",  # Specialized for crisis detection
            "joeddav/xlm-roberta-large-xnli",  # Multilingual classification
            "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"  # Lightweight multilingual
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
                    device_map="auto" if model_name == self.models[0] else "cpu"  # Use GPU for crisis-bert if available
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
        Analyze geopolitical risk using AI to read and understand the full article.
        
        Args:
            title: Article title
            content: Full article content
            country: Country/region if known
            
        Returns:
            Dict with risk analysis results
        """
        try:
            # Prepare the text for analysis
            full_text = f"Título: {title}\n\nContenido: {content}"
            if country:
                full_text += f"\n\nPaís/Región: {country}"
            
            # Create the AI prompt for risk analysis
            prompt = self._create_risk_analysis_prompt(full_text)
            
            # Try different AI models in order of preference
            analysis_result = None
            
            # Try Groq first (fastest and most reliable)
            if self.groq_key and not analysis_result:
                analysis_result = self._analyze_with_groq(prompt)
            
            # Try OpenAI as fallback
            if self.openai_key and not analysis_result:
                analysis_result = self._analyze_with_openai(prompt)
            
            # Try DeepSeek as second fallback
            if self.deepseek_key and not analysis_result:
                analysis_result = self._analyze_with_deepseek(prompt)
            
            # If all AI models fail, use basic keyword analysis as last resort
            if not analysis_result:
                logger.warning("All AI models failed, using basic keyword analysis")
                return self._basic_keyword_analysis(title, content)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI risk analysis error: {e}")
            return self._basic_keyword_analysis(title, content)
    
    def _create_risk_analysis_prompt(self, text: str) -> str:
        """Create a detailed prompt for AI risk analysis."""
        return f"""
Eres un analista geopolítico experto. Analiza el siguiente artículo de noticias y determina su nivel de riesgo geopolítico.

ARTÍCULO:
{text}

INSTRUCCIONES:
1. Lee y comprende completamente el contenido del artículo
2. Evalúa el nivel de riesgo geopolítico basándote en:
   - Gravedad de los eventos descritos
   - Potencial de escalada o conflicto
   - Impacto en la estabilidad regional/global
   - Amenazas a la seguridad internacional
   - Implicaciones económicas y políticas

3. Clasifica el riesgo como:
   - HIGH: Guerra activa, ataques militares, terrorismo, crisis nuclear, golpes de estado, genocidio, amenazas existenciales
   - MEDIUM: Tensiones diplomáticas serias, protestas violentas, sanciones importantes, crisis económicas, disputas territoriales
   - LOW: Cooperación internacional, acuerdos diplomáticos, noticias rutinarias, eventos deportivos/culturales

4. Responde ÚNICAMENTE en formato JSON válido:
{{
    "risk_level": "HIGH|MEDIUM|LOW",
    "confidence": 0.0-1.0,
    "reasoning": "Explicación detallada de por qué asignaste este nivel de riesgo",
    "key_factors": ["factor1", "factor2", "factor3"],
    "potential_escalation": "Descripción del potencial de escalada",
    "geographic_impact": "Alcance geográfico del impacto",
    "severity_score": 0.0-1.0
}}

IMPORTANTE: 
- Sé estricto en la clasificación
- HIGH solo para eventos realmente graves
- Considera el contexto completo, no solo palabras clave
- Responde SOLO con JSON válido, sin texto adicional
"""

    def _analyze_with_groq(self, prompt: str) -> Optional[Dict]:
        """Analyze risk using Groq API."""
        try:
            import requests
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "Eres un analista geopolítico experto. Responde solo en JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            
            # Parse JSON response
            analysis = json.loads(ai_response)
            
            # Validate and normalize the response
            return self._validate_and_normalize_response(analysis, "groq")
            
        except Exception as e:
            logger.error(f"Groq analysis failed: {e}")
            return None
    
    def _analyze_with_openai(self, prompt: str) -> Optional[Dict]:
        """Analyze risk using OpenAI API."""
        try:
            import openai
            
            try:
                # Try new OpenAI client (v1+)
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un analista geopolítico experto. Responde solo en JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                ai_response = response.choices[0].message.content.strip()
            except ImportError:
                # Fallback to old OpenAI interface
                openai.api_key = self.openai_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un analista geopolítico experto. Responde solo en JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                ai_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            analysis = json.loads(ai_response)
            
            # Validate and normalize the response
            return self._validate_and_normalize_response(analysis, "openai")
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return None
    
    def _analyze_with_deepseek(self, prompt: str) -> Optional[Dict]:
        """Analyze risk using DeepSeek API."""
        try:
            import requests
            
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.deepseek_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Eres un analista geopolítico experto. Responde solo en JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            
            # Parse JSON response
            analysis = json.loads(ai_response)
            
            # Validate and normalize the response
            return self._validate_and_normalize_response(analysis, "deepseek")
            
        except Exception as e:
            logger.error(f"DeepSeek analysis failed: {e}")
            return None
    
    def _validate_and_normalize_response(self, analysis: Dict, model_name: str) -> Dict:
        """Validate and normalize AI response."""
        try:
            # Ensure required fields exist
            risk_level = analysis.get('risk_level', 'LOW').upper()
            if risk_level not in ['HIGH', 'MEDIUM', 'LOW']:
                risk_level = 'LOW'
            
            confidence = float(analysis.get('confidence', 0.5))
            confidence = max(0.0, min(1.0, confidence))
            
            severity_score = float(analysis.get('severity_score', 0.3))
            severity_score = max(0.0, min(1.0, severity_score))
            
            # Convert to our standard format
            return {
                'level': risk_level.lower(),
                'score': severity_score,
                'confidence': confidence,
                'reasoning': analysis.get('reasoning', 'AI analysis completed'),
                'key_factors': analysis.get('key_factors', []),
                'potential_escalation': analysis.get('potential_escalation', 'Unknown'),
                'geographic_impact': analysis.get('geographic_impact', 'Local'),
                'model_used': model_name,
                'ai_powered': True
            }
            
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            return {
                'level': 'low',
                'score': 0.3,
                'confidence': 0.5,
                'reasoning': f'AI analysis completed with {model_name} but validation failed',
                'key_factors': [],
                'potential_escalation': 'Unknown',
                'geographic_impact': 'Unknown',
                'model_used': model_name,
                'ai_powered': True
            }
    
    def _basic_keyword_analysis(self, title: str, content: str) -> Dict:
        """Basic keyword-based analysis as fallback when AI fails."""
        text = f"{title} {content}".lower()
        
        high_risk_keywords = [
            'war', 'guerra', 'attack', 'ataque', 'bombing', 'missile', 'nuclear',
            'terrorism', 'terrorist', 'coup', 'invasion', 'crisis', 'emergency',
            'hamas', 'israel', 'gaza', 'ukraine', 'russia', 'putin', 'zelensky',
            'iran', 'syria', 'north korea', 'china', 'taiwan', 'conflict',
            'military', 'bomb', 'explosion', 'threat', 'sanctions', 'embargo'
        ]
        
        medium_risk_keywords = [
            'tension', 'dispute', 'protest', 'demonstration', 'diplomatic',
            'negotiation', 'border', 'election', 'political', 'government',
            'minister', 'parliament', 'trade war', 'economic pressure'
        ]
        
        high_matches = sum(1 for keyword in high_risk_keywords if keyword in text)
        medium_matches = sum(1 for keyword in medium_risk_keywords if keyword in text)
        
        if high_matches >= 2:
            level = 'high'
            score = 0.8
        elif high_matches >= 1 or medium_matches >= 3:
            level = 'medium'
            score = 0.5
        else:
            level = 'low'
            score = 0.2
        
        return {
            'level': level,
            'score': score,
            'confidence': 0.6,
            'reasoning': f'Keyword-based analysis: {high_matches} high-risk, {medium_matches} medium-risk keywords found',
            'key_factors': [],
            'potential_escalation': 'Unknown',
            'geographic_impact': 'Unknown',
            'model_used': 'keyword_fallback',
            'ai_powered': False
        }

def main():
    """Test the AI risk analyzer."""
    analyzer = AIRiskAnalyzer()
    
    # Test cases
    test_articles = [
        {
            'title': 'Hamas envía propuesta de cese al fuego a Israel mientras la hambruna se extiende en Gaza',
            'content': 'Un oficial israelí dice que la última versión del grupo es factible mientras que las dos partes se preparan para nuevas negociaciones. La situación humanitaria en Gaza continúa deteriorándose.',
            'country': 'Israel'
        },
        {
            'title': 'Ucranianos protestan por segundo día por ley de lucha contra la corrupción',
            'content': 'Miles de ucranianos se reunieron por segundo día en Kiev y Lviv manifestando contra una nueva ley considerada insuficiente para combatir la corrupción.',
            'country': 'Ukraine'
        },
        {
            'title': 'Cumbre económica internacional busca fortalecer cooperación comercial',
            'content': 'Líderes de 20 países se reúnen para discutir nuevos acuerdos comerciales y fortalecer la cooperación económica internacional en un ambiente de diálogo constructivo.',
            'country': 'Global'
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

if __name__ == "__main__":
    main()