#!/usr/bin/env python3
"""
Sistema de Traducción Automática para RiskMap

Este módulo implementa traducción automática para artículos que no estén en español,
tanto durante la ingesta como antes de mostrar en el frontend.

Características:
- Detección automática de idioma
- Traducción a español usando múltiples servicios
- Almacenamiento en base de datos de traducciones
- Sistema de fallback para múltiples APIs
- Cache de traducciones para optimizar rendimiento
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import hashlib

# Importar sistema robusto
try:
    from robust_translation import get_robust_translation, RobustTranslationService
    ROBUST_TRANSLATOR_AVAILABLE = True
    robust_service = RobustTranslationService()
    logger.info("✅ Sistema de traducción robusto cargado")
except ImportError as e:
    ROBUST_TRANSLATOR_AVAILABLE = False
    robust_service = None
    logger.warning(f"⚠️ Sistema robusto no disponible: {e}")

# Librerías para traducción
try:
    from googletrans import Translator as GoogleTranslator
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    import requests
    from deep_translator import GoogleTranslator as DeepGoogleTranslator, MicrosoftTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # Para resultados consistentes
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# Base de datos
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

# Sistema de traducción robusto como fallback
try:
    from robust_translation import get_robust_translation
    ROBUST_TRANSLATION_AVAILABLE = True
except ImportError:
    ROBUST_TRANSLATION_AVAILABLE = False

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService:
    """Servicio principal de traducción."""
    
    def __init__(self, db_connection=None):
        """
        Inicializa el servicio de traducción.
        
        Args:
            db_connection: Conexión a la base de datos (opcional)
        """
        self.db = db_connection
        self.translation_cache = {}
        self.failed_translations = set()
        
        # Inicializar traductores disponibles
        self.translators = self._initialize_translators()
        
        # Crear tabla de traducciones si no existe
        self._ensure_translation_table()
    
    def _initialize_translators(self) -> List[Dict]:
        """Inicializa todos los traductores disponibles."""
        translators = []
        
        if GOOGLE_AVAILABLE:
            translators.append({
                'name': 'google_trans',
                'translator': GoogleTranslator(),
                'priority': 1
            })
        
        if DEEP_TRANSLATOR_AVAILABLE:
            translators.append({
                'name': 'deep_google',
                'translator': DeepGoogleTranslator(source='auto', target='es'),
                'priority': 2
            })
            
            # Microsoft Translator (requiere API key)
            ms_key = os.getenv('MICROSOFT_TRANSLATOR_KEY')
            if ms_key:
                translators.append({
                    'name': 'microsoft',
                    'translator': MicrosoftTranslator(api_key=ms_key, source='auto', target='es'),
                    'priority': 3
                })
        
        # Ordenar por prioridad
        translators.sort(key=lambda x: x['priority'])
        
        logger.info(f"Traductores inicializados: {[t['name'] for t in translators]}")
        return translators
    
    def _ensure_translation_table(self):
        """Asegura que exista la tabla de traducciones en la base de datos."""
        if not self.db:
            return
            
        try:
            cursor = self.db.cursor()
            
            # Crear tabla de traducciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id SERIAL PRIMARY KEY,
                    original_hash VARCHAR(64) UNIQUE NOT NULL,
                    original_text TEXT NOT NULL,
                    original_language VARCHAR(10),
                    translated_text TEXT NOT NULL,
                    target_language VARCHAR(10) DEFAULT 'es',
                    translator_used VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear índices para optimizar consultas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_translations_hash 
                ON translations(original_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_translations_language 
                ON translations(original_language)
            """)
            
            self.db.commit()
            logger.info("Tabla de traducciones creada/verificada correctamente")
            
        except Exception as e:
            logger.error(f"Error creando tabla de traducciones: {e}")
            if self.db:
                self.db.rollback()
    
    def _get_text_hash(self, text: str) -> str:
        """Genera un hash único para el texto."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detecta el idioma del texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Código del idioma detectado o None si no se puede detectar
        """
        if not text or len(text.strip()) < 10:
            return None
            
        try:
            if LANGDETECT_AVAILABLE:
                detected = detect(text)
                logger.info(f"Idioma detectado: {detected}")
                return detected
        except Exception as e:
            logger.warning(f"Error detectando idioma: {e}")
        
        # Fallback: detectar palabras comunes en español
        spanish_indicators = [
            'el', 'la', 'los', 'las', 'de', 'en', 'un', 'una', 'que', 'con',
            'por', 'para', 'del', 'al', 'se', 'no', 'es', 'son', 'fue', 'han'
        ]
        
        words = text.lower().split()[:50]  # Primeras 50 palabras
        spanish_count = sum(1 for word in words if word in spanish_indicators)
        
        if spanish_count >= len(words) * 0.3:  # Si 30%+ son palabras en español
            return 'es'
        
        return 'unknown'
    
    def get_cached_translation(self, text: str) -> Optional[str]:
        """
        Busca una traducción en cache (memoria y base de datos).
        
        Args:
            text: Texto original
            
        Returns:
            Traducción si existe, None caso contrario
        """
        text_hash = self._get_text_hash(text)
        
        # Verificar cache en memoria
        if text_hash in self.translation_cache:
            return self.translation_cache[text_hash]
        
        # Verificar cache en base de datos
        if self.db:
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    "SELECT translated_text FROM translations WHERE original_hash = %s",
                    (text_hash,)
                )
                result = cursor.fetchone()
                
                if result:
                    translation = result[0] if isinstance(result, tuple) else result['translated_text']
                    # Agregar al cache en memoria
                    self.translation_cache[text_hash] = translation
                    return translation
                    
            except Exception as e:
                logger.error(f"Error consultando cache de traducciones: {e}")
        
        return None
    
    def save_translation(self, original_text: str, translated_text: str, 
                        original_language: str, translator_used: str):
        """
        Guarda una traducción en cache y base de datos.
        
        Args:
            original_text: Texto original
            translated_text: Texto traducido
            original_language: Idioma original detectado
            translator_used: Servicio usado para traducir
        """
        text_hash = self._get_text_hash(original_text)
        
        # Guardar en cache de memoria
        self.translation_cache[text_hash] = translated_text
        
        # Guardar en base de datos
        if self.db:
            try:
                cursor = self.db.cursor()
                cursor.execute("""
                    INSERT INTO translations 
                    (original_hash, original_text, original_language, 
                     translated_text, translator_used)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (original_hash) 
                    DO UPDATE SET 
                        translated_text = EXCLUDED.translated_text,
                        translator_used = EXCLUDED.translator_used,
                        updated_at = CURRENT_TIMESTAMP
                """, (text_hash, original_text, original_language, 
                     translated_text, translator_used))
                
                self.db.commit()
                logger.info(f"Traducción guardada: {translator_used}")
                
            except Exception as e:
                logger.error(f"Error guardando traducción: {e}")
                if self.db:
                    self.db.rollback()
    
    async def translate_text(self, text: str, target_language: str = 'es') -> Tuple[str, str]:
        """
        Traduce texto usando el mejor traductor disponible.
        
        Args:
            text: Texto a traducir
            target_language: Idioma de destino (por defecto español)
            
        Returns:
            Tupla (texto_traducido, idioma_original)
        """
        if not text or len(text.strip()) < 3:
            return text, 'unknown'
        
        # Detectar idioma
        original_language = self.detect_language(text)
        
        # Si ya está en español, no traducir
        if original_language == target_language:
            return text, original_language
        
        # Buscar en cache
        cached = self.get_cached_translation(text)
        if cached:
            return cached, original_language or 'unknown'
        
        # Verificar si ya falló antes
        text_hash = self._get_text_hash(text)
        if text_hash in self.failed_translations:
            return text, original_language or 'unknown'
        
        # PRIORIDAD 1: Intentar con sistema robusto (sin httpcore/httpx)
        if ROBUST_TRANSLATOR_AVAILABLE and robust_service:
            try:
                logger.info("🔄 Intentando traducción con sistema robusto (sin httpcore)")
                translated_text, detected_lang = robust_service.translate_text_robust(text, target_language)
                
                if translated_text and translated_text != text and len(translated_text.strip()) > 3:
                    # Guardar traducción exitosa
                    self.save_translation(
                        text, translated_text, 
                        detected_lang or original_language, 
                        'robust_primary'
                    )
                    
                    logger.info("✅ Traducción exitosa con sistema robusto primario")
                    return translated_text, detected_lang or original_language
                    
            except Exception as e:
                logger.warning(f"Error con sistema robusto primario: {e}")
        
        # PRIORIDAD 2: Intentar con traductores tradicionales (con manejo de errores httpcore)
        for translator_info in self.translators:
            try:
                translator_name = translator_info['name']
                translator = translator_info['translator']
                
                logger.info(f"Intentando traducir con {translator_name}")
                
                if translator_name == 'google_trans':
                    result = translator.translate(text, dest=target_language)
                    translated_text = result.text
                    detected_lang = result.src
                    
                elif translator_name in ['deep_google', 'microsoft']:
                    # Actualizar idioma de destino
                    translator.target = target_language
                    translated_text = translator.translate(text)
                    detected_lang = original_language
                
                else:
                    continue
                
                # Validar traducción
                if (translated_text and 
                    translated_text != text and 
                    len(translated_text.strip()) > 3):
                    
                    # Guardar traducción exitosa
                    self.save_translation(
                        text, translated_text, 
                        detected_lang or original_language, 
                        translator_name
                    )
                    
                    logger.info(f"Traducción exitosa con {translator_name}")
                    return translated_text, detected_lang or original_language
                
            except Exception as e:
                error_msg = str(e).lower()
                # Manejo específico para errores de httpcore/httpx y compatibilidad
                if any(keyword in error_msg for keyword in ["synchttptransport", "httpcore", "httpx", "transport", "async"]):
                    logger.warning(f"❌ Error de compatibilidad httpcore/httpx con {translator_name}: {e}")
                    continue
                elif "connection" in error_msg or "timeout" in error_msg:
                    logger.warning(f"Error de conexión con {translator_name}: {e}")
                    continue
                elif "rate limit" in error_msg or "quota" in error_msg:
                    logger.warning(f"Límite de rate/quota con {translator_name}: {e}")
                    continue
                else:
                    logger.warning(f"Error general con traductor {translator_name}: {e}")
                continue
        
        # PRIORIDAD 3: Fallback con traducción robusta antigua (si la nueva falla)
        if ROBUST_TRANSLATION_AVAILABLE:
            try:
                logger.info("🔄 Usando fallback de traducción robusta")
                translated_text, detected_lang = get_robust_translation(text, target_language)
                
                if translated_text and translated_text != text:
                    # Guardar traducción exitosa
                    self.save_translation(
                        text, translated_text, 
                        detected_lang or original_language, 
                        'robust_fallback'
                    )
                    
                    logger.info("✅ Traducción exitosa con fallback robusto")
                    return translated_text, detected_lang or original_language
                    
            except Exception as e:
                logger.warning(f"Error con fallback robusto: {e}")
        
        # Si todo falla, marcar como fallido
        logger.error(f"❌ Traducción completamente fallida para: {text[:100]}...")
        self.failed_translations.add(text_hash)
        
        return text, original_language or 'unknown'
    
    async def translate_article_content(self, article: Dict) -> Dict:
        """
        Traduce el contenido completo de un artículo.
        
        Args:
            article: Diccionario con datos del artículo
            
        Returns:
            Artículo con contenido traducido
        """
        translated_article = article.copy()
        
        # Campos a traducir
        fields_to_translate = ['title', 'content', 'description', 'summary']
        
        for field in fields_to_translate:
            if field in article and article[field]:
                original_text = article[field]
                translated_text, detected_lang = await self.translate_text(original_text)
                
                # Guardar traducción
                translated_article[field] = translated_text
                
                # Guardar idioma original si no existe
                if field == 'title' and detected_lang != 'es':
                    translated_article['original_language'] = detected_lang
                    translated_article['is_translated'] = True
        
        return translated_article

# Funciones de utilidad para integración con el sistema existente

def get_database_connection():
    """Obtiene conexión a la base de datos del sistema."""
    try:
        # Intentar PostgreSQL primero
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'riskmap'),
            user=os.getenv('DB_USER', 'riskmap_user'),
            password=os.getenv('DB_PASSWORD', 'riskmap_pass'),
            port=os.getenv('DB_PORT', 5432)
        )
        return conn
    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL: {e}")
        
        # Fallback a SQLite
        try:
            sqlite_path = os.path.join(os.path.dirname(__file__), 'riskmap.db')
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e2:
            logger.error(f"Error conectando a SQLite: {e2}")
            return None

async def translate_article_for_display(article_data: Dict) -> Dict:
    """
    Traduce un artículo antes de mostrarlo en el frontend.
    
    Args:
        article_data: Datos del artículo
        
    Returns:
        Artículo traducido
    """
    db_conn = get_database_connection()
    translator = TranslationService(db_conn)
    
    try:
        translated = await translator.translate_article_content(article_data)
        return translated
    finally:
        if db_conn:
            db_conn.close()

async def translate_during_ingestion(articles: List[Dict]) -> List[Dict]:
    """
    Traduce artículos durante el proceso de ingesta.
    
    Args:
        articles: Lista de artículos a procesar
        
    Returns:
        Lista de artículos traducidos
    """
    db_conn = get_database_connection()
    translator = TranslationService(db_conn)
    
    try:
        translated_articles = []
        
        for article in articles:
            try:
                translated = await translator.translate_article_content(article)
                translated_articles.append(translated)
                
                # Log del progreso
                if translated.get('is_translated'):
                    logger.info(f"Artículo traducido: {translated.get('title', 'Sin título')[:50]}...")
                
            except Exception as e:
                logger.error(f"Error traduciendo artículo: {e}")
                translated_articles.append(article)  # Agregar original si falla
        
        return translated_articles
        
    finally:
        if db_conn:
            db_conn.close()

def install_translation_dependencies():
    """Instala las dependencias necesarias para traducción."""
    dependencies = [
        'googletrans==4.0.0rc1',
        'deep-translator',
        'langdetect',
        'requests'
    ]
    
    import subprocess
    import sys
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            logger.info(f"Instalado: {dep}")
        except Exception as e:
            logger.error(f"Error instalando {dep}: {e}")

if __name__ == "__main__":
    # Prueba del sistema de traducción
    async def test_translation():
        """Prueba básica del sistema de traducción."""
        print("🔄 Probando sistema de traducción...")
        
        # Crear servicio de traducción
        db_conn = get_database_connection()
        translator = TranslationService(db_conn)
        
        # Texto de prueba
        test_texts = [
            "This is a test article about conflicts in the region",
            "Breaking news: Major incident reported in downtown area",
            "Ceci est un article de test en français",
            "Dies ist ein Testartikel auf Deutsch",
            "Este es un artículo de prueba en español"  # No debe traducirse
        ]
        
        for text in test_texts:
            try:
                translated, lang = await translator.translate_text(text)
                print(f"Original ({lang}): {text}")
                print(f"Traducido: {translated}")
                print("-" * 50)
            except Exception as e:
                print(f"Error: {e}")
        
        if db_conn:
            db_conn.close()
    
    # Ejecutar prueba
    asyncio.run(test_translation())
