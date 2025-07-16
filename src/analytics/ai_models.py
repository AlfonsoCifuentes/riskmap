"""
AI Models Integration for Geopolitical Analysis
Handles multiple AI providers with fallback mechanisms
"""

import logging
import os
from typing import Optional, Dict, Any
import json

class AIModels:
    """Unified AI models interface with multiple providers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.available_models = []
        self.priority_order = ['groq', 'deepseek', 'openai', 'huggingface', 'local']
        
        # Initialize available models
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize and test available AI models."""
        
        # Test Groq
        try:
            import groq
            self.available_models.append('groq')
            self.logger.info("Groq model available")
        except ImportError:
            self.logger.warning("Groq not available")
            
        # Test OpenAI
        try:
            import openai
            self.available_models.append('openai')
            self.logger.info("OpenAI model available")
        except ImportError:
            self.logger.warning("OpenAI not available")
            
        # Test DeepSeek (through OpenAI API)
        if 'openai' in self.available_models:
            self.available_models.append('deepseek')
            self.logger.info("DeepSeek model available")
            
        # Test HuggingFace
        try:
            import transformers
            self.available_models.append('huggingface')
            self.logger.info("HuggingFace model available")
        except ImportError:
            self.logger.warning("HuggingFace not available")
            
        # Local fallback always available
        self.available_models.append('local')
        self.logger.info("Local model available")
        
        self.logger.info(f"Available models: {self.available_models}")
        
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate response using the best available AI model.
        """
        
        for model_name in self.priority_order:
            if model_name in self.available_models:
                try:
                    self.logger.info(f"Attempting to use {model_name} for AI analysis")
                    
                    if model_name == 'groq':
                        return self._generate_groq(prompt, max_tokens)
                    elif model_name == 'deepseek':
                        return self._generate_deepseek(prompt, max_tokens)
                    elif model_name == 'openai':
                        return self._generate_openai(prompt, max_tokens)
                    elif model_name == 'huggingface':
                        return self._generate_huggingface(prompt, max_tokens)
                    elif model_name == 'local':
                        return self._generate_local(prompt, max_tokens)
                        
                except Exception as e:
                    self.logger.error(f"{model_name.capitalize()} error: {str(e)}")
                    continue
                    
        # If all models fail, return a basic response
        return self._generate_fallback_response(prompt)
    
    def _generate_groq(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Groq."""
        try:
            import groq
            
            client = groq.Groq(
                api_key=os.getenv('GROQ_API_KEY', 'gsk_placeholder')
            )
            
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
    
    def _generate_deepseek(self, prompt: str, max_tokens: int) -> str:
        """Generate response using DeepSeek."""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=os.getenv('DEEPSEEK_API_KEY', 'sk-placeholder'),
                base_url="https://api.deepseek.com/v1"
            )
            
            completion = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"DeepSeek API error: {str(e)}")
    
    def _generate_openai(self, prompt: str, max_tokens: int) -> str:
        """Generate response using OpenAI."""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=os.getenv('OPENAI_API_KEY', 'sk-placeholder')
            )
            
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _generate_huggingface(self, prompt: str, max_tokens: int) -> str:
        """Generate response using HuggingFace."""
        try:
            import requests
            
            # Use HuggingFace Inference API
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY', 'hf_placeholder')}"}
            
            models_to_try = [
                "microsoft/DialoGPT-large",
                "microsoft/DialoGPT-medium", 
                "facebook/blenderbot-400M-distill",
                "gpt2"
            ]
            
            for model in models_to_try:
                try:
                    response = requests.post(
                        f"https://api-inference.huggingface.co/models/{model}",
                        headers=headers,
                        json={"inputs": prompt[:500]},  # Limit input length
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if isinstance(result, list) and len(result) > 0:
                            return result[0].get('generated_text', '').strip()
                    else:
                        self.logger.warning(f"HuggingFace model {model} returned: {response.status_code}")
                        continue
                        
                except Exception as e:
                    self.logger.warning(f"HuggingFace model {model} failed: {str(e)}")
                    continue
                    
            raise Exception("All HuggingFace models failed")
            
        except Exception as e:
            raise Exception(f"HuggingFace error: {str(e)}")
    
    def _generate_local(self, prompt: str, max_tokens: int) -> str:
        """Generate response using local/rule-based logic."""
        self.logger.info("Using local model generation")
        
        # Basic keyword-based analysis for geopolitical content
        keywords_analysis = {
            'conflict': ['war', 'conflict', 'battle', 'military', 'invasion', 'attack'],
            'diplomacy': ['negotiation', 'treaty', 'agreement', 'summit', 'diplomatic'],
            'economy': ['trade', 'tariff', 'economic', 'sanctions', 'market', 'gdp'],
            'politics': ['election', 'government', 'president', 'minister', 'parliament'],
            'crisis': ['crisis', 'emergency', 'urgent', 'critical', 'disaster']
        }
        
        prompt_lower = prompt.lower()
        detected_themes = []
        
        for theme, words in keywords_analysis.items():
            if any(word in prompt_lower for word in words):
                detected_themes.append(theme)
        
        # Generate analysis based on detected themes
        if 'conflict' in detected_themes:
            analysis = """Based on the geopolitical situation described, this appears to involve military or security-related tensions. Key factors to monitor include:
            - Regional stability implications
            - International response and interventions
            - Civilian impact and humanitarian concerns
            - Economic consequences for affected regions"""
            
        elif 'diplomacy' in detected_themes:
            analysis = """This situation involves diplomatic negotiations and international relations. Important aspects include:
            - Multilateral cooperation opportunities
            - Bilateral relationship dynamics
            - International law and treaty implications
            - Long-term regional stability effects"""
            
        elif 'economy' in detected_themes:
            analysis = """The economic dimensions of this geopolitical development suggest:
            - Trade relationship impacts
            - Market volatility considerations
            - Supply chain disruption potential
            - International financial system effects"""
            
        elif 'crisis' in detected_themes:
            analysis = """This represents a significant geopolitical crisis requiring immediate attention:
            - Emergency response coordination
            - International humanitarian assistance
            - Regional security implications
            - Long-term reconstruction needs"""
            
        else:
            analysis = """This geopolitical development requires careful monitoring and analysis:
            - Regional stability assessment
            - International stakeholder involvement
            - Medium and long-term implications
            - Potential escalation scenarios"""
        
        return analysis
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate a basic fallback response when all models fail."""
        return """Análisis geopolítico: La situación descrita requiere monitoreo continuo y evaluación de múltiples factores incluyendo estabilidad regional, respuesta internacional, y implicaciones a largo plazo para la seguridad global."""
