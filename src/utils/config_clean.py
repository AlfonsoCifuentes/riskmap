"""
Utilidades comunes y gestión de configuración para el Sistema de Inteligencia Geopolítica.
Implementa una configuración robusta y validada con Pydantic, logging centralizado
y gestión de base de datos.
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
        default="data/geopolitical_intelligence.db",
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


# --- Configuración Global ---
config = Config()

# --- Configuración de Logging ---


def setup_logging():
    """Configura el sistema de logging centralizado."""

    # Crear directorio de logs si no existe
    log_dir = Path(config.logging.file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configurar logger principal
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.logging.level.upper()))

    # Evitar múltiples handlers
    if logger.handlers:
        logger.handlers.clear()

    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        config.logging.file_path,
        maxBytes=config.logging.max_bytes,
        backupCount=config.logging.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formato de logging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Inicializar logging
logger = setup_logging()

# --- Gestor de Base de Datos ---


class DatabaseManager:
    """Gestor centralizado de base de datos con pooling de conexiones."""

    def __init__(self, config: Config):
        self.config = config
        self.db_path = config.database.path
        self._lock = threading.Lock()
        self._setup_database()

    def _setup_database(self):
        """Inicializa la estructura de la base de datos."""
        # Crear directorio de datos si no existe
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Tabla principal de artículos
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
                    image_url TEXT
                )
            ''')

            # Índices para mejorar rendimiento
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_articles_risk_score ON articles(risk_score)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_articles_country ON articles(country)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)')

            conn.commit()
            logger.info("Base de datos inicializada correctamente")

        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_connection(self):
        """Obtiene una conexión a la base de datos."""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            return conn
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {e}")
            raise

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Ejecuta una consulta y retorna los resultados."""
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)

                if query.strip().upper().startswith('SELECT'):
                    results = [dict(row) for row in cursor.fetchall()]
                    return results
                else:
                    conn.commit()
                    return [{'affected_rows': cursor.rowcount}]

            except Exception as e:
                logger.error(f"Error ejecutando consulta: {e}")
                conn.rollback()
                raise
            finally:
                conn.close()


# Instancia global del gestor de base de datos
db_manager = DatabaseManager(config)

# --- Funciones Utilitarias ---


def validate_config():
    """Valida la configuración del sistema."""
    try:
        # Verificar directorios necesarios
        required_dirs = [
            Path(config.database.path).parent,
            Path(config.logging.file_path).parent,
            Path("data/generated_images"),
            Path("data/image_cache")
        ]

        for dir_path in required_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Verificar base de datos
        conn = db_manager.get_connection()
        conn.execute("SELECT 1")
        conn.close()

        logger.info("Configuración validada correctamente")
        return True

    except Exception as e:
        logger.error(f"Error validando configuración: {e}")
        return False


def get_system_status() -> Dict[str, Any]:
    """Obtiene el estado del sistema."""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Estadísticas básicas
        cursor.execute("SELECT COUNT(*) as total_articles FROM articles")
        total_articles = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) as recent_articles FROM articles WHERE created_at > datetime('now', '-24 hours')")
        recent_articles = cursor.fetchone()[0]

        conn.close()

        return {
            'status': 'operational',
            'total_articles': total_articles,
            'recent_articles': recent_articles,
            'database_path': config.database.path,
            'config_valid': True
        }

    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'config_valid': False
        }


# Validar configuración al importar
if __name__ != "__main__":
    validate_config()

if __name__ == "__main__":
    print("=== Sistema de Configuración de Inteligencia Geopolítica ===")
    print(f"Base de datos: {config.database.path}")
    print(f"Logs: {config.logging.file_path}")
    print(f"Puerto: {config.app.port}")

    status = get_system_status()
    print(f"Estado: {status}")

    if validate_config():
        print("✓ Configuración válida")
    else:
        print("✗ Error en configuración")
