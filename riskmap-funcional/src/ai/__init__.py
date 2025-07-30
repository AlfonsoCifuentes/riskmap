"""
Módulo de Inteligencia Artificial para análisis geopolítico.
Soporta múltiples modelos: OpenAI, DeepSeek, Groq, HuggingFace y locales.
"""

from .multi_model_client import generate_ai_analysis, MultiModelAIClient

__all__ = ['generate_ai_analysis', 'MultiModelAIClient']
