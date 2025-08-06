#!/usr/bin/env python3
"""
Sistema de Traducción Robusto con Fallbacks

Este módulo implementa traducción con múltiples fallbacks para evitar
errores de compatibilidad con httpcore/httpx.
"""

import logging
import requests
import json
import urllib.parse
import urllib.request
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class RobustTranslationService:
    """Servicio de traducción robusto con múltiples fallbacks"""
    
    def __init__(self):
        self.failed_services = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def _translate_with_urllib(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando urllib (sin dependencias HTTP externas)"""
        try:
            if 'urllib' in self.failed_services:
                return None
                
            # Usar MyMemory API con urllib para evitar conflictos HTTP
            base_url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text[:500],  # Límite de caracteres
                'langpair': f'auto|{target_lang}'
            }
            
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if data.get('responseStatus') == 200:
                        translated_text = data.get('responseData', {}).get('translatedText', '')
                        if translated_text and translated_text != text:
                            logger.info("✅ Traducción exitosa con urllib/MyMemory")
                            return translated_text
                            
        except Exception as e:
            logger.warning(f"Error con urllib: {e}")
            self.failed_services.add('urllib')
            
        return None
        
    def _translate_with_libre(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando LibreTranslate (servicio público)"""
        try:
            if 'libre' in self.failed_services:
                return None
                
            # Usar instancia pública de LibreTranslate
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
        """Traducir usando MyMemory API (gratuita) con requests"""
        try:
            if 'mymemory' in self.failed_services:
                return None
                
            # MyMemory API gratuita
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text[:500],  # Límite de caracteres
                'langpair': f'auto|{target_lang}'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('responseStatus') == 200:
                    translated_text = result.get('responseData', {}).get('translatedText', '')
                    if translated_text and translated_text != text:
                        logger.info("✅ Traducción exitosa con MyMemory")
                        return translated_text
                        
        except Exception as e:
            logger.warning(f"Error con MyMemory: {e}")
            self.failed_services.add('mymemory')
            
        return None
    
    def _translate_offline_patterns(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducción básica offline usando patrones comunes"""
        try:
            if target_lang != 'es':
                return None
                
            # Diccionario básico de traducciones comunes
            translations = {
                # Términos de noticias comunes
                'breaking news': 'noticias de última hora',
                'update': 'actualización', 
                'urgent': 'urgente',
                'crisis': 'crisis',
                'conflict': 'conflicto',
                'war': 'guerra',
                'peace': 'paz',
                'security': 'seguridad',
                'government': 'gobierno',
                'military': 'militar',
                'police': 'policía',
                'protest': 'protesta',
                'demonstration': 'manifestación',
                'violence': 'violencia',
                'attack': 'ataque',
                'bombing': 'bombardeo',
                'explosion': 'explosión',
                'casualties': 'víctimas',
                'injured': 'heridos',
                'dead': 'muertos',
                'rescue': 'rescate',
                'emergency': 'emergencia',
                'alert': 'alerta',
                'warning': 'advertencia',
                'threat': 'amenaza',
                'terror': 'terror',
                'terrorism': 'terrorismo',
                'investigation': 'investigación',
                'report': 'informe',
                'statement': 'declaración',
                'conference': 'conferencia',
                'meeting': 'reunión',
                'agreement': 'acuerdo',
                'treaty': 'tratado',
                'negotiations': 'negociaciones',
                'diplomatic': 'diplomático',
                'international': 'internacional',
                'national': 'nacional',
                'regional': 'regional',
                'local': 'local',
                'global': 'global',
                'worldwide': 'mundial',
                'economic': 'económico',
                'financial': 'financiero',
                'political': 'político',
                'social': 'social'
            }
            
            # Reemplazar palabras clave
            text_lower = text.lower()
            translated_parts = []
            words = text.split()
            
            for word in words:
                word_clean = word.lower().strip('.,!?;:')
                if word_clean in translations:
                    translated_parts.append(translations[word_clean])
                else:
                    translated_parts.append(word)
            
            result = ' '.join(translated_parts)
            
            # Solo devolver si hubo al menos una traducción
            if result != text:
                logger.info("✅ Traducción parcial offline aplicada")
                return result
                
        except Exception as e:
            logger.warning(f"Error en traducción offline: {e}")
            
        return None
    
    def _simple_language_detection(self, text: str) -> str:
        """Detección simple de idioma basada en patrones"""
        # Patrones comunes en diferentes idiomas
        spanish_indicators = ['el', 'la', 'los', 'las', 'de', 'en', 'un', 'una', 'que', 'con', 'por', 'para', 'del', 'al', 'se', 'no', 'es', 'son', 'fue', 'han', 'será', 'desde', 'hasta', 'pero', 'como', 'muy', 'más', 'todo', 'cada']
        english_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should']
        
        words = text.lower().split()[:20]  # Primeras 20 palabras
        
        spanish_count = sum(1 for word in words if word in spanish_indicators)
        english_count = sum(1 for word in words if word in english_indicators)
        
        if spanish_count >= len(words) * 0.2:
            return 'es'
        elif english_count >= len(words) * 0.2:
            return 'en'
        else:
            return 'unknown'
    
    def translate_text_robust(self, text: str, target_lang: str = 'es') -> Tuple[str, str]:
        """
        Traducir texto usando servicios robustos
        
        Args:
            text: Texto a traducir
            target_lang: Idioma de destino
            
        Returns:
            Tupla (texto_traducido, idioma_detectado)
        """
        if not text or len(text.strip()) < 3:
            return text, 'unknown'
            
        # Detectar idioma
        detected_lang = self._simple_language_detection(text)
        
        # Si ya está en español, no traducir
        if detected_lang == target_lang:
            return text, detected_lang
            
        # Intentar traducir con diferentes servicios (en orden de preferencia)
        translation_services = [
            self._translate_with_urllib,      # Más confiable, sin dependencias HTTP complejas
            self._translate_with_libre,       # Servicio gratuito robusto
            self._translate_with_mymemory,    # API gratuita con requests
            self._translate_offline_patterns  # Fallback offline
        ]
        
        for service in translation_services:
            try:
                translated_text = service(text, target_lang)
                if translated_text:
                    return translated_text, detected_lang
            except Exception as e:
                logger.warning(f"Error en servicio de traducción: {e}")
                continue
        
        # Si todos fallan, devolver texto original
        logger.warning(f"No se pudo traducir: {text[:100]}...")
        return text, detected_lang

# Instancia global
robust_translator = RobustTranslationService()

def get_robust_translation(text: str, target_lang: str = 'es') -> Tuple[str, str]:
    """Función pública para traducción robusta"""
    return robust_translator.translate_text_robust(text, target_lang)
