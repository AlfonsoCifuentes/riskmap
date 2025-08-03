"""
Configuración del ETL de Conflictos Geopolíticos
Variables de entorno y configuración central para el sistema ETL
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

# Configuración de rutas
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Configuración de base de datos
DEFAULT_DB_PATH = str(DATA_DIR / "geopolitical_intel.db")

# APIs y credenciales (desde variables de entorno)
ACLED_API_KEY = os.getenv('ACLED_API_KEY', '')
PLANET_API_KEY = os.getenv('PLANET_API_KEY', '')
GDELT_API_BASE = os.getenv('GDELT_API_BASE', "http://api.gdeltproject.org/api/v2")

# Configuración de ETL desde variables de entorno
ETL_ALERT_THRESHOLD = int(os.getenv('ETL_ALERT_THRESHOLD', '50'))
ETL_BATCH_SIZE = int(os.getenv('ETL_BATCH_SIZE', '100'))
ETL_MAX_RETRIES = int(os.getenv('ETL_MAX_RETRIES', '3'))
ETL_TIMEOUT_SECONDS = int(os.getenv('ETL_TIMEOUT_SECONDS', '30'))

# Configuración de fuentes de datos
DATA_SOURCES_CONFIG = {
    "acled": {
        "name": "ACLED - Armed Conflict Location & Event Data Project",
        "url": "https://api.acleddata.com/acled/read",
        "type": "api",
        "requires_key": True,
        "api_key_env": "ACLED_API_KEY",
        "rate_limit": "1000/hour",
        "documentation": "https://acleddata.com/resources/general-guides/",
        "fields": ["event_date", "country", "region", "latitude", "longitude", "event_type", "fatalities"],
        "confidence": 0.9
    },
    "gdelt": {
        "name": "GDELT - Global Database of Events, Language, and Tone",
        "url": "http://api.gdeltproject.org/api/v2/doc/doc",
        "type": "api",
        "requires_key": False,
        "rate_limit": "500/request",
        "documentation": "https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/",
        "fields": ["seendate", "url", "title", "tone", "domain"],
        "confidence": 0.6
    },
    "ucdp": {
        "name": "UCDP - Uppsala Conflict Data Program",
        "url": "https://ucdp.uu.se/downloads/ged/ged231-csv.zip",
        "type": "download",
        "requires_key": False,
        "documentation": "https://ucdp.uu.se/encyclopedia",
        "fields": ["date_start", "country", "region", "latitude", "longitude", "type_of_violence", "deaths_a"],
        "confidence": 0.95
    }
}

# Configuración de alertas
ALERT_CONFIG = {
    "thresholds": {
        "fatalities": {
            "low": 10,
            "medium": 25,
            "high": 50,
            "critical": 100
        },
        "severity_score": {
            "low": 0.3,
            "medium": 0.5,
            "high": 0.7,
            "critical": 0.9
        }
    },
    "notification_channels": ["database", "log"],  # Extensible a email, slack, etc.
    "critical_event_types": [
        "Violence against civilians",
        "Battles", 
        "Explosions/Remote violence",
        "Armed conflict"
    ]
}

# Configuración de regiones geopolíticas
REGIONS_CONFIG = {
    "middle_east": {
        "name": "Medio Oriente",
        "countries": ["Syria", "Iraq", "Iran", "Israel", "Palestine", "Lebanon", "Jordan", "Yemen", "Saudi Arabia"],
        "priority": "high"
    },
    "eastern_europe": {
        "name": "Europa del Este",
        "countries": ["Ukraine", "Russian Federation", "Belarus", "Moldova", "Georgia"],
        "priority": "high"
    },
    "sub_saharan_africa": {
        "name": "África Subsahariana",
        "countries": ["Nigeria", "Democratic Republic of Congo", "Somalia", "South Sudan", "Chad", "Mali"],
        "priority": "medium"
    },
    "south_asia": {
        "name": "Asia del Sur",
        "countries": ["Afghanistan", "Pakistan", "India", "Myanmar", "Bangladesh"],
        "priority": "medium"
    }
}

# Configuración de tipos de conflicto
CONFLICT_TYPES_CONFIG = {
    "interstate": {
        "name": "Conflicto Interestatal",
        "description": "Conflicto armado entre dos o más estados",
        "severity_multiplier": 1.5
    },
    "internal": {
        "name": "Conflicto Interno",
        "description": "Conflicto armado dentro de un estado",
        "severity_multiplier": 1.0
    },
    "non_state": {
        "name": "Conflicto No Estatal",
        "description": "Conflicto entre grupos no estatales",
        "severity_multiplier": 0.8
    },
    "one_sided": {
        "name": "Violencia Unilateral",
        "description": "Violencia contra civiles",
        "severity_multiplier": 1.3
    }
}

# Configuración de ETL por defecto
DEFAULT_ETL_CONFIG = {
    "sources": ["acled", "gdelt"],
    "date_range_days": 7,
    "regions": [],
    "conflict_types": [],
    "enable_alerts": True,
    "alert_threshold": ETL_ALERT_THRESHOLD,
    "batch_size": ETL_BATCH_SIZE,
    "max_retries": ETL_MAX_RETRIES,
    "timeout_seconds": ETL_TIMEOUT_SECONDS,
    "enable_geocoding": False,
    "enable_nlp_analysis": False
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": {
        "file": {
            "enabled": True,
            "path": str(LOGS_DIR / "etl_conflicts.log"),
            "max_bytes": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5
        },
        "console": {
            "enabled": True
        }
    }
}

# Configuración de dashboards y visualización
DASHBOARD_CONFIG = {
    "refresh_interval_seconds": 300,  # 5 minutos
    "max_events_display": 1000,
    "default_map_center": [20.0, 0.0],  # Centro mundial
    "default_map_zoom": 2,
    "chart_colors": {
        "critical": "#dc3545",
        "high": "#fd7e14", 
        "medium": "#ffc107",
        "low": "#28a745"
    },
    "heatmap_settings": {
        "radius": 10,
        "blur": 15,
        "max_zoom": 1.0
    }
}

# Configuración de la base de datos
DATABASE_CONFIG = {
    "connection_timeout": 30,
    "enable_wal_mode": True,
    "enable_foreign_keys": True,
    "backup_enabled": True,
    "backup_interval_hours": 24,
    "backup_retention_days": 30,
    "vacuum_interval_days": 7
}

# URLs y endpoints de datos específicos por conflicto
SPECIFIC_DATASETS = {
    "ukraine_russia": {
        "name": "Conflicto Rusia-Ucrania",
        "sources": [
            "https://www.kaggle.com/datasets/hskhawaja/russia-ukraine-conflict",
            "https://api.acleddata.com/acled/read?country=Ukraine&country=Russia"
        ],
        "keywords": ["Ukraine", "Russia", "Donetsk", "Luhansk", "Crimea", "Kiev"],
        "active": True,
        "priority": "critical"
    },
    "israel_palestine": {
        "name": "Conflicto Israel-Palestina",
        "sources": [
            "https://api.acleddata.com/acled/read?country=Israel&country=Palestine"
        ],
        "keywords": ["Israel", "Palestine", "Gaza", "West Bank", "Hamas", "IDF"],
        "active": True,
        "priority": "high"
    },
    "drc_m23": {
        "name": "Conflicto RDC - M23",
        "sources": [
            "https://api.acleddata.com/acled/read?country=Democratic Republic of Congo"
        ],
        "keywords": ["Congo", "M23", "Kivu", "Goma", "DRC"],
        "active": True,
        "priority": "high"
    },
    "afghanistan_taliban": {
        "name": "Situación Afganistán",
        "sources": [
            "https://api.acleddata.com/acled/read?country=Afghanistan"
        ],
        "keywords": ["Afghanistan", "Taliban", "Kabul", "ISIS-K"],
        "active": True,
        "priority": "medium"
    },
    "myanmar_crisis": {
        "name": "Crisis Myanmar",
        "sources": [
            "https://api.acleddata.com/acled/read?country=Myanmar"
        ],
        "keywords": ["Myanmar", "Rohingya", "Junta", "Yangon"],
        "active": True,
        "priority": "medium"
    }
}

# Configuración de calidad de datos
DATA_QUALITY_CONFIG = {
    "required_fields": ["event_date", "country", "event_type"],
    "coordinate_validation": {
        "enabled": True,
        "require_valid_coords": False,
        "geocoding_fallback": False
    },
    "date_validation": {
        "min_date": "2020-01-01",
        "future_date_tolerance_days": 1
    },
    "text_cleaning": {
        "remove_html": True,
        "normalize_whitespace": True,
        "max_length": 10000
    },
    "duplicate_detection": {
        "enabled": True,
        "similarity_threshold": 0.9,
        "fields_to_compare": ["event_date", "country", "latitude", "longitude"]
    }
}

def get_etl_config() -> Dict:
    """Obtener configuración completa del ETL"""
    return {
        "sources": DATA_SOURCES_CONFIG,
        "alerts": ALERT_CONFIG,
        "regions": REGIONS_CONFIG,
        "conflict_types": CONFLICT_TYPES_CONFIG,
        "defaults": DEFAULT_ETL_CONFIG,
        "logging": LOGGING_CONFIG,
        "dashboard": DASHBOARD_CONFIG,
        "database": DATABASE_CONFIG,
        "datasets": SPECIFIC_DATASETS,
        "data_quality": DATA_QUALITY_CONFIG,
        "paths": {
            "data_dir": str(DATA_DIR),
            "logs_dir": str(LOGS_DIR),
            "config_dir": str(CONFIG_DIR),
            "db_path": DEFAULT_DB_PATH
        }
    }

def get_api_credentials() -> Dict[str, str]:
    """Obtener credenciales de APIs"""
    return {
        "acled_api_key": ACLED_API_KEY,
        "planet_api_key": PLANET_API_KEY,
        "gdelt_api_base": GDELT_API_BASE
    }

def validate_configuration() -> List[str]:
    """Validar configuración y retornar warnings"""
    warnings = []
    
    # Verificar credenciales
    if not ACLED_API_KEY:
        warnings.append("ACLED_API_KEY no configurada - fuente ACLED deshabilitada")
    
    if not PLANET_API_KEY:
        warnings.append("PLANET_API_KEY no configurada - análisis satelital deshabilitado")
    
    # Verificar directorios
    if not DATA_DIR.exists():
        warnings.append(f"Directorio de datos no existe: {DATA_DIR}")
    
    if not LOGS_DIR.exists():
        warnings.append(f"Directorio de logs no existe: {LOGS_DIR}")
    
    return warnings

if __name__ == "__main__":
    # Test de configuración
    config = get_etl_config()
    print("✅ Configuración ETL cargada correctamente")
    print(f"📁 Directorio de datos: {config['paths']['data_dir']}")
    print(f"💾 Base de datos: {config['paths']['db_path']}")
    print(f"🔍 Fuentes configuradas: {list(config['sources'].keys())}")
    
    warnings = validate_configuration()
    if warnings:
        print("\n⚠️ Advertencias de configuración:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n✅ Configuración válida - sin advertencias")
