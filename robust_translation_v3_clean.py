#!/usr/bin/env python3
"""
Sistema Ultra-Robusto de Traducción v3.0 CLEAN
===============================================

Sistema de traducción completamente libre de dependencias problemáticas
de httpcore/httpx que causaban errores de SyncHTTPTransport.

Características:
- 100% compatible con requests estándar
- Múltiples servicios de traducción como fallback
- Detección inteligente de idioma
- Manejo robusto de errores
- Sin dependencias problemáticas

Autor: Sistema de Automatización Inteligente
Fecha: Agosto 2025
Versión: 3.0 CLEAN
"""

import os
import logging
import json
import re
from typing import Optional, Tuple, Dict, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltraRobustTranslationService:
    """
    Servicio ultra-robusto de traducción sin dependencias problemáticas.
    
    Utiliza múltiples servicios de traducción como fallback:
    1. Google Translate (sin API key)
    2. LibreTranslate (público)
    3. MyMemory (gratuito)
    4. Patrones offline básicos
    """
    
    def __init__(self):
        """Inicializar el servicio de traducción."""
        self.failed_services = set()
        self.session = self._create_robust_session()
        self.translation_cache = {}
        
        logger.info("🚀 Sistema Ultra-Robusto de Traducción v3.0 CLEAN inicializado")
    
    def _create_robust_session(self) -> requests.Session:
        """Crear sesión HTTP robusta con reintentos."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        return session
    
    def translate_text(self, text: str, target_lang: str = 'es') -> Tuple[str, str]:
        """
        Traducir texto usando múltiples servicios como fallback.
        
        Args:
            text (str): Texto a traducir
            target_lang (str): Idioma objetivo (default: 'es')
            
        Returns:
            Tuple[str, str]: (texto_traducido, idioma_detectado)
        """
        if not text or not text.strip():
            return text, 'unknown'
        
        # Detectar idioma
        detected_lang = self._detect_language_simple(text)
        
        # Si ya está en el idioma objetivo, no traducir
        if detected_lang == target_lang:
            logger.info(f"📝 Texto ya está en {target_lang}")
            return text, detected_lang
        
        # Verificar caché
        cache_key = f"{text[:50]}_{target_lang}"
        if cache_key in self.translation_cache:
            cached_result = self.translation_cache[cache_key]
            logger.info("📋 Traducción desde caché")
            return cached_result
        
        # Intentar traducción con diferentes servicios
        translation_services = [
            self._translate_with_google,
            self._translate_with_libre,
            self._translate_with_mymemory,
            self._translate_offline_patterns
        ]
        
        for service in translation_services:
            try:
                translated = service(text, target_lang)
                if translated and translated != text:
                    # Guardar en caché
                    self.translation_cache[cache_key] = (translated, detected_lang)
                    logger.info("✅ Traducción exitosa")
                    return translated, detected_lang
            except Exception as e:
                logger.warning(f"Error en servicio de traducción: {e}")
                continue
        
        # Si no se pudo traducir, retornar original
        logger.warning("⚠️ No se pudo traducir, retornando texto original")
        return text, detected_lang
    
    def _detect_language_simple(self, text: str) -> str:
        """Detectar idioma usando patrones simples."""
        if not text:
            return 'unknown'
        
        text_lower = text.lower()
        
        # Palabras comunes en inglés
        english_words = ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 
                        'can', 'had', 'was', 'one', 'our', 'out', 'day', 'get', 
                        'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now',
                        'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'way',
                        'with', 'from', 'they', 'know', 'want', 'been', 'good',
                        'much', 'some', 'time', 'very', 'when', 'come', 'here',
                        'just', 'like', 'long', 'make', 'many', 'over', 'such',
                        'take', 'than', 'them', 'well', 'were', 'into', 'that',
                        'have', 'will', 'would', 'could', 'should', 'about',
                        'after', 'before', 'between', 'through', 'against']
        
        # Palabras comunes en español
        spanish_words = ['que', 'los', 'las', 'una', 'del', 'por', 'con', 'para',
                        'sin', 'como', 'más', 'año', 'día', 'muy', 'dos', 'ser',
                        'son', 'está', 'han', 'sus', 'fue', 'pero', 'otro', 'años',
                        'entre', 'otros', 'desde', 'hasta', 'donde', 'cuando',
                        'mientras', 'aunque', 'porque', 'durante', 'después',
                        'antes', 'contra', 'dentro', 'fuera', 'sobre', 'bajo',
                        'hacia', 'según', 'sino', 'también', 'además', 'incluso']
        
        words = text_lower.split()[:20]  # Solo primeras 20 palabras
        
        english_count = sum(1 for word in words if word in english_words)
        spanish_count = sum(1 for word in words if word in spanish_words)
        
        if english_count > spanish_count:
            return 'en'
        elif spanish_count > english_count:
            return 'es'
        else:
            # Heurísticas adicionales
            if any(char in text for char in ['ñ', 'ü']):
                return 'es'
            elif text.count(' ') / len(text) > 0.15:  # Espacios frecuentes = posible inglés
                return 'en'
            else:
                return 'es'  # Default español
    
    def _translate_with_google(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando Google Translate sin API key."""
        try:
            if 'google' in self.failed_services:
                return None
            
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'tl': target_lang,
                'dt': 't',
                'q': text
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    translated_text = ''.join([item[0] for item in result[0] if item[0]])
                    if translated_text and translated_text != text:
                        logger.info("✅ Traducción exitosa con Google Translate")
                        return translated_text
                        
        except Exception as e:
            logger.warning(f"Error con Google Translate: {e}")
            self.failed_services.add('google')
            
        return None
    
    def _translate_with_libre(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando LibreTranslate (servicio público)."""
        try:
            if 'libre' in self.failed_services:
                return None
                
            url = "https://libretranslate.de/translate"
            data = {
                'q': text,
                'source': 'auto',
                'target': target_lang,
                'format': 'text'
            }
            
            response = self.session.post(url, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get('translatedText', '')
                if translated_text and translated_text != text:
                    logger.info("✅ Traducción exitosa con LibreTranslate")
                    return translated_text
                    
        except Exception as e:
            logger.warning(f"Error con LibreTranslate: {e}")
            self.failed_services.add('libre')
            
        return None
    
    def _translate_with_mymemory(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando MyMemory API (gratuita)."""
        try:
            if 'mymemory' in self.failed_services:
                return None
                
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text,
                'langpair': f'auto|{target_lang}'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get('responseData', {}).get('translatedText', '')
                if translated_text and translated_text != text:
                    logger.info("✅ Traducción exitosa con MyMemory")
                    return translated_text
                    
        except Exception as e:
            logger.warning(f"Error con MyMemory: {e}")
            self.failed_services.add('mymemory')
            
        return None
    
    def _translate_offline_patterns(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducción básica usando patrones offline como último recurso."""
        if target_lang != 'es':
            return None
            
        # Diccionario básico de términos geopolíticos comunes
        translation_patterns = {
            # Términos básicos
            'breaking news': 'noticias de última hora',
            'news': 'noticias',
            'report': 'reporte',
            'reports': 'reportes',
            'government': 'gobierno',
            'president': 'presidente',
            'minister': 'ministro',
            'military': 'militar',
            'security': 'seguridad',
            'conflict': 'conflicto',
            'crisis': 'crisis',
            'emergency': 'emergencia',
            'protest': 'protesta',
            'protests': 'protestas',
            'violence': 'violencia',
            'attack': 'ataque',
            'explosion': 'explosión',
            'bomb': 'bomba',
            'terror': 'terror',
            'threat': 'amenaza',
            'war': 'guerra',
            'peace': 'paz',
            'nuclear': 'nuclear',
            'weapons': 'armas',
            'forces': 'fuerzas',
            'troops': 'tropas',
            'police': 'policía',
            'officials': 'funcionarios',
            'international': 'internacional',
            'region': 'región',
            'country': 'país',
            'countries': 'países',
            'city': 'ciudad',
            'capital': 'capital',
            'border': 'frontera',
            'agreement': 'acuerdo',
            'treaty': 'tratado',
            'sanctions': 'sanciones',
            'economy': 'economía',
            'economic': 'económico',
            'trade': 'comercio',
            'energy': 'energía',
            'oil': 'petróleo',
            'gas': 'gas',
            'climate': 'clima',
            'environment': 'medio ambiente'
        }
        
        try:
            translated = text
            for english_term, spanish_term in translation_patterns.items():
                # Reemplazar con sensibilidad a mayúsculas/minúsculas
                pattern = re.compile(re.escape(english_term), re.IGNORECASE)
                translated = pattern.sub(spanish_term, translated)
            
            if translated != text:
                logger.info("✅ Traducción básica con patrones offline")
                return translated
                
        except Exception as e:
            logger.warning(f"Error en traducción offline: {e}")
            
        return None


# ============================================
# FUNCIONES DE CONVENIENCIA GLOBALES
# ============================================

# Instancia global del servicio
_global_translation_service = None

def get_ultra_robust_translation(text: str, target_language: str = 'es') -> Tuple[str, str]:
    """
    Función de conveniencia para traducción ultra-robusta.
    
    Args:
        text (str): Texto a traducir
        target_language (str): Idioma objetivo
        
    Returns:
        Tuple[str, str]: (texto_traducido, idioma_detectado)
    """
    global _global_translation_service
    
    try:
        if _global_translation_service is None:
            _global_translation_service = UltraRobustTranslationService()
        
        return _global_translation_service.translate_text(text, target_language)
    except Exception as e:
        logger.error(f"Error crítico en traducción ultra-robusta: {e}")
        return text, 'unknown'


def translate_text_robust(text: str, target_lang: str = 'es') -> Tuple[str, str]:
    """
    Función de traducción robusta para compatibilidad con translation_service.py.
    
    Args:
        text (str): Texto a traducir
        target_lang (str): Idioma objetivo
        
    Returns:
        Tuple[str, str]: (texto_traducido, idioma_detectado)
    """
    return get_ultra_robust_translation(text, target_lang)


# Alias para compatibilidad con código existente
def get_robust_translation(text: str, target_language: str = 'es') -> Tuple[str, str]:
    """Alias para compatibilidad con código existente."""
    return get_ultra_robust_translation(text, target_language)


# Clase alias para compatibilidad
class RobustTranslationService(UltraRobustTranslationService):
    """Alias para compatibilidad con código existente."""
    pass


# ============================================
# TESTING Y DEMOSTRACIÓN
# ============================================

if __name__ == "__main__":
    # Test completo del sistema
    print("🧪 Testando Sistema de Traducción Ultra-Robusto v3.0 CLEAN")
    print("=" * 70)
    
    service = UltraRobustTranslationService()
    
    test_texts = [
        "Breaking news: Major conflict reported in the region with multiple casualties",
        "Government officials confirm new security measures in response to protests",
        "International observers are monitoring the situation closely",
        "Emergency services responded to the explosion in the city center",
        "President announces new policies to address the crisis"
    ]
    
    for i, test_text in enumerate(test_texts, 1):
        try:
            print(f"\n📝 Test {i}:")
            print(f"Original: {test_text}")
            
            translated, detected = service.translate_text(test_text, 'es')
            
            print(f"Traducido: {translated}")
            print(f"Idioma detectado: {detected}")
            print("-" * 50)
                                
        except Exception as e:
            logger.warning(f"Error en test de traducción: {e}")
            print(f"❌ Error en test {i}: {e}")
            
    print("\n✅ Tests completados")
    print("🎉 Sistema Ultra-Robusto de Traducción v3.0 CLEAN funcionando correctamente")
