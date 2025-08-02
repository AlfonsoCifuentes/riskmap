"""
Utilidades comunes y gestión de configuración para el Sistema de Inteligencia Geopolítica.
Implementa una configuración robusta y validada con Pydantic, logging centralizado
hasta la gestión de base de datos.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import threading

from pydantic import BaseModel, Field, validator, ValidationError

# Cargar variables de entorno desde .env
load_dotenv()

# --- Modelos de Configuración con Pydantic ---


class AppConfig(BaseModel):
    """Configuración general de la aplicación."""
    debug: bool = Field(default=False, description="Modo debug")
    host: str = Field(default="127.0.0.1", description="Host del servidor")
    port: int = Field(default=5001, description="Puerto del servidor")


class DatabaseConfig(BaseModel):
    """Configuración de base de datos."""
    path: str = Field(
        default="data/geopolitical_intel.db",
        description="Ruta de la base de datos")
    backup_enabled: bool = Field(default=True,
                                 description="Habilitar backups automáticos")
    max_connections: int = Field(default=10,
                                 description="Máximo número de conexiones")


class LoggingConfig(BaseModel):
    """Configuración de logging."""
    level: str = Field(default="INFO", description="Nivel de logging")
    file_path: str = Field(
        default="logs/geopolitical_intel.log",
        description="Ruta del archivo de log")
    max_bytes: int = Field(
        default=10485760,
        description="Tamaño máximo del archivo de log")
    backup_count: int = Field(
        default=5, description="Número de backups de logs")


class DashboardConfig(BaseModel):
    """Configuración del dashboard."""
    secret_key: str = Field(
        default="geopolitical-intelligence-secure-key-2024",
        description="Clave secreta")
    refresh_interval: int = Field(
        default=30, description="Intervalo de actualización en segundos")


class Config(BaseModel):
    """Configuración principal del sistema."""
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración usando notación de punto."""
        keys = key.split('.')
        obj = self
        try:
            for k in keys:
                obj = getattr(obj, k)
            return obj
        except AttributeError:
            return default

    def get_supported_languages(self):
        # Dummy: return a list of supported languages
        return ['en', 'es', 'ru', 'zh', 'ar']

    def get_newsapi_key(self) -> Optional[str]:
        """Obtiene la API key de NewsAPI desde configuración o variable de entorno."""
        return os.getenv('NEWSAPI_KEY') or self.get('api_keys.newsapi')
    
    def get_google_translate_key(self) -> Optional[str]:
        """Obtiene la API key de Google Translate desde configuración o variable de entorno."""
        return os.getenv('GOOGLE_TRANSLATE_KEY') or self.get('api_keys.google_translate')
    
    def get_openai_key(self) -> Optional[str]:
        """Obtiene la API key de OpenAI desde configuración o variable de entorno."""
        return os.getenv('OPENAI_API_KEY') or self.get('api_keys.openai')
    
    def get_deepseek_key(self) -> Optional[str]:
        """Obtiene la API key de DeepSeek desde configuración o variable de entorno."""
        return os.getenv('DEEPSEEK_API_KEY') or self.get('api_keys.deepseek')
    
    def get_groq_key(self) -> Optional[str]:
        """Obtiene la API key de GroqCloud desde configuración o variable de entorno."""
        return os.getenv('GROQ_API_KEY') or self.get('api_keys.groq')
    
    def get_hf_token(self) -> Optional[str]:
        """Obtiene el token de Hugging Face desde configuración o variable de entorno."""
        return os.getenv('HUGGINGFACE_TOKEN') or self.get('api_keys.huggingface')


# --- Configuración Global ---
config = Config()

# --- Configuración de Logging ---

def setup_logging():
    """Configura el sistema de logging centralizado."""

    log_dir = Path(config.logging.file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.logging.level.upper()))

    if logger.handlers:
        logger.handlers.clear()

    file_handler = RotatingFileHandler(
        config.logging.file_path,
        maxBytes=config.logging.max_bytes,
        backupCount=config.logging.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


class DatabaseManager:
    """Gestor centralizado de base de datos con pooling de conexiones."""

    def __init__(self, config: Config):
        self.config = config
        self.db_path = config.database.path
        self._lock = threading.Lock()
        self._setup_database()

    def get_connection(self):
        """Devuelve una conexión SQLite thread-safe."""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _setup_database(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
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
                    country TEXT,
                    region TEXT,
                    summary TEXT,
                    risk_score REAL,
                    sentiment_score REAL,
                    sentiment_label TEXT,
                    conflict_type TEXT,
                    key_persons TEXT,
                    key_locations TEXT,
                    entities_json TEXT,
                    conflict_indicators TEXT,
                    visual_risk_score REAL,
                    detected_objects TEXT,
                    visual_analysis_json TEXT,
                    image_url TEXT,
                    processed INTEGER DEFAULT 0,
                    processing_time REAL,
                    quality_score REAL
                )
            ''')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at)')

            # Add new columns if not exist
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN processed INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN processing_time REAL")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN quality_score REAL")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN validation_result TEXT")
            except sqlite3.OperationalError:
                pass

            conn.commit()
        except Exception as e:
            logger.error(f"Error init DB: {e}")
            conn.rollback()
        finally:
            conn.close()

db_manager = DatabaseManager(config)

def get_database_path() -> str:
    """
    Obtener la ruta de la base de datos principal.
    Esta función es utilizada por múltiples módulos para acceder a la BD.
    """
    return config.database.path
