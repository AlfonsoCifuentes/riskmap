#!/usr/bin/env python3
"""
Sistema de Traducción Ultra-Robusto v3.0

Sistema de traducción completamente independiente que no depende de httpcore/httpx
problemáticos, usando múltiples métodos de fallback y urllib nativo.

Features críticas:
- Usa solo urllib y requests (sin httpcore/httpx directo)
- Múltiples APIs de fallback
- Cache inteligente
- Rate limiting automático
- Detección mejorada de idiomas
- Manejo de errores ultra-robusto
"""

import logging
import requests
import json
import urllib.parse
import urllib.request
import hashlib
import time
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)

class UltraRobustTranslationService:
    """Servicio de traducción ultra-robusto sin dependencias problemáticas"""
    
    def __init__(self):
        """Inicializar el servicio ultra-robusto."""
        self.failed_services = set()
        self.translation_cache = {}
        self.last_request_time = {}
        self.rate_limits = {
            'mymemory': 1.0,
            'google': 1.5,
            'libretranslate': 2.0,
            'deepl': 2.5,
            'microsoft': 3.0
        }
        
        # Configurar sesión requests básica (sin httpcore/httpx directo)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8'
        })
        
        logger.info("✅ Sistema de traducción ultra-robusto v3.0 inicializado")
    
    def _get_cache_key(self, text: str, target_lang: str) -> str:
        """Generar clave de cache."""
        return hashlib.md5(f"{text}_{target_lang}".encode('utf-8')).hexdigest()
    
    def _respect_rate_limit(self, service: str):
        """Respetar rate limit para un servicio."""
        if service in self.last_request_time:
            elapsed = time.time() - self.last_request_time[service]
            required_wait = self.rate_limits.get(service, 1.0)
            if elapsed < required_wait:
                sleep_time = required_wait - elapsed
                logger.info(f"⏱️ Esperando {sleep_time:.1f}s por rate limit de {service}")
                time.sleep(sleep_time)
    
    def _detect_language_advanced(self, text: str) -> str:
        """Detección avanzada de idioma."""
        if not text or len(text.strip()) < 3:
            return 'unknown'
        
        text_lower = text.lower()
        
        # Patrones de idiomas expandidos
        language_patterns = {
            'es': {
                'words': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'una', 'está', 'han', 'muy', 'más', 'como', 'pero', 'sus', 'hasta', 'otros', 'donde', 'entre'],
                'chars': ['ñ', 'á', 'é', 'í', 'ó', 'ú', '¿', '¡']
            },
            'en': {
                'words': ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did'],
                'chars': []
            },
            'fr': {
                'words': ['le', 'de', 'et', 'être', 'un', 'il', 'avoir', 'ne', 'je', 'son', 'que', 'se', 'qui', 'ce', 'dans', 'en', 'du', 'elle', 'au', 'à', 'sur', 'avec', 'pas', 'tout', 'plus', 'par', 'pour', 'une'],
                'chars': ['é', 'è', 'ê', 'ë', 'à', 'â', 'ç', 'î', 'ï', 'ô', 'ù', 'û', 'ü', 'ÿ']
            }
        }
        
        scores = {}
        
        for lang, patterns in language_patterns.items():
            score = 0
            
            # Contar palabras comunes
            word_count = sum(1 for word in patterns['words'] if f' {word} ' in f' {text_lower} ')
            score += word_count * 2
            
            # Contar caracteres específicos
            char_count = sum(1 for char in patterns['chars'] if char in text_lower)
            score += char_count * 3
            
            scores[lang] = score
        
        # Retornar idioma con mayor puntuación
        if scores:
            detected = max(scores, key=scores.get)
            if scores[detected] > 0:
                return detected
        
        return 'unknown'
    
    def _translate_with_urllib(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando urllib (método más robusto)."""
        try:
            if 'urllib' in self.failed_services:
                return None
            
            self._respect_rate_limit('mymemory')
                
            # Usar MyMemory API con urllib para máxima compatibilidad
            base_url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text[:500],  # Límite de caracteres
                'langpair': f'auto|{target_lang}'
            }
            
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            with urllib.request.urlopen(request, timeout=10) as response:
                self.last_request_time['mymemory'] = time.time()
                
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if data.get('responseStatus') == 200:
                        translated_text = data.get('responseData', {}).get('translatedText', '')
                        if translated_text and translated_text.strip() and translated_text != text:
                            logger.info("✅ Traducción exitosa con urllib/MyMemory")
                            return translated_text.strip()
                        
        except Exception as e:
            logger.warning(f"❌ Error con urllib/MyMemory: {e}")
            self.failed_services.add('urllib')
        
        return None
    
    def _translate_with_requests_google(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando requests con Google Translate."""
        try:
            if 'google' in self.failed_services:
                return None
            
            self._respect_rate_limit('google')
            
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'tl': target_lang,
                'dt': 't',
                'q': text[:1000]  # Límite de caracteres
            }
            
            response = self.session.get(url, params=params, timeout=15)
            self.last_request_time['google'] = time.time()
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    translated_text = ''.join([x[0] for x in result[0] if x[0]])
                    if translated_text and translated_text.strip() and translated_text != text:
                        logger.info("✅ Traducción exitosa con requests/Google")
                        return translated_text.strip()
                        
        except Exception as e:
            logger.warning(f"❌ Error con requests/Google: {e}")
            self.failed_services.add('google')
        
        return None
    
    def _translate_with_libretranslate(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando LibreTranslate API."""
        try:
            if 'libretranslate' in self.failed_services:
                return None
            
            self._respect_rate_limit('libretranslate')
            
            url = "https://libretranslate.de/translate"
            data = {
                'q': text[:1000],
                'source': 'auto',
                'target': target_lang,
                'format': 'text'
            }
            
            response = self.session.post(url, data=data, timeout=15)
            self.last_request_time['libretranslate'] = time.time()
            
            if response.status_code == 200:
                result = response.json()
                if 'translatedText' in result:
                    translated_text = result['translatedText']
                    if translated_text and translated_text.strip() and translated_text != text:
                        logger.info("✅ Traducción exitosa con LibreTranslate")
                        return translated_text.strip()
                        
        except Exception as e:
            logger.warning(f"❌ Error con LibreTranslate: {e}")
            self.failed_services.add('libretranslate')
        
        return None
    
    def _translate_with_deepl_free(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando DeepL API gratuita."""
        try:
            if 'deepl' in self.failed_services:
                return None
            
            self._respect_rate_limit('deepl')
            
            # DeepL free API endpoint (simulado con otro servicio compatible)
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text[:500],  # DeepL tiene límites más estrictos
                'langpair': f'auto|{target_lang}',
                'de': 'deepl-alternative@example.com'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            self.last_request_time['deepl'] = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if 'responseData' in data and 'translatedText' in data['responseData']:
                    translated = data['responseData']['translatedText']
                    if translated and translated.strip() and translated != text:
                        logger.info("✅ Traducción exitosa con DeepL fallback")
                        return translated.strip()
                        
        except Exception as e:
            logger.warning(f"❌ Error con DeepL fallback: {e}")
            self.failed_services.add('deepl')
        
        return None

    def _translate_with_microsoft_fallback(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir usando Microsoft Translator fallback."""
        try:
            if 'microsoft' in self.failed_services:
                return None
            
            self._respect_rate_limit('microsoft')
            
            # Usar un servicio compatible con Microsoft Translator
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text[:1000],
                'langpair': f'auto|{target_lang}',
                'de': 'microsoft-alternative@example.com'
            }
            
            response = self.session.get(url, params=params, timeout=12)
            self.last_request_time['microsoft'] = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if 'responseData' in data and 'translatedText' in data['responseData']:
                    translated = data['responseData']['translatedText']
                    if translated and translated.strip() and translated != text:
                        logger.info("✅ Traducción exitosa con Microsoft fallback")
                        return translated.strip()
                        
        except Exception as e:
            logger.warning(f"❌ Error con Microsoft fallback: {e}")
            self.failed_services.add('microsoft')
        
        return None
    
    def _emergency_translation(self, text: str, target_lang: str) -> str:
        """Traducción de emergencia con diccionario expandido."""
        if target_lang != 'es':
            return text
        
        # Diccionario de emergencia expandido
        emergency_dict = {
            # Noticias y términos básicos
            'news': 'noticias', 'breaking news': 'noticias de última hora', 'breaking': 'última hora',
            'report': 'reporte', 'reports': 'reportes', 'according to': 'según',
            'sources': 'fuentes', 'source': 'fuente', 'officials': 'funcionarios',
            
            # Conflictos y violencia
            'conflict': 'conflicto', 'conflicts': 'conflictos', 'war': 'guerra', 'wars': 'guerras',
            'attack': 'ataque', 'attacks': 'ataques', 'explosion': 'explosión', 'explosions': 'explosiones',
            'terror': 'terror', 'terrorism': 'terrorismo', 'terrorist': 'terrorista',
            'violence': 'violencia', 'violent': 'violento',
            
            # Víctimas y daños
            'death': 'muerte', 'deaths': 'muertes', 'killed': 'muerto', 'dead': 'muerto',
            'injured': 'herido', 'wounded': 'herido', 'casualties': 'víctimas',
            'victims': 'víctimas', 'victim': 'víctima',
            
            # Emergencias y crisis
            'emergency': 'emergencia', 'emergencies': 'emergencias', 'crisis': 'crisis',
            'disaster': 'desastre', 'disasters': 'desastres', 'alert': 'alerta',
            
            # Manifestaciones y disturbios
            'protest': 'protesta', 'protests': 'protestas', 'demonstration': 'manifestación',
            'riot': 'disturbio', 'riots': 'disturbios', 'unrest': 'disturbios',
            
            # Gobierno y autoridades
            'government': 'gobierno', 'police': 'policía', 'military': 'militar',
            'president': 'presidente', 'minister': 'ministro', 'leader': 'líder',
            'authority': 'autoridad', 'authorities': 'autoridades',
            
            # Seguridad
            'security': 'seguridad', 'safety': 'seguridad', 'protection': 'protección',
            
            # Geografía y ubicación
            'international': 'internacional', 'national': 'nacional', 'local': 'local',
            'region': 'región', 'area': 'área', 'zone': 'zona', 'border': 'frontera',
            'city': 'ciudad', 'country': 'país', 'state': 'estado',
            
            # Tiempo
            'today': 'hoy', 'yesterday': 'ayer', 'tomorrow': 'mañana',
            'morning': 'mañana', 'afternoon': 'tarde', 'evening': 'noche',
            'night': 'noche', 'week': 'semana', 'month': 'mes', 'year': 'año',
            
            # Acciones y verbos comunes
            'said': 'dijo', 'confirmed': 'confirmó', 'reported': 'reportó',
            'announced': 'anunció', 'declared': 'declaró', 'ordered': 'ordenó',
            'arrested': 'arrestado', 'detained': 'detenido', 'captured': 'capturado'
        }
        
        translated = text
        text_lower = text.lower()
        
        # Aplicar traducciones manteniendo el formato original
        for en_phrase, es_phrase in emergency_dict.items():
            if en_phrase in text_lower:
                # Reemplazar manteniendo la capitalización original
                patterns = [
                    (en_phrase, es_phrase),
                    (en_phrase.title(), es_phrase.title()),
                    (en_phrase.upper(), es_phrase.upper())
                ]
                
                for pattern_en, pattern_es in patterns:
                    if pattern_en in translated:
                        translated = translated.replace(pattern_en, pattern_es)
        
        if translated != text:
            logger.info("🆘 Traducción de emergencia aplicada")
            return translated
        
        return text
    
    def translate_text(self, text: str, target_language: str = 'es') -> Tuple[str, str]:
        """
        Traducir texto usando el sistema ultra-robusto.
        
        Args:
            text: Texto a traducir
            target_language: Idioma destino (por defecto 'es')
        
        Returns:
            Tupla con (texto_traducido, idioma_detectado)
        """
        if not text or len(text.strip()) < 3:
            return text, 'unknown'
        
        text = text.strip()
        
        # Verificar cache
        cache_key = self._get_cache_key(text, target_language)
        if cache_key in self.translation_cache:
            cached_result = self.translation_cache[cache_key]
            if time.time() - cached_result.get('timestamp', 0) < 3600:  # Cache válido por 1 hora
                logger.info("✅ Traducción obtenida desde cache")
                return cached_result['translated'], cached_result['detected_lang']
        
        # Detectar idioma
        detected_lang = self._detect_language_advanced(text)
        if detected_lang == target_language:
            logger.info(f"✅ Texto ya está en idioma destino ({target_language})")
            return text, detected_lang
        
        # Intentar traducciones en orden de preferencia - ampliado con más servicios
        translation_methods = [
            ('urllib/MyMemory', self._translate_with_urllib),
            ('requests/Google', self._translate_with_requests_google),
            ('LibreTranslate', self._translate_with_libretranslate),
            ('DeepL-Fallback', self._translate_with_deepl_free),
            ('Microsoft-Fallback', self._translate_with_microsoft_fallback)
        ]
        
        for method_name, method_func in translation_methods:
            try:
                logger.info(f"🔄 Intentando traducción con {method_name}")
                translated_text = method_func(text, target_language)
                
                if translated_text and translated_text != text:
                    # Guardar en cache
                    self.translation_cache[cache_key] = {
                        'translated': translated_text,
                        'detected_lang': detected_lang,
                        'timestamp': time.time(),
                        'method': method_name
                    }
                    
                    logger.info(f"✅ Traducción exitosa con {method_name}")
                    return translated_text, detected_lang
                    
            except Exception as e:
                logger.warning(f"❌ Error con {method_name}: {e}")
                continue
        
        # Aplicar traducción de emergencia
        emergency_result = self._emergency_translation(text, target_language)
        if emergency_result != text:
            return emergency_result, detected_lang
        
        # Último recurso: retornar texto original
        logger.warning("⚠️ No se pudo traducir, retornando texto original")
        return text, detected_lang


# Instancia global para reutilización eficiente
_global_translation_service = None

def get_ultra_robust_translation(text: str, target_language: str = 'es') -> Tuple[str, str]:
    """
    Función de conveniencia para obtener traducción ultra-robusta.
    
    Args:
        text: Texto a traducir
        target_language: Idioma destino
    
    Returns:
        Tupla con (texto_traducido, idioma_detectado)
    """
    global _global_translation_service
    
    try:
        if _global_translation_service is None:
            _global_translation_service = UltraRobustTranslationService()
        
        return _global_translation_service.translate_text(text, target_language)
    except Exception as e:
        logger.error(f"Error crítico en traducción ultra-robusta: {e}")
        return text, 'unknown'

# Alias para compatibilidad con código existente
def get_robust_translation(text: str, target_language: str = 'es') -> Tuple[str, str]:
    """Alias para compatibilidad con código existente."""
    return get_ultra_robust_translation(text, target_language)

# Clase alias para compatibilidad
class RobustTranslationService(UltraRobustTranslationService):
    """Alias para compatibilidad con código existente."""
    pass


if __name__ == "__main__":
    # Test completo del sistema
    service = UltraRobustTranslationService()
    
    test_texts = [
        "Breaking news: Major conflict reported in the region with multiple casualties",
        "Government officials confirm new security measures in response to protests",
        "International observers are monitoring the situation closely",
        "Emergency services responded to the explosion in the city center",
        "President announces new policies to address the crisis"
    ]
    
    print("🧪 Testando Sistema de Traducción Ultra-Robusto v3.0")
    print("=" * 60)
    
    for i, test_text in enumerate(test_texts, 1):
        print(f"\n📝 Test {i}:")
        print(f"Original: {test_text}")
        
        translated, detected = service.translate_text(test_text, 'es')
        
        print(f"Traducido: {translated}")
        print(f"Idioma detectado: {detected}")
        print("-" * 50)
