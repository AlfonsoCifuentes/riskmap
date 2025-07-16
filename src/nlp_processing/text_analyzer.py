"""
Módulo de análisis de texto para procesamiento NLP multilingüe avanzado.
Maneja clasificación, análisis de sentimiento, NER, resumen y traducción en los 5 idiomas obligatorios.
Optimizado para análisis geopolítico en tiempo real con datos reales.
"""

import logging
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config, DatabaseManager

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """
    Analizador de texto simplificado para clasificación de artículos.
    """
    
    def __init__(self):
        self.risk_keywords = {
            'CRITICAL': ['war', 'guerra', 'bombing', 'attack', 'invasion', 'crisis', 'emergency', 'conflict', 'violence', 'terror', 'nuclear', 'militar'],
            'HIGH': ['tension', 'dispute', 'protest', 'sanction', 'threat', 'riot', 'strike', 'instability', 'rebellion', 'coup'],
            'MEDIUM': ['economy', 'trade', 'diplomatic', 'election', 'policy', 'government', 'political', 'border', 'negotiation'],
            'LOW': ['announcement', 'meeting', 'agreement', 'cooperation', 'visit', 'conference', 'development', 'growth']
        }
        
        self.conflict_keywords = {
            'Military': ['military', 'army', 'defense', 'weapon', 'soldier', 'combat', 'war', 'battle'],
            'Political': ['government', 'parliament', 'election', 'vote', 'policy', 'diplomatic', 'politics'],
            'Economic': ['economy', 'trade', 'market', 'financial', 'business', 'economic', 'commercial'],
            'Social': ['social', 'protest', 'demonstration', 'civil', 'society', 'community', 'people'],
            'Cybersecurity': ['cyber', 'hacker', 'security', 'data', 'digital', 'technology', 'internet'],
            'Natural Disaster': ['flood', 'earthquake', 'hurricane', 'disaster', 'emergency', 'natural', 'climate']
        }
        
        self.country_keywords = {
            'United States': ['usa', 'america', 'washington', 'biden', 'congress'],
            'Russia': ['russia', 'moscow', 'putin', 'kremlin', 'russian'],
            'China': ['china', 'beijing', 'chinese', 'xi jinping'],
            'Ukraine': ['ukraine', 'ukrainian', 'kyiv', 'kiev', 'zelensky'],
            'Israel': ['israel', 'israeli', 'jerusalem', 'gaza', 'palestine'],
            'Iran': ['iran', 'iranian', 'tehran', 'persian'],
            'North Korea': ['north korea', 'pyongyang', 'kim jong'],
            'Syria': ['syria', 'syrian', 'damascus', 'assad'],
            'Venezuela': ['venezuela', 'venezuelan', 'caracas', 'maduro'],
            'Afghanistan': ['afghanistan', 'kabul', 'taliban'],
            'Turkey': ['turkey', 'turkish', 'ankara', 'erdogan'],
            'India': ['india', 'indian', 'delhi', 'modi'],
            'Pakistan': ['pakistan', 'pakistani', 'islamabad'],
            'Global': []  # Default fallback
        }
    
    def analyze_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza un artículo y extrae metadatos de riesgo, conflicto, país y región.
        """
        try:
            title = article_data.get('title', '').lower()
            content = article_data.get('content', '').lower()
            text = f"{title} {content}"
            
            # Analyze risk level
            risk_level = self._classify_risk(text)
            
            # Analyze conflict type
            conflict_type = self._classify_conflict(text)
            
            # Analyze country
            country = self._identify_country(text)
            
            # Determine region based on country
            region = self._get_region_for_country(country)
            
            # Calculate sentiment score (simplified)
            sentiment_score = self._calculate_sentiment(text)
            
            # Generate summary
            summary = self._generate_summary(article_data.get('title', ''), article_data.get('content', ''))
            
            return {
                'risk_level': risk_level,
                'conflict_type': conflict_type,
                'country': country,
                'region': region,
                'sentiment_score': sentiment_score,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return {
                'risk_level': 'LOW',
                'conflict_type': 'Other',
                'country': 'Global',
                'region': 'International',
                'sentiment_score': 0.0,
                'summary': article_data.get('title', 'No title')[:200]
            }
    
    def _classify_risk(self, text: str) -> str:
        """Clasifica el nivel de riesgo basado en palabras clave."""
        risk_scores = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for risk_level, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    risk_scores[risk_level] += 1
        
        # Return the risk level with the highest score
        max_risk = max(risk_scores, key=risk_scores.get)
        return max_risk if risk_scores[max_risk] > 0 else 'LOW'
    
    def _classify_conflict(self, text: str) -> str:
        """Clasifica el tipo de conflicto basado en palabras clave."""
        conflict_scores = {}
        
        for conflict_type, keywords in self.conflict_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                conflict_scores[conflict_type] = score
        
        if not conflict_scores:
            return 'Other'
        
        return max(conflict_scores, key=conflict_scores.get)
    
    def _identify_country(self, text: str) -> str:
        """Identifica el país mencionado en el texto."""
        country_scores = {}
        
        for country, keywords in self.country_keywords.items():
            if country == 'Global':
                continue
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                country_scores[country] = score
        
        if not country_scores:
            return 'Global'
        
        return max(country_scores, key=country_scores.get)
    
    def _get_region_for_country(self, country: str) -> str:
        """Mapea países a regiones."""
        region_mapping = {
            'United States': 'North America',
            'Russia': 'Eastern Europe',
            'China': 'East Asia',
            'Ukraine': 'Eastern Europe',
            'Israel': 'Middle East',
            'Iran': 'Middle East',
            'North Korea': 'East Asia',
            'Syria': 'Middle East',
            'Venezuela': 'South America',
            'Afghanistan': 'Central Asia',
            'Turkey': 'Middle East',
            'India': 'South Asia',
            'Pakistan': 'South Asia',
            'Global': 'International'
        }
        
        return region_mapping.get(country, 'International')
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calcula un score de sentimiento simplificado."""
        positive_words = ['peace', 'agreement', 'cooperation', 'stability', 'growth', 'success']
        negative_words = ['war', 'conflict', 'crisis', 'violence', 'attack', 'threat', 'instability']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        total_words = positive_count + negative_count
        if total_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_words
    
    def _generate_summary(self, title: str, content: str) -> str:
        """Genera un resumen simplificado."""
        if not content:
            return title[:200] + '...' if len(title) > 200 else title
        
        # Take first sentence or first 200 characters
        sentences = content.split('.')
        if sentences and len(sentences[0]) > 50:
            return sentences[0].strip() + '.'
        
        return content[:200] + '...' if len(content) > 200 else content


class LanguageMetadataRegistry:
    """
    Provides metadata for languages, countries, and regions, focusing on geopolitical context.
    """
    # Extended language metadata
    LANGUAGE_METADATA = {
        'en': {'name': 'English', 'region': 'Global', 'conflict_priority': 'standard'},
        'es': {'name': 'Spanish', 'region': 'Global', 'conflict_priority': 'standard'},
        'ru': {'name': 'Russian', 'region': 'Eastern Europe/CIS', 'conflict_priority': 'critical'},
        'zh': {'name': 'Chinese', 'region': 'East Asia', 'conflict_priority': 'critical'},
        'ar': {'name': 'Arabic', 'region': 'MENA', 'conflict_priority': 'critical'},
        'fr': {'name': 'French', 'region': 'Global', 'conflict_priority': 'standard'},
        'de': {'name': 'German', 'region': 'Western Europe', 'conflict_priority': 'standard'},
        'uk': {'name': 'Ukrainian', 'region': 'Eastern Europe', 'conflict_priority': 'critical'},
        'he': {'name': 'Hebrew', 'region': 'Middle East', 'conflict_priority': 'critical'},
        'tr': {'name': 'Turkish', 'region': 'Middle East/Europe', 'conflict_priority': 'critical'},
        'fa': {'name': 'Persian/Farsi', 'region': 'Central/South Asia', 'conflict_priority': 'critical'},
        'ja': {'name': 'Japanese', 'region': 'East Asia', 'conflict_priority': 'standard'},
        'ko': {'name': 'Korean', 'region': 'East Asia', 'conflict_priority': 'standard'},
        'pt': {'name': 'Portuguese', 'region': 'Global', 'conflict_priority': 'standard'},
        'it': {'name': 'Italian', 'region': 'Western Europe', 'conflict_priority': 'standard'},
        'nl': {'name': 'Dutch', 'region': 'Western Europe', 'conflict_priority': 'standard'},
    }

    # Mapeo de países a regiones para una extracción más sencilla
    COUNTRY_TO_REGION = {
        'UA': 'Eastern Europe', 'RU': 'Eastern Europe', 'BY': 'Eastern Europe',
        'IL': 'Middle East', 'PS': 'Middle East', 'SY': 'Middle East', 'IQ': 'Middle East', 
        'LB': 'Middle East', 'SA': 'Middle East', 'AE': 'Middle East', 'QA': 'Middle East',
        'TR': 'Middle East', 'IR': 'Middle East', 'YE': 'Middle East',
        'CN': 'East Asia', 'TW': 'East Asia', 'JP': 'East Asia', 'KR': 'East Asia', 'KP': 'East Asia',
        'US': 'North America', 'CA': 'North America',
        'GB': 'Western Europe', 'DE': 'Western Europe', 'FR': 'Western Europe', 'ES': 'Western Europe',
        'IT': 'Western Europe', 'PL': 'Eastern Europe',
        'CO': 'South America', 'VE': 'South America', 'AR': 'South America', 'BR': 'South America', 'CL': 'South America',
        'MX': 'North America',
        'NG': 'West Africa', 'ET': 'East Africa', 'SD': 'North Africa',
        'IN': 'South Asia', 'PK': 'South Asia', 'AF': 'South Asia', 'MM': 'Southeast Asia',
    }

    def get_region_for_country(self, country_code: str) -> Optional[str]:
        """Obtiene la región para un código de país dado."""
        return self.COUNTRY_TO_REGION.get(country_code.upper())

class GeopoliticalTextAnalyzer:
    """
    Analizador de texto geopolítico para clasificar riesgo, tipo de conflicto y extraer entidades.
    """
    def __init__(self):
        self.risk_keywords = {
            'CRITICAL': ['imminent threat', 'state of emergency', 'war declared', 'catastrophic', 'collapse', 'amenaza inminente', 'estado de emergencia', 'guerra declarada', 'catastrófico', 'colapso', 'неминуемая угроза', 'чрезвычайное положение', 'объявлена война', 'катастрофический', 'коллапс', '迫在眉睫的威胁', '紧急状态', '宣战', '灾难性的', '崩溃', 'تهديد وشيك', 'حالة الطوارئ', 'إعلان الحرب', 'كارثي', 'انهيار'],
            'HIGH': ['escalation', 'mobilization', 'major crisis', 'severe', 'violation', 'escalada', 'movilización', 'crisis mayor', 'grave', 'violación', 'эскалация', 'мобилизация', 'крупный кризис', 'серьезный', 'нарушение', '升级', '动员', '重大危机', '严重的', '违反', 'تصعيد', 'تعبئة', 'أزمة كبيرة', 'خطير', 'انتهاك'],
            'MEDIUM': ['tension', 'dispute', 'unrest', 'protest', 'warning', 'tensión', 'disputa', 'malestar', 'protesta', 'advertencia', 'напряженность', 'спор', 'беспорядки', 'протест', 'предупреждение', '紧张', '争议', '动荡', '抗议', '警告', 'توتر', 'نزاع', 'اضطرابات', 'احتجاج', 'تحذير'],
            'LOW': ['agreement', 'talks', 'discussion', 'stable', 'cooperation', 'acuerdo', 'conversaciones', 'discusión', 'estable', 'cooperación', 'соглашение', 'переговоры', 'обсуждение', 'стабильный', 'сотрудничество', '协议', '会谈', '讨论', '稳定', '合作', 'اتفاق', 'محادثات', 'مناقشة', 'مستقر', 'تعاون']
        }
        self.conflict_keywords = {
            'Military': ['war', 'conflict', 'military', 'troops', 'invasion', 'airstrike', 'battle', 'ceasefire', 'guerra', 'conflicto', 'militar', 'tropas', 'invasión', 'ataque aéreo', 'batalla', 'alto el fuego', 'война', 'конфликт', 'военный', 'войска', 'вторжение', 'воздушный удар', 'битва', 'прекращение огня', '战争', '冲突', '军事', '部队', '入侵', '空袭', '战斗', '停火', 'حرب', 'صراع', 'عسكري', 'قوات', 'غزو', 'غارة جوية', 'معركة', 'وقف إطلاق النار'],
            'Political': ['election', 'government', 'protest', 'coup', 'diplomacy', 'treaty', 'sanctions', 'elección', 'gobierno', 'protesta', 'golpe de estado', 'diplomacia', 'tratado', 'sanciones', 'выборы', 'правительство', 'протест', 'переворот', 'дипломатия', 'договор', 'санкции', '选举', '政府', '抗议', '政变', '外交', '条约', '制裁', 'انتخابات', 'حكومة', 'احتجاج', 'انقلاب', 'دبلوماسية', 'معاهدة', 'عقوبات'],
            'Economic': ['economy', 'crisis', 'inflation', 'recession', 'market', 'trade', 'tariffs', 'economía', 'crisis', 'inflación', 'recesión', 'mercado', 'comercio', 'aranceles', 'экономика', 'кризис', 'инфляция', 'рецессия', 'рынок', 'торговля', 'тарифы', '经济', '危机', '通货膨胀', '衰退', '市场', '贸易', '关税', 'اقتصاد', 'أزمة', 'تضخم', 'ركود', 'سوق', 'تجارة', 'تعريفات'],
            'Social': ['human rights', 'refugees', 'humanitarian', 'social unrest', 'strike', 'derechos humanos', 'refugiados', 'humanitario', 'malestar social', 'huelga', 'права человека', 'беженцы', 'гуманитарный', 'социальные волнения', 'забастовка', '人权', '难民', '人道主义', '社会动荡', '罢工', 'حقوق الإنسان', 'لاجئون', 'إنساني', 'اضطرابات اجتماعية', 'إضراب'],
            'Cybersecurity': ['cyberattack', 'hack', 'data breach', 'malware', 'ransomware', 'ciberataque', 'hackeo', 'violación de datos', 'malware', 'ransomware', 'кибератака', 'взлом', 'утечка данных', 'вредоносное ПО', 'программа-вымогатель', '网络攻击', '黑客', '数据泄露', '恶意软件', '勒索软件', 'هجوم إلكتروني', 'قرصنة', 'خرق للبيانات', 'برامج ضارة', 'برامج الفدية'],
            'Natural Disaster': ['earthquake', 'hurricane', 'flood', 'tsunami', 'wildfire', 'volcano', 'терремото', 'huracán', 'inundación', 'tsunami', 'incendio forestal', 'volcán', 'землетрясение', 'ураган', 'наводнение', 'цунами', 'лесной пожар', 'вулкан', '地震', '飓风', '洪水', '海啸', '野火', '火山', 'زلزال', 'إعصار', 'فيضان', 'تسونامي', 'حريق هائل', 'بركان']
        }
        self.nlp_models = {}
        self._load_nlp_models()

    def _load_nlp_models(self):
        """Carga modelos de NLP de forma segura."""
        try:
            from transformers import pipeline
            # Modelo para Zero-Shot Classification que puede ser usado para NER y más
            self.nlp_models['zero-shot'] = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            # Modelo para NER
            self.nlp_models['ner'] = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", grouped_entities=True)
            logger.info("Modelos de NLP para análisis geopolítico cargados.")
        except Exception as e:
            logger.error(f"No se pudieron cargar los modelos de NLP: {e}")

    def analyze_risk_and_conflict(self, text: str) -> Dict[str, Optional[str]]:
        """Analiza el texto para determinar el nivel de riesgo y el tipo de conflicto."""
        text_lower = text.lower()
        
        # Clasificación de riesgo
        risk_level = 'LOW' # Por defecto
        for level, keywords in self.risk_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                risk_level = level
                break # Detenerse en el nivel más alto encontrado

        # Clasificación de tipo de conflicto
        conflict_type = 'General' # Por defecto
        max_matches = 0
        for type, keywords in self.conflict_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > max_matches:
                max_matches = matches
                conflict_type = type

        return {
            'risk_level': risk_level,
            'conflict_type': conflict_type
        }

    def extract_geographic_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extrae el país y la región del texto usando NER."""
        if 'ner' not in self.nlp_models:
            return {'country': None, 'region': None}
        
        try:
            entities = self.nlp_models['ner'](text)
            locations = [entity['word'] for entity in entities if entity['entity_group'] == 'LOC' or entity['entity_group'] == 'GPE']
            
            # Usar pycountry para encontrar el código de país
            import pycountry
            country_code = None
            country_name = None

            for loc in locations:
                try:
                    country = pycountry.countries.get(name=loc) or pycountry.countries.search_fuzzy(loc)[0]
                    if country:
                        country_code = country.alpha_2
                        country_name = country.name
                        break
                except (LookupError, IndexError):
                    continue
            
            region = None
            if country_code:
                registry = LanguageMetadataRegistry()
                region = registry.get_region_for_country(country_code)

            return {'country': country_name, 'region': region}
        except Exception as e:
            logger.error(f"Error en extracción geográfica: {e}")
            return {'country': None, 'region': None}


class TranslationService:
    """Servicio avanzado de traducción con cache inteligente y múltiples proveedores."""
    
    def __init__(self):
        self.service = config.get('nlp.translation.service', 'google')
        self.cache_enabled = config.get('nlp.translation.cache_translations', True)
        self._translation_cache = {}
        self._cache_lock = threading.Lock()
        self.supported_languages = ['es', 'en', 'ru', 'zh', 'ar']
        
        # Métricas de rendimiento
        self.stats = {
            'total_translations': 0,
            'cache_hits': 0,
            'failed_translations': 0,
            'avg_translation_time': 0.0
        }
    
    def translate_text(self, text: str, target_language: str = 'en', source_language: str = None) -> str:
        """Traduce texto al idioma objetivo con manejo robusto de errores."""
        start_time = time.time()
        
        if not text or not text.strip():
            return text
        
        # Validar idiomas soportados
        if target_language not in self.supported_languages:
            logger.warning(f"Idioma objetivo no soportado: {target_language}")
            return text
        
        # Si el texto ya está en el idioma objetivo, no traducir
        if source_language == target_language:
            return text
        
        # Detectar idioma si no se especifica
        if not source_language:
            source_language = self._detect_language(text)
            if source_language == target_language:
                return text
        
        # Verificar cache
        cache_key = self._generate_cache_key(text, source_language, target_language)
        
        with self._cache_lock:
            if self.cache_enabled and cache_key in self._translation_cache:
                self.stats['cache_hits'] += 1
                return self._translation_cache[cache_key]
        
        try:
            # Intentar traducción con el servicio principal
            translated = self._translate_with_fallback(text, target_language, source_language)
            
            # Actualizar cache
            with self._cache_lock:
                if self.cache_enabled:
                    self._translation_cache[cache_key] = translated
            
            # Actualizar métricas
            self.stats['total_translations'] += 1
            execution_time = time.time() - start_time
            self._update_avg_time(execution_time)
            
            return translated
            
        except Exception as e:
            logger.error(f"Error en traducción: {e}")
            self.stats['failed_translations'] += 1
            return text  # Devolver texto original si falla
    
    def _translate_with_fallback(self, text: str, target_lang: str, source_lang: str) -> str:
        """Traduce con múltiples proveedores como fallback."""
        providers = ['google_free', 'google_official', 'huggingface']
        
        for provider in providers:
            try:
                if provider == 'google_free':
                    return self._translate_google_free(text, target_lang, source_lang)
                elif provider == 'google_official':
                    return self._translate_google(text, target_lang, source_lang)
                elif provider == 'huggingface':
                    return self._translate_huggingface(text, target_lang, source_lang)
            except Exception as e:
                logger.warning(f"Fallo traducción con {provider}: {e}")
                continue
        
        # Si todos fallan, devolver texto original
        logger.error(f"Todos los proveedores de traducción fallaron para {source_lang}->{target_lang}")
        return text
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detecta el idioma del texto con alta precisión para los 5 idiomas soportados."""
        if not text or len(text.strip()) < 2:
            return None
            
        text_clean = text.strip().lower()
        
        # Estrategia 1: Detección por caracteres específicos (muy precisa)
        char_detection = self._detect_by_characters(text_clean)
        if char_detection:
            logger.debug(f"Detección por caracteres: {char_detection}")
            return char_detection
        
        # Estrategia 2: Detección por palabras clave comunes
        keyword_detection = self._detect_by_keywords(text_clean)
        if keyword_detection:
            logger.debug(f"Detección por palabras clave: {keyword_detection}")
            return keyword_detection
        
        # Estrategia 3: langdetect con post-procesamiento mejorado
        langdetect_result = self._detect_with_langdetect(text_clean)
        if langdetect_result:
            logger.debug(f"Detección langdetect mejorada: {langdetect_result}")
            return langdetect_result
        
        # Fallback: detectar por contexto geopolítico
        return self._detect_by_geopolitical_context(text_clean)
    
    def _detect_by_characters(self, text: str) -> Optional[str]:
        """Detecta idioma basándose en caracteres específicos."""
        # Contar caracteres por script
        char_counts = {
            'cyrillic': 0,  # Ruso
            'arabic': 0,    # Árabe
            'chinese': 0,   # Chino
            'latin': 0      # Español/Inglés
        }
        
        for char in text:
            # Cirílico (Ruso)
            if '\u0400' <= char <= '\u04FF' or '\u0500' <= char <= '\u052F':
                char_counts['cyrillic'] += 1
            # Árabe
            elif '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F':
                char_counts['arabic'] += 1
            # Chino (CJK)
            elif '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf':
                char_counts['chinese'] += 1
            # Latín
            elif char.isalpha() and ord(char) < 256:
                char_counts['latin'] += 1
        
        total_chars = sum(char_counts.values())
        if total_chars < 3:
            return None
        
        # Si más del 30% son caracteres específicos, detectar idioma
        if char_counts['cyrillic'] / total_chars > 0.3:
            return 'ru'
        elif char_counts['arabic'] / total_chars > 0.3:
            return 'ar'
        elif char_counts['chinese'] / total_chars > 0.3:
            return 'zh'
        
        return None
    
    def _detect_by_keywords(self, text: str) -> Optional[str]:
        """Detecta idioma basándose en palabras clave comunes."""
        # Palabras muy comunes en cada idioma
        keywords = {
            'es': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'está', 'las', 'del', 'los', 'una', 'como', 'pero', 'sus', 'más', 'esto', 'hasta', 'cuando', 'donde', 'quien', 'hace', 'dice'],
            'en': ['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'words', 'but', 'not', 'what', 'all', 'were', 'when', 'we', 'there', 'can', 'said'],
            'ru': ['в', 'и', 'на', 'не', 'с', 'то', 'что', 'по', 'за', 'для', 'как', 'из', 'до', 'он', 'она', 'они', 'мы', 'вы', 'это', 'этот', 'была', 'были', 'будет', 'может', 'если', 'когда', 'где', 'который', 'которая', 'которые', 'или', 'также', 'между', 'под', 'над'],
            'zh': ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '里', '就是', '现在', '什么', '如果', '还是'],
            'ar': ['في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'التي', 'الذي', 'كان', 'كانت', 'يكون', 'تكون', 'ولا', 'لا', 'أن', 'أو', 'لكن', 'فقط', 'بعد', 'قبل', 'مع', 'عند', 'كل', 'بين', 'تحت', 'فوق', 'ضد', 'حول', 'نحو']
        }
        
        words = text.split()
        if len(words) < 2:
            return None
        
        # Contar coincidencias por idioma
        scores = {}
        for lang, lang_keywords in keywords.items():
            score = sum(1 for word in words if word in lang_keywords)
            if score > 0:
                scores[lang] = score / len(words)  # Normalizar por longitud
        
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])
            # Si la puntuación es significativa, devolver el idioma
            if best_lang[1] > 0.1:  # Al menos 10% de palabras coinciden
                return best_lang[0]
        
        return None
    
    def _detect_with_langdetect(self, text: str) -> Optional[str]:
        """Usa langdetect con mapeo mejorado para los 5 idiomas soportados."""
        try:
            from langdetect import detect, DetectorFactory, detect_langs
            
            # Configurar para resultados deterministas
            DetectorFactory.seed = 0
            
            # Obtener múltiples detecciones con probabilidades
            detections = detect_langs(text)
            
            # Mapeo mejorado que resuelve confusiones comunes
            language_map = {
                # Idiomas principales
                'es': 'es', 'en': 'en', 'ru': 'ru', 'zh': 'zh', 'ar': 'ar',
                # Variantes de chino
                'zh-cn': 'zh', 'zh-tw': 'zh',
                # Idiomas similares al ruso (cirílicos)
                'bg': 'ru',  # Búlgaro -> Ruso (corrección principal)
                'mk': 'ru',  # Macedonio -> Ruso
                'sr': 'ru',  # Сербский -> Русский
                'uk': 'ru',  # Ucraniano -> Ruso
                # Idiomas similares al árabe
                'fa': 'ar',  # Persa -> Árabe
                'ur': 'ar',  # Urdu -> Árabe
                # Idiomas latinos similares
                'ca': 'es',  # Catalán -> Español
                'pt': 'es',  # Portugués -> Español
                'it': 'es',  # Italiano -> Español
                'fr': 'es'   # Francés -> Español (para contexto geopolítico)
            }
            
            # Buscar el primer idioma soportado con probabilidad > 0.7
            for detection in detections:
                mapped_lang = language_map.get(detection.lang, detection.lang)
                if mapped_lang in ['es', 'en', 'ru', 'zh', 'ar'] and detection.prob > 0.7:
                    return mapped_lang
            
            # Si no hay alta confianza, usar el más probable
            if detections:
                best_detection = detections[0]
                mapped_lang = language_map.get(best_detection.lang, best_detection.lang)
                if mapped_lang in ['es', 'en', 'ru', 'zh', 'ar']:
                    return mapped_lang
            
            return None
            
        except ImportError:
            logger.warning("langdetect no disponible")
            return None
        except Exception as e:
            logger.warning(f"Error en langdetect: {e}")
            return None
    
    def _detect_by_geopolitical_context(self, text: str) -> Optional[str]:
        """Detecta idioma basándose en términos geopolíticos específicos."""
        geopolitical_terms = {
            'es': ['guerra', 'conflicto', 'protesta', 'gobierno', 'militar', 'diplomático', 'crisis', 'tensión', 'región', 'país', 'estado', 'política'],
            'en': ['war', 'conflict', 'protest', 'government', 'military', 'diplomatic', 'crisis', 'tension', 'region', 'country', 'state', 'politics'],
            'ru': ['война', 'конфликт', 'протест', 'правительство', 'военный', 'дипломатический', 'кризис', 'напряжение', 'регион', 'страна', 'государство'],
            'zh': ['战争', '冲突', '抗议', '政府', '军事', '外交', '危机', '紧张', '地区', '国家', '政治', '局势'],
            'ar': ['حرب', 'صراع', 'احتجاج', 'حكومة', 'عسكري', 'دبلوماسي', 'أزمة', 'توتر', 'منطقة', 'دولة', 'سياسة']
        }
        
        words = text.split()
        scores = {}
        
        for lang, terms in geopolitical_terms.items():
            score = sum(1 for word in words if word in terms)
            if score > 0:
                scores[lang] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        # Fallback a inglés para contexto geopolítico
        return 'en'
    
    def _generate_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Genera clave única para cache."""
        content = f"{text}_{source_lang}_{target_lang}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _update_avg_time(self, execution_time: float):
        """Actualiza tiempo promedio de traducción."""
        current_avg = self.stats['avg_translation_time']
        total_translations = self.stats['total_translations']
        
        if total_translations == 1:
            self.stats['avg_translation_time'] = execution_time
        else:
            self.stats['avg_translation_time'] = (
                (current_avg * (total_translations - 1) + execution_time) / total_translations
            )
    
    def _translate_google_free(self, text: str, target_lang: str, source_lang: str = None) -> str:
        """Traduce usando la librería gratuita googletrans (no requiere API key)."""
        try:
            # Usar googletrans 4.0.2 que es async
            import asyncio
            from googletrans import Translator
            
            # Mapear códigos de idioma si es necesario
            lang_map = {'zh': 'zh-cn'}  # Ajustar códigos específicos
            target_lang = lang_map.get(target_lang, target_lang)
            source_lang = lang_map.get(source_lang, source_lang) if source_lang else None
            
            async def translate_async():
                translator = Translator()
                result = await translator.translate(text, dest=target_lang, src=source_lang)
                return result.text
            
            # Ejecutar en un nuevo event loop o usar el existente
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si ya hay un loop ejecutándose, usar run_in_executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, translate_async())
                        return future.result(timeout=10)
                else:
                    return loop.run_until_complete(translate_async())
            except RuntimeError:
                # No hay loop, crear uno nuevo
                return asyncio.run(translate_async())
            
        except ImportError:
            logger.warning("googletrans no instalada. Usar: pip install googletrans==4.0.2")
            raise
        except Exception as e:
            logger.error(f"Error con Google Translate gratuito: {e}")
            raise

    def translate_text_with_deepl(self, text: str, target_language: str, source_language: str = None) -> str:
        """Traduce texto usando la API de DeepL (requiere clave)."""
        try:
            from deep_translator import DeepL
            
            deepl_key = config.get_google_translate_key()  # Using same env var for simplicity
            if not deepl_key:
                raise ValueError("DeepL API key not configured")
            
            translator = DeepL(api_key=deepl_key, source=source_language, target=target_language)
            translated_text = translator.translate(text)
            
            logger.info(f"Traducción exitosa con DeepL: {text[:50]}... -> {translated_text[:50]}...")
            return translated_text
        except Exception as e:
            logger.error(f"Error en traducción con DeepL: {e}")
            return text  # Devolver texto original en caso de error

    def translate_text_with_vader(self, text: str, target_language: str, source_language: str) -> str:
        """
        Simula traducción para análisis de sentimiento con VADER, que funciona mejor en inglés.
        Si el idioma de origen no es inglés, devuelve el texto original para ser procesado
        por un modelo de traducción real si es necesario en otra etapa.
        """
        if source_language != 'en':
            # En un escenario real, aquí se podría llamar a un servicio de traducción.
            # Por ahora, devolvemos el texto original asumiendo que el análisis posterior lo manejará.
            logger.info(f"VADER: Devolviendo texto original para idioma '{source_language}'. Se recomienda traducción a 'en'.")
        return text

    def _detect_language_vader(self, text: str) -> str:
        """
        Detecta el idioma del texto.
        """
        try:
            # Vader es específico para inglés, pero esta función podría extenderse
            return 'en' 
        except Exception as e:
            logger.error(f"Error en detección de idioma para VADER: {e}")
            return 'en'

    def get_stats(self) -> Dict[str, Any]:
        """Devuelve estadísticas de uso del servicio de traducción."""
        with self._cache_lock:
            return self.stats.copy()

class GeopoliticalTextAnalyzer:
    """
    Analizador de texto geopolítico para clasificar riesgo, tipo de conflicto y extraer entidades.
    """
    def __init__(self):
        self.risk_keywords = {
            'CRITICAL': ['imminent threat', 'state of emergency', 'war declared', 'catastrophic', 'collapse', 'amenaza inminente', 'estado de emergencia', 'guerra declarada', 'catastrófico', 'colapso', 'неминуемая угроза', 'чрезвычайное положение', 'объявлена война', 'катастрофический', 'коллапс', '迫在眉睫的威胁', '紧急状态', '宣战', '灾难性的', '崩溃', 'تهديد وشيك', 'حالة الطوارئ', 'إعلان الحرب', 'كارثي', 'انهيار'],
            'HIGH': ['escalation', 'mobilization', 'major crisis', 'severe', 'violation', 'escalada', 'movilización', 'crisis mayor', 'grave', 'violación', 'эскалация', 'мобилизация', 'крупный кризис', 'серьезный', 'нарушение', '升级', '动员', '重大危机', '严重的', '违反', 'تصعيد', 'تعبئة', 'أزمة كبيرة', 'خطير', 'انتهاك'],
            'MEDIUM': ['tension', 'dispute', 'unrest', 'protest', 'warning', 'tensión', 'disputa', 'malestar', 'protesta', 'advertencia', 'напряженность', 'спор', 'беспорядки', 'протест', 'предупреждение', '紧张', '争议', '动荡', '抗议', '警告', 'توتر', 'نزاع', 'اضطرابات', 'احتجاج', 'تحذير'],
            'LOW': ['agreement', 'talks', 'discussion', 'stable', 'cooperation', 'acuerdo', 'conversaciones', 'discusión', 'estable', 'cooperación', 'соглашение', 'переговоры', 'обсуждение', 'стабильный', 'сотрудничество', '协议', '会谈', '讨论', '稳定', '合作', 'اتفاق', 'محادثات', 'مناقشة', 'مستقر', 'تعاون']
        }
        self.conflict_keywords = {
            'Military': ['war', 'conflict', 'military', 'troops', 'invasion', 'airstrike', 'battle', 'ceasefire', 'guerra', 'conflicto', 'militar', 'tropas', 'invasión', 'ataque aéreo', 'batalla', 'alto el fuego', 'война', 'конфликт', 'военный', 'войска', 'вторжение', 'воздушный удар', 'битва', 'прекращение огня', '战争', '冲突', '军事', '部队', '入侵', '空袭', '战斗', '停火', 'حرب', 'صراع', 'عسكري', 'قوات', 'غزو', 'غارة جوية', 'معركة', 'وقف إطلاق النار'],
            'Political': ['election', 'government', 'protest', 'coup', 'diplomacy', 'treaty', 'sanctions', 'elección', 'gobierno', 'protesta', 'golpe de estado', 'diplomacia', 'tratado', 'sanciones', 'выборы', 'правительство', 'протест', 'переворот', 'дипломатия', 'договор', 'санкции', '选举', '政府', '抗议', '政变', '外交', '条约', '制裁', 'انتخابات', 'حكومة', 'احتجاج', 'انقلاب', 'دبلوماسية', 'معاهدة', 'عقوبات'],
            'Economic': ['economy', 'crisis', 'inflation', 'recession', 'market', 'trade', 'tariffs', 'economía', 'crisis', 'inflación', 'recesión', 'mercado', 'comercio', 'aranceles', 'экономика', 'кризис', 'инфляция', 'рецессия', 'рынок', 'торговля', 'тарифы', '经济', '危机', '通货膨胀', '衰退', '市场', '贸易', '关税', 'اقتصاد', 'أزمة', 'تضخم', 'ركود', 'سوق', 'تجارة', 'تعريفات'],
            'Social': ['human rights', 'refugees', 'humanitarian', 'social unrest', 'strike', 'derechos humanos', 'refugiados', 'humanitario', 'malestar social', 'huelga', 'права человека', 'беженцы', 'гуманитарный', 'социальные волнения', 'забастовка', '人权', '难民', '人道主义', '社会动荡', '罢工', 'حقوق الإنسان', 'لاجئون', 'إنساني', 'اضطرابات اجتماعية', 'إضراب'],
            'Cybersecurity': ['cyberattack', 'hack', 'data breach', 'malware', 'ransomware', 'ciberataque', 'hackeo', 'violación de datos', 'malware', 'ransomware', 'кибератака', 'взлом', 'утечка данных', 'вредоносное ПО', 'программа-вымогатель', '网络攻击', '黑客', '数据泄露', '恶意软件', '勒索软件', 'هجوم إلكتروني', 'قرصنة', 'خرق للبيانات', 'برامج ضارة', 'برامج الفدية'],
            'Natural Disaster': ['earthquake', 'hurricane', 'flood', 'tsunami', 'wildfire', 'volcano', 'терремото', 'huracán', 'inundación', 'tsunami', 'incendio forestal', 'volcán', 'землетрясение', 'ураган', 'наводнение', 'цунами', 'лесной пожар', 'вулкан', '地震', '飓风', '洪水', '海啸', '野火', '火山', 'زلزال', 'إعصار', 'فيضان', 'تسونامي', 'حريق هائل', 'بركان']
        }
        self.nlp_models = {}
        self._load_nlp_models()

    def _load_nlp_models(self):
        """Carga modelos de NLP de forma segura."""
        try:
            from transformers import pipeline
            # Modelo para Zero-Shot Classification que puede ser usado para NER y más
            self.nlp_models['zero-shot'] = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            # Modelo para NER
            self.nlp_models['ner'] = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", grouped_entities=True)
            logger.info("Modelos de NLP para análisis geopolítico cargados.")
        except Exception as e:
            logger.error(f"No se pudieron cargar los modelos de NLP: {e}")

    def analyze_risk_and_conflict(self, text: str) -> Dict[str, Optional[str]]:
        """Analiza el texto para determinar el nivel de riesgo y el tipo de conflicto."""
        text_lower = text.lower()
        
        # Clasificación de riesgo
        risk_level = 'LOW' # Por defecto
        for level, keywords in self.risk_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                risk_level = level
                break # Detenerse en el nivel más alto encontrado

        # Clasificación de tipo de conflicto
        conflict_type = 'General' # Por defecto
        max_matches = 0
        for type, keywords in self.conflict_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > max_matches:
                max_matches = matches
                conflict_type = type

        return {
            'risk_level': risk_level,
            'conflict_type': conflict_type
        }

    def extract_geographic_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extrae el país y la región del texto usando NER."""
        if 'ner' not in self.nlp_models:
            return {'country': None, 'region': None}
        
        try:
            entities = self.nlp_models['ner'](text)
            locations = [entity['word'] for entity in entities if entity['entity_group'] == 'LOC' or entity['entity_group'] == 'GPE']
            
            # Usar pycountry para encontrar el código de país
            import pycountry
            country_code = None
            country_name = None

            for loc in locations:
                try:
                    country = pycountry.countries.get(name=loc) or pycountry.countries.search_fuzzy(loc)[0]
                    if country:
                        country_code = country.alpha_2
                        country_name = country.name
                        break
                except (LookupError, IndexError):
                    continue
            
            region = None
            if country_code:
                registry = LanguageMetadataRegistry()
                region = registry.get_region_for_country(country_code)

            return {'country': country_name, 'region': region}
        except Exception as e:
            logger.error(f"Error en extracción geográfica: {e}")
            return {'country': None, 'region': None}


class TranslationService:
    """Servicio avanzado de traducción con cache inteligente y múltiples proveedores."""
    
    def __init__(self):
        self.service = config.get('nlp.translation.service', 'google')
        self.cache_enabled = config.get('nlp.translation.cache_translations', True)
        self._translation_cache = {}
        self._cache_lock = threading.Lock()
        self.supported_languages = ['es', 'en', 'ru', 'zh', 'ar']
        
        # Métricas de rendimiento
        self.stats = {
            'total_translations': 0,
            'cache_hits': 0,
            'failed_translations': 0,
            'avg_translation_time': 0.0
        }
    
    def translate_text(self, text: str, target_language: str = 'en', source_language: str = None) -> str:
        """Traduce texto al idioma objetivo con manejo robusto de errores."""
        start_time = time.time()
        
        if not text or not text.strip():
            return text
        
        # Validar idiomas soportados
        if target_language not in self.supported_languages:
            logger.warning(f"Idioma objetivo no soportado: {target_language}")
            return text
        
        # Si el texto ya está en el idioma objetivo, no traducir
        if source_language == target_language:
            return text
        
        # Detectar idioma si no se especifica
        if not source_language:
            source_language = self._detect_language(text)
            if source_language == target_language:
                return text
        
        # Verificar cache
        cache_key = self._generate_cache_key(text, source_language, target_language)
        
        with self._cache_lock:
            if self.cache_enabled and cache_key in self._translation_cache:
                self.stats['cache_hits'] += 1
                return self._translation_cache[cache_key]
        
        try:
            # Intentar traducción con el servicio principal
            translated = self._translate_with_fallback(text, target_language, source_language)
            
            # Actualizar cache
            with self._cache_lock:
                if self.cache_enabled:
                    self._translation_cache[cache_key] = translated
            
            # Actualizar métricas
            self.stats['total_translations'] += 1
            execution_time = time.time() - start_time
            self._update_avg_time(execution_time)
            
            return translated
            
        except Exception as e:
            logger.error(f"Error en traducción: {e}")
            self.stats['failed_translations'] += 1
            return text  # Devolver texto original si falla
    
    def _translate_with_fallback(self, text: str, target_lang: str, source_lang: str) -> str:
        """Traduce con múltiples proveedores como fallback."""
        providers = ['google_free', 'google_official', 'huggingface']
        
        for provider in providers:
            try:
                if provider == 'google_free':
                    return self._translate_google_free(text, target_lang, source_lang)
                elif provider == 'google_official':
                    return self._translate_google(text, target_lang, source_lang)
                elif provider == 'huggingface':
                    return self._translate_huggingface(text, target_lang, source_lang)
            except Exception as e:
                logger.warning(f"Fallo traducción con {provider}: {e}")
                continue
        
        # Si todos fallan, devolver texto original
        logger.error(f"Todos los proveedores de traducción fallaron para {source_lang}->{target_lang}")
        return text
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detecta el idioma del texto con alta precisión para los 5 idiomas soportados."""
        if not text or len(text.strip()) < 2:
            return None
            
        text_clean = text.strip().lower()
        
        # Estrategia 1: Detección por caracteres específicos (muy precisa)
        char_detection = self._detect_by_characters(text_clean)
        if char_detection:
            logger.debug(f"Detección por caracteres: {char_detection}")
            return char_detection
        
        # Estrategia 2: Detección por palabras clave comunes
        keyword_detection = self._detect_by_keywords(text_clean)
        if keyword_detection:
            logger.debug(f"Detección por palabras clave: {keyword_detection}")
            return keyword_detection
        
        # Estrategia 3: langdetect con post-procesamiento mejorado
        langdetect_result = self._detect_with_langdetect(text_clean)
        if langdetect_result:
            logger.debug(f"Detección langdetect mejorada: {langdetect_result}")
            return langdetect_result
        
        # Fallback: detectar por contexto geopolítico
        return self._detect_by_geopolitical_context(text_clean)
    
    def _detect_by_characters(self, text: str) -> Optional[str]:
        """Detecta idioma basándose en caracteres específicos."""
        # Contar caracteres por script
        char_counts = {
            'cyrillic': 0,  # Ruso
            'arabic': 0,    # Árabe
            'chinese': 0,   # Chino
            'latin': 0      # Español/Inglés
        }
        
        for char in text:
            # Cirílico (Ruso)
            if '\u0400' <= char <= '\u04FF' or '\u0500' <= char <= '\u052F':
                char_counts['cyrillic'] += 1
            # Árabe
            elif '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F':
                char_counts['arabic'] += 1
            # Chino (CJK)
            elif '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf':
                char_counts['chinese'] += 1
            # Latín
            elif char.isalpha() and ord(char) < 256:
                char_counts['latin'] += 1
        
        total_chars = sum(char_counts.values())
        if total_chars < 3:
            return None
        
        # Si más del 30% son caracteres específicos, detectar idioma
        if char_counts['cyrillic'] / total_chars > 0.3:
            return 'ru'
        elif char_counts['arabic'] / total_chars > 0.3:
            return 'ar'
        elif char_counts['chinese'] / total_chars > 0.3:
            return 'zh'
        
        return None
    
    def _detect_by_keywords(self, text: str) -> Optional[str]:
        """Detecta idioma basándose en palabras clave comunes."""
        # Palabras muy comunes en cada idioma
        keywords = {
            'es': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'está', 'las', 'del', 'los', 'una', 'como', 'pero', 'sus', 'más', 'esto', 'hasta', 'cuando', 'donde', 'quien', 'hace', 'dice'],
            'en': ['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'words', 'but', 'not', 'what', 'all', 'were', 'when', 'we', 'there', 'can', 'said'],
            'ru': ['в', 'и', 'на', 'не', 'с', 'то', 'что', 'по', 'за', 'для', 'как', 'из', 'до', 'он', 'она', 'они', 'мы', 'вы', 'это', 'этот', 'была', 'были', 'будет', 'может', 'если', 'когда', 'где', 'который', 'которая', 'которые', 'или', 'также', 'между', 'под', 'над'],
            'zh': ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '里', '就是', '现在', '什么', '如果', '还是'],
            'ar': ['في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'التي', 'الذي', 'كان', 'كانت', 'يكون', 'تكون', 'ولا', 'لا', 'أن', 'أو', 'لكن', 'فقط', 'بعد', 'قبل', 'مع', 'عند', 'كل', 'بين', 'تحت', 'فوق', 'ضد', 'حول', 'نحو']
        }
        
        words = text.split()
        if len(words) < 2:
            return None
        
        # Contar coincidencias por idioma
        scores = {}
        for lang, lang_keywords in keywords.items():
            score = sum(1 for word in words if word in lang_keywords)
            if score > 0:
                scores[lang] = score / len(words)  # Normalizar por longitud
        
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])
            # Si la puntuación es significativa, devolver el idioma
            if best_lang[1] > 0.1:  # Al menos 10% de palabras coinciden
                return best_lang[0]
        
        return None
    
    def _detect_with_langdetect(self, text: str) -> Optional[str]:
        """Usa langdetect con mapeo mejorado para los 5 idiomas soportados."""
        try:
            from langdetect import detect, DetectorFactory, detect_langs
            
            # Configurar para resultados deterministas
            DetectorFactory.seed = 0
            
            # Obtener múltiples detecciones con probabilidades
            detections = detect_langs(text)
            
            # Mapeo mejorado que resuelve confusiones comunes
            language_map = {
                # Idiomas principales
                'es': 'es', 'en': 'en', 'ru': 'ru', 'zh': 'zh', 'ar': 'ar',
                # Variantes de chino
                'zh-cn': 'zh', 'zh-tw': 'zh',
                # Idiomas similares al ruso (cirílicos)
                'bg': 'ru',  # Búlgaro -> Ruso (corrección principal)
                'mk': 'ru',  # Macedonio -> Ruso
                'sr': 'ru',  # Сербский -> Русский
                'uk': 'ru',  # Ucraniano -> Ruso
                # Idiomas similares al árabe
                'fa': 'ar',  # Persa -> Árabe
                'ur': 'ar',  # Urdu -> Árabe
                # Idiomas latinos similares
                'ca': 'es',  # Catalán -> Español
                'pt': 'es',  # Portugués -> Español
                'it': 'es',  # Italiano -> Español
                'fr': 'es'   # Francés -> Español (para contexto geopolítico)
            }
            
            # Buscar el primer idioma soportado con probabilidad > 0.7
            for detection in detections:
                mapped_lang = language_map.get(detection.lang, detection.lang)
                if mapped_lang in ['es', 'en', 'ru', 'zh', 'ar'] and detection.prob > 0.7:
                    return mapped_lang
            
            # Si no hay alta confianza, usar el más probable
            if detections:
                best_detection = detections[0]
                mapped_lang = language_map.get(best_detection.lang, best_detection.lang)
                if mapped_lang in ['es', 'en', 'ru', 'zh', 'ar']:
                    return mapped_lang
            
            return None
            
        except ImportError:
            logger.warning("langdetect no disponible")
            return None
        except Exception as e:
            logger.warning(f"Error en langdetect: {e}")
            return None
    
    def _detect_by_geopolitical_context(self, text: str) -> Optional[str]:
        """Detecta idioma basándose en términos geopolíticos específicos."""
        geopolitical_terms = {
            'es': ['guerra', 'conflicto', 'protesta', 'gobierno', 'militar', 'diplomático', 'crisis', 'tensión', 'región', 'país', 'estado', 'política'],
            'en': ['war', 'conflict', 'protest', 'government', 'military', 'diplomatic', 'crisis', 'tension', 'region', 'country', 'state', 'politics'],
            'ru': ['война', 'конфликт', 'протест', 'правительство', 'военный', 'дипломатический', 'кризис', 'напряжение', 'регион', 'страна', 'государство'],
            'zh': ['战争', '冲突', '抗议', '政府', '军事', '外交', '危机', '紧张', '地区', '国家', '政治', '局势'],
            'ar': ['حرب', 'صراع', 'احتجاج', 'حكومة', 'عسكري', 'دبلوماسي', 'أزمة', 'توتر', 'منطقة', 'دولة', 'سياسة']
        }
        
        words = text.split()
        scores = {}
        
        for lang, terms in geopolitical_terms.items():
            score = sum(1 for word in words if word in terms)
            if score > 0:
                scores[lang] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        # Fallback a inglés para contexto geopolítico
        return 'en'
    
    def _generate_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Genera clave única para cache."""
        content = f"{text}_{source_lang}_{target_lang}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _update_avg_time(self, execution_time: float):
        """Actualiza tiempo promedio de traducción."""
        current_avg = self.stats['avg_translation_time']
        total_translations = self.stats['total_translations']
        
        if total_translations == 1:
            self.stats['avg_translation_time'] = execution_time
        else:
            self.stats['avg_translation_time'] = (
                (current_avg * (total_translations - 1) + execution_time) / total_translations
            )
    
    def _translate_google_free(self, text: str, target_lang: str, source_lang: str = None) -> str:
        """Traduce usando la librería gratuita googletrans (no requiere API key)."""
        try:
            # Usar googletrans 4.0.2 que es async
            import asyncio
            from googletrans import Translator
            
            # Mapear códigos de idioma si es necesario
            lang_map = {'zh': 'zh-cn'}  # Ajustar códigos específicos
            target_lang = lang_map.get(target_lang, target_lang)
            source_lang = lang_map.get(source_lang, source_lang) if source_lang else None
            
            async def translate_async():
                translator = Translator()
                result = await translator.translate(text, dest=target_lang, src=source_lang)
                return result.text
            
            # Ejecutar en un nuevo event loop o usar el existente
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si ya hay un loop ejecutándose, usar run_in_executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, translate_async())
                        return future.result(timeout=10)
                else:
                    return loop.run_until_complete(translate_async())
            except RuntimeError:
                # No hay loop, crear uno nuevo
                return asyncio.run(translate_async())
            
        except ImportError:
            logger.warning("googletrans no instalada. Usar: pip install googletrans==4.0.2")
            raise
        except Exception as e:
            logger.error(f"Error con Google Translate gratuito: {e}")
            raise

    def translate_text_with_deepl(self, text: str, target_language: str, source_language: str = None) -> str:
        """Traduce texto usando la API de DeepL (requiere clave)."""
        try:
            from deep_translator import DeepL
            
            deepl_key = config.get_google_translate_key()  # Using same env var for simplicity
            if not deepl_key:
                raise ValueError("DeepL API key not configured")
            
            translator = DeepL(api_key=deepl_key, source=source_language, target=target_language)
            translated_text = translator.translate(text)
            
            logger.info(f"Traducción exitosa con DeepL: {text[:50]}... -> {translated_text[:50]}...")
            return translated_text
        except Exception as e:
            logger.error(f"Error en traducción con DeepL: {e}")
            return text  # Devolver texto original en caso de error

    def translate_text_with_vader(self, text: str, target_language: str, source_language: str) -> str:
        """
        Simula traducción para análisis de sentimiento con VADER, que funciona mejor en inglés.
        Si el idioma de origen no es inglés, devuelve el texto original para ser procesado
        por un modelo de traducción real si es necesario en otra etapa.
        """
        if source_language != 'en':
            # En un escenario real, aquí se podría llamar a un servicio de traducción.
            # Por ahora, devolvemos el texto original asumiendo que el análisis posterior lo manejará.
            logger.info(f"VADER: Devolviendo texto original para idioma '{source_language}'. Se recomienda traducción a 'en'.")
        return text

    def _detect_language_vader(self, text: str) -> str:
        """
        Detecta el idioma del texto.
        """
        try:
            # Vader es específico para inglés, pero esta función podría extenderse
            return 'en' 
        except Exception as e:
            logger.error(f"Error en detección de idioma para VADER: {e}")
            return 'en'

    def get_stats(self) -> Dict[str, Any]:
        """Devuelve estadísticas de uso del servicio de traducción."""
        with self._cache_lock:
            return self.stats.copy()