"""
Utilidades comunes y gestión de configuración para el Sistema de Inteligencia Geopolítica.
Implementa configuración robusta, logging avanzado y gestión de base de datos optimizada.
Incluye sistema de encriptación segura para claves API.
"""

import os
import yaml
import logging
import sqlite3
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

class Config:
    """Gestión avanzada de configuración con validación, cache y encriptación de claves."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()
        self._cache = {}
        self._lock = threading.Lock()
        self._setup_logging()
        self._validate_config()
        
        # Initialize secure key manager
        self._secure_keys = None
        self._api_keys_cache = {}
        
    def _get_secure_key_manager(self):
        """Lazy loading del gestor de claves seguras."""
        if self._secure_keys is None:
            try:
                from .secure_keys import SecureKeyManager
                self._secure_keys = SecureKeyManager()
            except ImportError as e:
                logging.warning(f"Secure key manager not available: {e}")
                self._secure_keys = None
        return self._secure_keys
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga configuración desde archivo YAML con manejo robusto de errores."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logging.warning(f"Archivo de configuración no encontrado: {self.config_path}")
                return self._get_default_config()
            
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            if not config:
                logging.warning("Archivo de configuración vacío, usando valores por defecto")
                return self._get_default_config()
            
            # Replace environment variables
            self._replace_env_vars(config)
            logging.info(f"[OK] Configuración cargada desde {self.config_path}")
            return config
            
        except yaml.YAMLError as e:
            logging.error(f"Error parseando configuración YAML: {e}")
            return self._get_default_config()
        except Exception as e:
            logging.error(f"Error cargando configuración: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto cuando no se puede cargar el archivo."""
        return {
            'app': {
                'name': 'Geopolitical Intelligence System',
                'version': '1.0.0',
                'debug': False
            },
            'languages': {
                'supported': ['es', 'en', 'ru', 'zh', 'ar'],
                'primary': 'en'
            },
            'data_sources': {
                'newsapi': {'enabled': True, 'max_articles_per_country': 50},
                'rss': {'enabled': True, 'timeout': 30, 'max_articles_per_source': 15}
            },
            'nlp': {
                'translation': {'service': 'google', 'cache_translations': True},
                'classification': {'model': 'xlm-roberta-base'},
                'sentiment': {'model': 'cardiffnlp/twitter-xlm-roberta-base-sentiment'}
            },
            'database': {
                'path': 'data/geopolitical_intelligence.db',
                'backup_interval_hours': 24
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/geopolitical_intel.log'
            }
        }
    
    def _replace_env_vars(self, obj):
        """Reemplaza variables de entorno en la configuración."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._replace_env_vars(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._replace_env_vars(item)
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            env_value = os.getenv(env_var)
            if env_value is None:
                logging.warning(f"Variable de entorno no encontrada: {env_var}")
                return obj
            return env_value
        return obj
    
    def _validate_config(self):
        """Valida la configuración cargada."""
        required_sections = ['app', 'languages', 'data_sources', 'nlp', 'database']
        missing_sections = []
        
        for section in required_sections:
            if section not in self._config:
                missing_sections.append(section)
        
        if missing_sections:
            logging.warning(f"Secciones de configuración faltantes: {missing_sections}")
        
        # Validar idiomas obligatorios
        supported_langs = self.get('languages.supported', [])
        required_langs = ['es', 'en', 'ru', 'zh', 'ar']
        
        if not all(lang in supported_langs for lang in required_langs):
            logging.warning("No todos los idiomas obligatorios están configurados")
    
    def _setup_logging(self):
        """Configuración avanzada de logging con rotación y filtros."""
        log_config = self.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = log_config.get('format', 
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        log_file = log_config.get('file', 'logs/geopolitical_intel.log')
        
        # Create logs directory
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging with rotation
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def get(self, key: str, default=None):
        """Obtiene valor de configuración con cache."""
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            
            with self._lock:
                self._cache[key] = value
            
            return value
        except (KeyError, TypeError):
            return default
    
    def get_supported_languages(self) -> List[str]:
        """Obtiene lista de idiomas soportados (solo los 5 obligatorios)."""
        return self.get('languages.supported', ['es', 'en', 'ru', 'zh', 'ar'])
    
    def _get_api_key_secure(self, key_name: str, env_var_name: str = None) -> str:
        """Obtiene clave API de forma segura: primero del gestor encriptado, luego de variables de entorno."""
        # Usar nombre de variable de entorno si no se especifica
        if env_var_name is None:
            env_var_name = key_name
        
        # Verificar cache primero
        if key_name in self._api_keys_cache:
            return self._api_keys_cache[key_name]
        
        api_key = ''
        
        # 1. Intentar obtener desde el gestor de claves encriptadas
        secure_manager = self._get_secure_key_manager()
        if secure_manager:
            try:
                api_key = secure_manager.get_key(key_name)
                if api_key:
                    logging.debug(f"[OK] {key_name} loaded from encrypted storage")
                    self._api_keys_cache[key_name] = api_key
                    return api_key
            except Exception as e:
                logging.debug(f"Could not load {key_name} from encrypted storage: {e}")
        
        # 2. Fallback a variables de entorno
        api_key = os.getenv(env_var_name, '')
        if api_key and api_key not in ['your_newsapi_key_here', 'your_openai_key_here', 'your_google_translate_key_here']:
            logging.debug(f"[OK] {key_name} loaded from environment variable")
            self._api_keys_cache[key_name] = api_key
            return api_key
        
        # 3. No encontrada
        if not api_key:
            logging.warning(f"[WARN] {key_name} not configured. Set up with: python -m src.utils.secure_keys setup")
        
        return api_key
    
    def get_newsapi_key(self) -> str:
        """Obtiene clave de NewsAPI con encriptación segura."""
        return self._get_api_key_secure('NEWSAPI_KEY')
    def get_openai_key(self) -> str:
        """Obtiene clave de OpenAI API con encriptación segura."""
        return self._get_api_key_secure('OPENAI_API_KEY')

    def get_google_translate_key(self) -> str:
        """Obtiene clave de Google Translate API con encriptación segura."""
        return self._get_api_key_secure('GOOGLE_TRANSLATE_KEY', 'GOOGLE_TRANSLATE_API_KEY')
    
    def is_api_configured(self, api_name: str) -> bool:
        """Verifica si una API específica está configurada."""
        api_keys = {
            'newsapi': self.get_newsapi_key(),
            'openai': self.get_openai_key(),
            'google_translate': self.get_google_translate_key()
        }
        
        key = api_keys.get(api_name.lower(), '')
        return bool(key and key != f'your_{api_name.lower()}_key_here')
    
    def get_database_path(self) -> str:
        """Obtiene ruta de la base de datos."""
        db_path = self.get('database.path', 'data/geopolitical_intel.db')
        # Asegurar que el directorio existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return db_path


class DatabaseManager:
    """Database connection and management utilities."""
    
    def __init__(self, config: Config):
        self.config = config
        self.db_path = config.get('database.path', 'data/geopolitical_intel.db')
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database file and directory exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Get database connection."""
        import sqlite3
        return sqlite3.connect(self.db_path)

    def _add_column_if_not_exists(self, cursor, table_name, column_name, column_type):
        """Utility to add a column to a table if it doesn't already exist."""
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                logger.info(f"Added column '{column_name}' to table '{table_name}'")
        except sqlite3.Error as e:
            logger.error(f"Error adding column {column_name} to {table_name}: {e}")

    def create_tables(self):
        """Create necessary database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT UNIQUE,
                source TEXT,
                published_at DATETIME,
                language TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                risk_level TEXT,
                conflict_type TEXT,
                country TEXT,
                region TEXT
            )
        ''')

        # Add new columns if they don't exist (for existing databases)
        self._add_column_if_not_exists(cursor, 'articles', 'risk_level', 'TEXT')
        self._add_column_if_not_exists(cursor, 'articles', 'conflict_type', 'TEXT')
        self._add_column_if_not_exists(cursor, 'articles', 'country', 'TEXT')
        self._add_column_if_not_exists(cursor, 'articles', 'region', 'TEXT')
        
        # Processed data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                category TEXT,
                sentiment REAL,
                sentiment_label TEXT,
                summary TEXT,
                entities TEXT,
                translated_content TEXT,
                confidence_score REAL,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')
        
        # Analysis results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                region TEXT,
                category TEXT,
                risk_level INTEGER,
                event_count INTEGER,
                avg_sentiment REAL,
                key_events TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()


# Global configuration instance
config = Config()

# Setup logging
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def ensure_directory(path: str) -> Path:
    """Ensure directory exists and return Path object."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def load_language_models():
    """Load and cache language detection and NLP models."""
    try:
        import spacy
        from langdetect import detect
        
        # Try to load spacy model
        try:
            nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy English model successfully")
        except OSError:
            logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            nlp = None
        
        return {'spacy': nlp}
    except ImportError as e:
        logger.error(f"Error loading language models: {e}")
        return {}


def detect_language(text: str) -> str:
    """Detect language of given text."""
    try:
        from langdetect import detect
        return detect(text)
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return 'en'  # Default to English


def get_country_from_text(text: str) -> List[str]:
    """Extract country names from text using NLP."""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        
        countries = []
        for ent in doc.ents:
            if ent.label_ == "GPE":  # Geopolitical entity
                countries.append(ent.text)
        
        return countries
    except Exception as e:
        logger.warning(f"Country extraction failed: {e}")
        return []


class CategoryMapper:
    """Map news categories to geopolitical risk categories."""
    
    CATEGORY_MAPPING = {
        'protest': ['protest', 'demonstration', 'riot', 'civil unrest', 'strike'],
        'military_conflict': ['war', 'military', 'conflict', 'battle', 'invasion', 'attack'],
        'diplomatic_crisis': ['diplomatic', 'sanctions', 'embassy', 'summit', 'negotiation'],
        'natural_disaster': ['earthquake', 'flood', 'hurricane', 'disaster', 'climate'],
        'neutral': ['neutral', 'general', 'other']
    }
    
    @classmethod
    def map_category(cls, keywords: List[str]) -> str:
        """Map keywords to category."""
        keywords_lower = [k.lower() for k in keywords]
        
        for category, category_keywords in cls.CATEGORY_MAPPING.items():
            if any(keyword in ' '.join(keywords_lower) for keyword in category_keywords):
                return category
        
        return 'neutral'
