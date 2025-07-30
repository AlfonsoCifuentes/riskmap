#!/usr/bin/env python3
"""
Translation Service for Geopolitical Intelligence System
"""

import requests
import json
import logging
from typing import Optional
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config

logger = logging.getLogger(__name__)

class TranslationService:
    """Translation service using LibreTranslate and fallback providers."""
    
    def __init__(self):
        # LibreTranslate configuration
        self.libretranslate_url = config.get('translation.libretranslate_url', 'https://libretranslate.de/translate')
        self.libretranslate_api_key = config.get('translation.libretranslate_api_key', None)
        
        # Fallback providers
        self.groq_key = config.get_groq_key()
        self.openai_key = config.get_openai_key()
        self.deepseek_key = config.get_deepseek_key()
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text from source language to target language."""
        
        # If same language, return original
        if source_lang == target_lang:
            return text
        
        # If text is too short, return original
        if len(text.strip()) < 10:
            return text
        
        try:
            # Try LibreTranslate first (free and open source)
            result = self._translate_libretranslate(text, source_lang, target_lang)
            if result:
                return result
            
            # Try local LibreTranslate instance
            result = self._translate_libretranslate_local(text, source_lang, target_lang)
            if result:
                return result
            
            # Try Groq as fallback
            if self.groq_key:
                result = self._translate_groq(text, source_lang, target_lang)
                if result:
                    return result
            
            # Try OpenAI as fallback
            if self.openai_key:
                result = self._translate_openai(text, source_lang, target_lang)
                if result:
                    return result
            
            # Try DeepSeek as fallback
            if self.deepseek_key:
                result = self._translate_deepseek(text, source_lang, target_lang)
                if result:
                    return result
            
            # Final fallback to simple dictionary translation
            return self._simple_translate(text, source_lang, target_lang)
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
    
    def _translate_libretranslate(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate using LibreTranslate API."""
        try:
            # Prepare the request data
            data = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            # Add API key if available
            if self.libretranslate_api_key:
                data['api_key'] = self.libretranslate_api_key
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Make the request with better error handling
            response = requests.post(
                self.libretranslate_url,
                headers=headers,
                json=data,
                timeout=15  # Reduced timeout
            )
            
            # Check if response is empty or invalid
            if not response.content:
                logger.warning(f"LibreTranslate: Empty response from {self.libretranslate_url}")
                return None
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                logger.warning(f"LibreTranslate: Invalid content type: {content_type}")
                return None
            
            response.raise_for_status()
            
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.warning(f"LibreTranslate: JSON decode error: {e}")
                return None
            
            # Extract translation
            if 'translatedText' in result:
                translation = result['translatedText'].strip()
                if translation and translation != text:  # Ensure we got a real translation
                    logger.info(f"LibreTranslate: {source_lang}->{target_lang} successful")
                    return translation
                else:
                    logger.warning(f"LibreTranslate: Empty or unchanged translation")
                    return None
            else:
                logger.warning(f"LibreTranslate: No translation in response: {result}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"LibreTranslate: Request timeout for {self.libretranslate_url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"LibreTranslate: Connection error to {self.libretranslate_url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"LibreTranslate request error: {e}")
            return None
        except Exception as e:
            logger.warning(f"LibreTranslate error: {e}")
            return None
    
    def _translate_libretranslate_local(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate using local LibreTranslate instance."""
        try:
            # Try common local LibreTranslate URLs
            local_urls = [
                'http://localhost:5000/translate',
                'http://127.0.0.1:5000/translate',
                'http://localhost:8080/translate'
            ]
            
            for url in local_urls:
                try:
                    data = {
                        'q': text,
                        'source': source_lang,
                        'target': target_lang,
                        'format': 'text'
                    }
                    
                    response = requests.post(
                        url,
                        json=data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'translatedText' in result:
                            logger.info(f"Local LibreTranslate: {source_lang}->{target_lang} successful")
                            return result['translatedText'].strip()
                            
                except requests.exceptions.RequestException:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Local LibreTranslate error: {e}")
            return None
    
    def _translate_groq(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate using Groq API."""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json"
            }
            
            lang_names = {
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ar': 'Arabic',
                'zh': 'Chinese',
                'ja': 'Japanese',
                'ko': 'Korean'
            }
            
            source_name = lang_names.get(source_lang, source_lang)
            target_name = lang_names.get(target_lang, target_lang)
            
            prompt = f"Translate the following text from {source_name} to {target_name}. Return only the translation, no explanations:\\n\\n{text}"
            
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a professional translator. Translate accurately and maintain the original meaning."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            translation = result['choices'][0]['message']['content'].strip()
            
            # Clean up common translation artifacts
            translation = translation.replace('"', '').strip()
            
            return translation
            
        except Exception as e:
            logger.error(f"Groq translation error: {e}")
            return None
    
    def _translate_openai(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate using OpenAI API."""
        try:
            import openai
            
            lang_names = {
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ar': 'Arabic',
                'zh': 'Chinese',
                'ja': 'Japanese',
                'ko': 'Korean'
            }
            
            source_name = lang_names.get(source_lang, source_lang)
            target_name = lang_names.get(target_lang, target_lang)
            
            prompt = f"Translate from {source_name} to {target_name}:\\n\\n{text}"
            
            try:
                # Try new OpenAI client
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional translator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                
                return response.choices[0].message.content.strip()
                
            except ImportError:
                # Fallback to old interface
                openai.api_key = self.openai_key
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional translator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            logger.error(f"OpenAI translation error: {e}")
            return None
    
    def _translate_deepseek(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate using DeepSeek API."""
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.deepseek_key}",
                "Content-Type": "application/json"
            }
            
            lang_names = {
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ar': 'Arabic',
                'zh': 'Chinese',
                'ja': 'Japanese',
                'ko': 'Korean'
            }
            
            source_name = lang_names.get(source_lang, source_lang)
            target_name = lang_names.get(target_lang, target_lang)
            
            prompt = f"Translate from {source_name} to {target_name}:\\n\\n{text}"
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"DeepSeek translation error: {e}")
            return None
    
    def _simple_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Simple fallback translation for common geopolitical terms."""
        
        # Basic translation dictionaries
        translations = {
            ('en', 'es'): {
                'government': 'gobierno',
                'politics': 'política',
                'military': 'militar',
                'security': 'seguridad',
                'economy': 'economía',
                'climate': 'clima',
                'energy': 'energía',
                'war': 'guerra',
                'peace': 'paz',
                'crisis': 'crisis',
                'conflict': 'conflicto',
                'international': 'internacional',
                'president': 'presidente',
                'minister': 'ministro',
                'parliament': 'parlamento',
                'election': 'elección',
                'democracy': 'democracia',
                'sanctions': 'sanciones',
                'trade': 'comercio',
                'oil': 'petróleo',
                'gas': 'gas'
            }
        }
        
        # Get translation dictionary
        trans_dict = translations.get((source_lang, target_lang), {})
        
        # Apply simple word replacements
        result = text
        for source_word, target_word in trans_dict.items():
            result = result.replace(source_word, target_word)
        
        return result

def main():
    """Test translation service."""
    translator = TranslationService()
    
    # Test translation
    text = "The government announced new security measures"
    result = translator.translate(text, 'en', 'es')
    print(f"Original: {text}")
    print(f"Translated: {result}")

if __name__ == "__main__":
    main()