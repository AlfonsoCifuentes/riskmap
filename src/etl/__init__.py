"""
ETL System for Geopolitical Conflicts
Módulo de ETL para ingesta y procesamiento de datos de conflictos geopolíticos

Este módulo proporciona:
- Extracción de datos de múltiples fuentes (ACLED, GDELT, UCDP)
- Transformación y normalización de datos
- Carga en base de datos SQLite
- Detección de eventos críticos
- Sistema de alertas automáticas
- Integración con Flask
"""

from .config import get_etl_config, get_api_credentials, validate_configuration
from .flask_controller import ETLController, create_etl_routes, get_etl_controller

try:
    from .conflict_data_etl import ConflictDataETL, ETLConfig, create_etl_instance
    ETL_CORE_AVAILABLE = True
except ImportError:
    ETL_CORE_AVAILABLE = False
    ConflictDataETL = None
    ETLConfig = None
    create_etl_instance = None

__version__ = "1.0.0"
__author__ = "RiskMap Team"

__all__ = [
    'get_etl_config',
    'get_api_credentials', 
    'validate_configuration',
    'ETLController',
    'create_etl_routes',
    'get_etl_controller',
    'ConflictDataETL',
    'ETLConfig',
    'create_etl_instance',
    'ETL_CORE_AVAILABLE'
]
