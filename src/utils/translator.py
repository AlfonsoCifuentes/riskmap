"""
Sistema de traducción automática multiidioma
Utiliza múltiples servicios de traducción con fallback
"""

import logging
import requests
from typing import Dict, Any, Optional, List
import time
import json
from deep_translator import GoogleTranslator
import os

logger = logging.getLogger(__name__)

# Definición de idiomas soportados
SUPPORTED_LANGUAGES = {
    'es': 'Spanish',
    'en': 'English', 
    'de': 'German',
    'fr': 'French',
    'it': 'Italian',
    'ru': 'Russian',
    'zh': 'Chinese',
    'ja': 'Japanese'
}

class MultilingualTranslator:
    """Traductor multilingüe con múltiples backends"""
    
    def __init__(self):
        self.cache = {}
        self.cache_file = "data/translation_cache.json"
        self.load_cache()
    
    def load_cache(self):
        """Carga caché de traducciones"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            else:
                os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
                self.cache = {}
        except Exception as e:
            logger.warning(f"No se pudo cargar el caché de traducciones: {e}")
            self.cache = {}
    
    def save_cache(self):
        """Guarda caché de traducciones"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"No se pudo guardar el caché de traducciones: {e}")
    
    def get_cache_key(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """Genera clave para caché"""
        return f"{source_lang}:{target_lang}:{hash(text)}"
    
    def translate_with_google(self, text: str, target_lang: str, source_lang: str = 'auto') -> Optional[str]:
        """Traduce usando Google Translate"""
        try:
            cache_key = self.get_cache_key(text, target_lang, source_lang)
            
            # Verificar caché
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Traducir usando deep-translator
            try:
                from deep_translator import GoogleTranslator
                if source_lang == 'auto':
                    translator = GoogleTranslator(target=target_lang)
                else:
                    translator = GoogleTranslator(source=source_lang, target=target_lang)
                
                translated_text = translator.translate(text)
                
                # Guardar en caché
                self.cache[cache_key] = translated_text
                self.save_cache()
                
                return translated_text
            except Exception as e:
                logger.error(f"Error importing or using deep_translator: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error con Google Translate: {e}")
            return None
    
    def translate_with_local(self, text: str, target_lang: str, source_lang: str = 'auto') -> Optional[str]:
        """Traduce usando modelo local (fallback)"""
        try:
            # Importar aquí para evitar errores si no está disponible
            from transformers import MarianMTModel, MarianTokenizer
            
            # Mapeo de códigos de idioma para Marian
            lang_map = {
                'es': 'es', 'en': 'en', 'de': 'de', 'fr': 'fr',
                'it': 'it', 'ru': 'ru', 'zh': 'zh', 'ja': 'jap'
            }
            
            if target_lang not in lang_map:
                return None
            
            # Para simplificar, usamos un modelo específico
            model_name = f"Helsinki-NLP/opus-mt-en-{lang_map[target_lang]}"
            
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            
            # Tokenizar y traducir
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            translated = model.generate(**inputs)
            translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Error con traducción local: {e}")
            return None
    
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """
        Traduce texto al idioma objetivo usando múltiples backends
        """
        if not text or not text.strip():
            return text
        
        # Si el idioma objetivo es el mismo que el de origen, no traducir
        if source_lang == target_lang:
            return text
        
        # Intentar con Google Translate primero
        result = self.translate_with_google(text, target_lang, source_lang)
        if result:
            return result
        
        # Fallback a traducción local
        result = self.translate_with_local(text, target_lang, source_lang)
        if result:
            return result
        
        # Si todo falla, devolver texto original
        logger.warning(f"No se pudo traducir el texto al idioma {target_lang}")
        return text
    
    def translate_dict(self, data: Dict[str, Any], target_lang: str, 
                      translate_keys: List[str] = None) -> Dict[str, Any]:
        """
        Traduce campos específicos de un diccionario
        """
        if not translate_keys:
            translate_keys = ['title', 'description', 'content', 'summary', 'text']
        
        translated_data = data.copy()
        
        for key in translate_keys:
            if key in translated_data and isinstance(translated_data[key], str):
                translated_data[key] = self.translate(translated_data[key], target_lang)
        
        return translated_data
    
    def translate_articles_list(self, articles: List[Dict[str, Any]], target_lang: str) -> List[Dict[str, Any]]:
        """
        Traduce una lista de artículos
        """
        translated_articles = []
        
        for article in articles:
            translated_article = self.translate_dict(
                article, 
                target_lang, 
                ['title', 'description', 'content', 'summary']
            )
            translated_articles.append(translated_article)
        
        return translated_articles

    def get_ui_translations(self, target_lang: str) -> Dict[str, str]:
        """
        Obtiene traducciones para elementos de la interfaz
        """
        ui_texts = {
            'dashboard': 'Dashboard',
            'reports': 'Reports', 
            'ai_chat': 'AI Chat',
            'about': 'About',
            'recent_articles': 'Recent Articles',
            'high_risk_articles': 'High Risk Articles',
            'language_distribution': 'Language Distribution',
            'ai_geopolitical_analysis': 'AI Geopolitical Analysis',
            'key_insights': 'Key Insights',
            'recommendations': 'Recommendations',
            'title': 'Title',
            'description': 'Description',
            'published': 'Published',
            'source': 'Source',
            'language': 'Language',
            'risk_level': 'Risk Level',
            'sentiment': 'Sentiment',
            'loading': 'Loading...',
            'error': 'Error',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
            'positive': 'Positive',
            'negative': 'Negative',
            'neutral': 'Neutral',
            'articles': 'Articles',
            'total_articles': 'Total Articles',
            'sources': 'Sources',
            'risk_index': 'Risk Index',
            'select_language': 'Select Language',
            'geopolitical_intelligence_system': 'Geopolitical Intelligence System',
            'osint_intelligence': 'OSINT Intelligence',
            'built_with_ai': 'Built with advanced AI and NLP technologies',
            'copyright': '© 2025 Geopolitical Intelligence System'
        }
        
        if target_lang == 'en':
            return ui_texts
        
        translated_ui = {}
        for key, text in ui_texts.items():
            translated_ui[key] = self.translate(text, target_lang, 'en')
        
        return translated_ui

# Instancia global del traductor
translator = MultilingualTranslator()

def get_translator() -> MultilingualTranslator:
    """Obtiene la instancia del traductor"""
    return translator
