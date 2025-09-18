#!/usr/bin/env python3
"""
Sistema de Traducción Gratuito v4.0
- LibreTranslate (instancia pública gratuita) como principal
- Groq (Llama-3.1) como fallback gratuito
- Sin dependencias problemáticas
"""

import logging
import requests
import json
import time
import os
from typing import Optional, Tuple
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)

class FreeTranslationService:
    """Servicio de traducción completamente gratuito"""
    
    def __init__(self):
        """Inicializar servicios gratuitos"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Instancias públicas de LibreTranslate (gratuitas) - URLs funcionales verificadas
        self.libretranslate_urls = [
            "https://libretranslate.com",
            "https://translate.terraprint.co" 
        ]
        
        # Configurar Groq como fallback principal
        self.groq_client = None
        if GROQ_AVAILABLE:
            try:
                from groq import Groq as GroqClient
                groq_api_key = os.getenv('GROQ_API_KEY')
                if groq_api_key:
                    self.groq_client = GroqClient(api_key=groq_api_key)
                    logger.info("✅ Groq configurado como fallback principal")
                else:
                    logger.warning("⚠️ GROQ_API_KEY no encontrada")
            except Exception as e:
                logger.error(f"❌ Error configurando Groq: {e}")
        else:
            logger.warning("⚠️ Groq no disponible - instalar con: pip install groq")
            
        # Configurar OpenAI como fallback secundario
        self.openai_client = None
        try:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                import openai
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                logger.info("✅ OpenAI configurado como fallback secundario")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI no disponible: {e}")
            
        self.translation_cache = {}
        self.failed_urls = set()
        
        logger.info("✅ Sistema de traducción gratuito v4.0 inicializado")
    
    def _detect_language(self, text: str) -> str:
        """Detectar idioma del texto"""
        if not text or len(text.strip()) < 3:
            return 'en'
        
        text_lower = text.lower()
        
        # Palabras comunes en español
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'una', 'está', 'han', 'muy', 'más', 'como', 'pero', 'del', 'las', 'los', 'al']
        english_words = ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'this', 'that', 'with', 'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were']
        
        spanish_count = sum(1 for word in spanish_words if f' {word} ' in f' {text_lower} ' or text_lower.startswith(f'{word} ') or text_lower.endswith(f' {word}'))
        english_count = sum(1 for word in english_words if f' {word} ' in f' {text_lower} ' or text_lower.startswith(f'{word} ') or text_lower.endswith(f' {word}'))
        
        # Si ya hay muchas palabras en español, no traducir
        words = text_lower.split()
        if len(words) > 0:
            spanish_ratio = spanish_count / len(words)
            if spanish_ratio > 0.15:  # Si más del 15% son palabras españolas comunes
                return 'es'
        
        # Detectar patrones en español
        spanish_patterns = ['ñ', 'ción', 'sión', 'idad', 'mente', 'ación', 'ería', 'ería']
        for pattern in spanish_patterns:
            if pattern in text_lower:
                return 'es'
                
        return 'en' if english_count > spanish_count else 'auto'
    
    def _translate_with_libretranslate(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando LibreTranslate (instancia pública gratuita)"""
        for url in self.libretranslate_urls:
            if url in self.failed_urls:
                continue
                
            try:
                endpoint = f"{url}/translate"
                
                payload = {
                    "q": text,
                    "source": "auto",
                    "target": target_lang,
                    "format": "text"
                }
                
                response = self.session.post(
                    endpoint, 
                    json=payload, 
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    translated_text = result.get('translatedText', '').strip()
                    
                    if translated_text and translated_text != text:
                        logger.info(f"✅ Traducción exitosa con LibreTranslate ({url})")
                        return translated_text
                        
            except Exception as e:
                logger.warning(f"⚠️ Error con LibreTranslate {url}: {e}")
                self.failed_urls.add(url)
                continue
                
        return None
    
    def _translate_with_openai(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando OpenAI como fallback secundario"""
        if not self.openai_client:
            return None
            
        try:
            # Prompt especializado para títulos de noticias geopolíticas
            prompt = f"""Translate this English news headline to Spanish. Keep proper nouns (NATO, Pentagon, Denmark, etc.) in their commonly used Spanish form. Provide ONLY the translation, no explanations or notes.

English: "{text}"
Spanish:"""

            response = self.openai_client.chat.completions.create(
                messages=[{
                    "role": "user", 
                    "content": prompt
                }],
                model="gpt-4o-mini",  # Modelo más económico
                max_tokens=150,
                temperature=0.1  # Baja temperatura para traducción consistente
            )
            
            translated_text = response.choices[0].message.content
            if translated_text:
                translated_text = translated_text.strip()
            
                # Limpiar posibles prefijos
                if translated_text.lower().startswith('spanish translation:'):
                    translated_text = translated_text[len('spanish translation:'):].strip()
                if translated_text.startswith('"') and translated_text.endswith('"'):
                    translated_text = translated_text[1:-1]
                    
                if translated_text and translated_text != text:
                    logger.info("✅ Traducción exitosa con OpenAI (GPT-4o-mini)")
                    return translated_text
                
        except Exception as e:
            logger.error(f"❌ Error con OpenAI: {e}")
            
        return None
    
    def _translate_with_groq(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando Groq (Llama-3.1) como fallback gratuito"""
        if not self.groq_client:
            return None
            
        try:
            # Prompt especializado para títulos de noticias geopolíticas
            prompt = f"""Translate this English news headline to Spanish. Keep proper nouns (NATO, Pentagon, Denmark, etc.) in their commonly used Spanish form. Provide ONLY the translation, no explanations or notes.

English: "{text}"
Spanish:"""

            response = self.groq_client.chat.completions.create(
                messages=[{
                    "role": "user", 
                    "content": prompt
                }],
                model="llama-3.1-8b-instant",  # Modelo gratuito actualizado
                max_tokens=150,
                temperature=0.1  # Baja temperatura para traducción consistente
            )
            
            translated_text = response.choices[0].message.content
            if translated_text:
                translated_text = translated_text.strip()
            
                # Limpiar posibles prefijos y notas extra
                if translated_text.lower().startswith('spanish translation:'):
                    translated_text = translated_text[len('spanish translation:'):].strip()
                if translated_text.startswith('"') and translated_text.endswith('"'):
                    translated_text = translated_text[1:-1]
                
                # Eliminar notas explicativas que empiecen con (Note: o paréntesis
                lines = translated_text.split('\n')
                translated_text = lines[0].strip()  # Solo tomar la primera línea
                
                # Limpiar comillas si están presentes
                if translated_text.startswith('"') and translated_text.endswith('"'):
                    translated_text = translated_text[1:-1]
                    
                if translated_text and translated_text != text:
                    logger.info("✅ Traducción exitosa con Groq (Llama-3.1)")
                    return translated_text
                
        except Exception as e:
            logger.error(f"❌ Error con Groq: {e}")
            
        return None
            
        return None
    
    def translate_text(self, text: str, target_language: str = 'es') -> Tuple[str, str]:
        """
        Traducir texto usando LibreTranslate + Groq fallback
        
        Returns:
            Tuple[str, str]: (texto_traducido, idioma_detectado)
        """
        if not text or not text.strip():
            return text, 'unknown'
        
        text = text.strip()
        
        # Cache check
        cache_key = f"{text}_{target_language}"
        if cache_key in self.translation_cache:
            cached_result = self.translation_cache[cache_key]
            return cached_result, 'cached'
        
        # Detectar idioma
        detected_lang = self._detect_language(text)
        
        # Si ya está en español, no traducir
        if detected_lang == 'es' or detected_lang == target_language:
            self.translation_cache[cache_key] = text
            return text, detected_lang
        
        # Intentar LibreTranslate primero (gratuito)
        logger.info("🔄 Intentando traducción con LibreTranslate...")
        translated_text = self._translate_with_libretranslate(text, target_language)
        
        # Si LibreTranslate falla, usar Groq
        if not translated_text:
            logger.info("🔄 LibreTranslate falló, usando Groq como fallback...")
            translated_text = self._translate_with_groq(text, target_language)
        
        # Si Groq falla, usar OpenAI
        if not translated_text:
            logger.info("🔄 Groq falló, usando OpenAI como último fallback...")
            translated_text = self._translate_with_openai(text, target_language)
        
        # Si ambos fallan, devolver texto original
        if not translated_text:
            logger.warning(f"⚠️ No se pudo traducir: {text[:50]}...")
            translated_text = text
        
        # Guardar en cache
        self.translation_cache[cache_key] = translated_text
        
        return translated_text, detected_lang
    
    def is_available(self) -> bool:
        """Verificar si el servicio está disponible"""
        return (len(self.failed_urls) < len(self.libretranslate_urls) or 
                self.groq_client is not None or 
                self.openai_client is not None)

# Instancia global
translator = None

def initialize_translation_system():
    """Inicializar sistema de traducción gratuito"""
    global translator
    try:
        translator = FreeTranslationService()
        logger.info("✅ Sistema de traducción gratuito inicializado")
        return translator
    except Exception as e:
        logger.error(f"❌ Error inicializando traducción: {e}")
        return None

if __name__ == "__main__":
    # Test del sistema
    translator = initialize_translation_system()
    
    if translator is None:
        print("❌ Error: No se pudo inicializar el sistema de traducción")
        exit(1)
    
    test_titles = [
        "Denmark picks French-Italian SAMP/T air defense system over Patriot",
        "Pentagon stages first 'Top Drone' school for operators",
        "NATO shot down 3 Russia drones in Poland"
    ]
    
    for title in test_titles:
        translated, lang = translator.translate_text(title)
        print(f"Original: {title}")
        print(f"Traducido: {translated}")
        print(f"Idioma: {lang}")
        print("-" * 50)