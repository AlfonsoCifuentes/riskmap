"""
Configuración avanzada para el Sistema de Inteligencia Geopolítica
Incluye configuración para todas las fuentes de datos especializadas
"""

import os
from pathlib import Path

# APIs y fuentes de datos especializadas
SPECIALIZED_DATA_SOURCES = {
    
    # === ENERGÍA Y PETRÓLEO ===
    'energy': {
        'eia': {
            'enabled': True,
            'api_key': os.getenv('EIA_API_KEY', ''),
            'base_url': 'https://api.eia.gov/v2',
            'endpoints': {
                'petroleum': '/petroleum/pri/spt/data/',
                'natural_gas': '/natural-gas/pri/sum/data/',
                'electricity': '/electricity/rto/region-data/data/',
                'coal': '/coal/data/'
            },
            'rate_limit': 5000  # requests per hour
        },
        'worldbank': {
            'enabled': True,
            'base_url': 'https://api.worldbank.org/v2',
            'indicators': [
                'EG.USE.PCAP.KG.OE',  # Energy use per capita
                'EG.ELC.ACCS.ZS',     # Access to electricity
                'EG.USE.COMM.FO.ZS',  # Fossil fuel energy consumption
                'EG.FEC.RNEW.ZS',     # Renewable energy consumption
                'EG.IMP.CONS.ZS',     # Energy imports, net
                'EG.USE.ELEC.KH.PC'   # Electric power consumption per capita
            ]
        },
        'huggingface_datasets': [
            'itsarnf/thorium_nuclear_energy_qa_squad',
            'DSCI511G1/COP26_Energy_Transition_Tweets',
            'cmudrc/wave-energy',
            'nenils/time_series_energy'
        ]
    },
    
    # === DATOS MILITARES ===
    'military': {
        'sipri': {
            'enabled': True,
            'base_url': 'https://www.sipri.org/databases',
            'datasets': ['military-expenditure', 'arms-transfers', 'nuclear-forces'],
            'scraping_required': True
        },
        'globalfirepower': {
            'enabled': True,
            'base_url': 'https://www.globalfirepower.com',
            'scraping_required': True,
            'data_types': ['rankings', 'military_strength', 'defense_budget']
        },
        'huggingface_datasets': [
            'mehul7/captioned_military_aircraft',
            'Illia56/Military-Aircraft-Detection',
            'Falah/military_machinery_prompts',
            'Falah/real_military_machinery_prompts',
            'Falah/Military_ships_prompts'
        ],
        'worldbank_military': [
            'MS.MIL.XPND.GD.ZS',  # Military expenditure (% of GDP)
            'MS.MIL.XPND.CD',     # Military expenditure (current USD)
            'MS.MIL.TOTL.P1',     # Armed forces personnel, total
            'MS.MIL.XPND.ZS'      # Military expenditure (% of central government expenditure)
        ]
    },
    
    # === COMERCIO INTERNACIONAL ===
    'trade': {
        'worldbank': {
            'enabled': True,
            'indicators': [
                'NE.EXP.GNFS.ZS',     # Exports of goods and services (% of GDP)
                'NE.IMP.GNFS.ZS',     # Imports of goods and services (% of GDP)
                'TG.VAL.TOTL.GD.ZS',  # Trade (% of GDP)
                'TX.VAL.TECH.CD',     # High-technology exports (current USD)
                'BG.GSR.NFSV.GD.ZS',  # Trade in services (% of GDP)
                'TM.TAX.MRCH.WM.AR.ZS' # Tariff rate, applied, weighted mean, all products
            ]
        },
        'wto': {
            'enabled': False,  # Limited API access
            'base_url': 'https://api.wto.org',
            'endpoints': ['trade_statistics', 'tariff_data']
        },
        'imf': {
            'enabled': False,  # Requires special access
            'datasets': ['direction_of_trade', 'balance_of_payments']
        },
        'oecd': {
            'enabled': True,
            'base_url': 'https://stats.oecd.org/restsdmx/sdmx.ashx',
            'datasets': ['TRADE_GOODS', 'TRADE_SERVICES']
        }
    },
    
    # === CONFLICTOS HISTÓRICOS ===
    'historical_conflicts': {
        'ucdp': {
            'enabled': True,
            'base_url': 'https://ucdp.uu.se/downloads/',
            'datasets': [
                'ucdp-prio-acd-231.csv',      # Armed Conflict Dataset
                'ucdp-brd-dyadic-231.csv',    # Battle-Related Deaths Dataset
                'ucdp-onesided-231.csv',      # One-sided Violence Dataset
                'ucdp-nonstate-231.csv'       # Non-state Conflict Dataset
            ]
        },
        'cow': {
            'enabled': True,
            'base_url': 'https://correlatesofwar.org/data-sets/',
            'datasets': [
                'inter-state-wars',
                'intra-state-wars', 
                'militarized-interstate-disputes',
                'national-material-capabilities'
            ]
        },
        'huggingface_datasets': [
            'hugginglearners/russia-ukraine-conflict-articles',
            'jorge-henao/historias_conflicto_colombia',
            'anytp/conflicto',
            'osunlp/ConflictQA'
        ],
        'acled': {
            'enabled': True,
            'base_url': 'https://api.acleddata.com/acled/read/',
            'api_key': os.getenv('ACLED_API_KEY', ''),
            'requires_registration': True
        }
    },
    
    # === INFRAESTRUCTURA E INTERNET ===
    'infrastructure': {
        'worldbank_infrastructure': [
            'IT.NET.USER.ZS',      # Individuals using the Internet (% of population)
            'IT.NET.BBND.P2',      # Fixed broadband subscriptions (per 100 people)
            'IT.CEL.SETS.P2',      # Mobile cellular subscriptions (per 100 people)
            'IT.MLT.MAIN.P2',      # Fixed telephone subscriptions (per 100 people)
            'IS.ROD.PAVE.ZS',      # Roads, paved (% of total roads)
            'IS.AIR.PSGR'          # Air transport, passengers carried
        ],
        'submarine_cables': {
            'enabled': True,
            'source': 'https://www.submarinecablemap.com/api/',
            'description': 'Submarine internet cable infrastructure'
        },
        'internet_exchange_points': {
            'enabled': True,
            'source': 'https://www.pch.net/ixp/dir',
            'description': 'Internet Exchange Points worldwide'
        }
    }
}

# === MODELOS DE IA ESPECIALIZADOS ===
AI_MODELS = {
    
    # Análisis de imágenes
    'image_analysis': {
        'primary': 'google/vit-base-patch16-224',
        'alternatives': [
            'microsoft/resnet-50',
            'facebook/deit-tiny-patch16-224'
        ],
        'nsfw_detection': 'Falconsai/nsfw_image_detection',
        'object_detection': 'facebook/detr-resnet-50'
    },
    
    # Geolocalización
    'geolocation': {
        'primary': 'geolocal/StreetCLIP',
        'alternatives': [
            'jrheiner/thesis-clip-geoloc-country',
            'jrheiner/thesis-clip-geoloc-continent'
        ]
    },
    
    # Análisis de texto geopolítico
    'geopolitical_text': {
        'classification': 'MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli',
        'ner': 'numind/NuNER-v2.0',
        'sentiment': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
        'conflict_detection': 'microsoft/DialoGPT-medium'
    },
    
    # Análisis multilingüe
    'multilingual': {
        'translation': 'Helsinki-NLP/opus-mt-mul-en',
        'language_detection': 'papluca/xlm-roberta-base-language-detection',
        'cross_lingual_ner': 'Davlan/distilbert-base-multilingual-cased-ner-hrl'
    }
}

# === CONFIGURACIÓN DE VALIDACIÓN DE IMÁGENES ===
IMAGE_VALIDATION = {
    'enabled': True,
    'models': {
        'content_validation': 'google/vit-base-patch16-224',
        'nsfw_detection': 'Falconsai/nsfw_image_detection',
        'fake_detection': 'dima806/deepfake_vs_real_image_detection'
    },
    'thresholds': {
        'content_confidence': 0.7,
        'nsfw_threshold': 0.5,
        'fake_threshold': 0.6
    },
    'allowed_formats': ['jpg', 'jpeg', 'png', 'webp'],
    'max_size_mb': 10,
    'timeout_seconds': 30
}

# === CONFIGURACIÓN DE ANÁLISIS GEOGRÁFICO ===
GEOGRAPHIC_ANALYSIS = {
    'enabled': True,
    'distinguish_source_content': True,
    'models': {
        'ner': 'numind/NuNER-v2.0',
        'classification': 'MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli'
    },
    'conflict_labels': [
        'military conflict', 'political crisis', 'economic disruption',
        'natural disaster', 'social unrest', 'diplomatic tension',
        'territorial dispute', 'cyber attack', 'terrorism',
        'ethnic conflict', 'religious conflict', 'resource conflict'
    ],
    'intensity_labels': [
        'low intensity', 'medium intensity', 'high intensity', 'critical severity'
    ],
    'actor_labels': [
        'state actors', 'non-state actors', 'international organizations', 
        'militia groups', 'terrorist organizations', 'peacekeeping forces'
    ],
    'confidence_threshold': 0.6
}

# === FUENTES RSS ESPECIALIZADAS ADICIONALES ===
SPECIALIZED_RSS_SOURCES = {
    'energy_news': [
        'https://www.energy.gov/rss.xml',
        'https://www.eia.gov/rss/petroleum.xml',
        'https://www.iea.org/rss',
        'https://oilprice.com/rss/main',
        'https://www.powermag.com/feed/',
        'https://www.windpowerengineering.com/feed/'
    ],
    'military_defense': [
        'https://www.defensenews.com/arc/outboundfeeds/rss/',
        'https://www.janes.com/feeds/news.xml',
        'https://breakingdefense.com/feed/',
        'https://www.military.com/rss/news.xml',
        'https://www.defenseone.com/rss/all/',
        'https://www.c4isrnet.com/rss/'
    ],
    'trade_economics': [
        'https://www.wto.org/english/news_e/rss_e/rss_news_e.xml',
        'https://www.imf.org/external/rss/news.xml',
        'https://www.worldbank.org/en/news/all.xml',
        'https://www.oecd.org/newsroom/rss.xml',
        'https://www.trade.gov/rss/trade-news.xml'
    ],
    'conflict_security': [
        'https://www.crisisgroup.org/rss.xml',
        'https://www.acleddata.com/feed/',
        'https://www.sipri.org/rss.xml',
        'https://www.securitycouncilreport.org/rss_feeds/un_documents.xml',
        'https://reliefweb.int/rss.xml'
    ]
}

# === CONFIGURACIÓN DE BASE DE DATOS ESPECIALIZADA ===
DATABASE_CONFIG = {
    'specialized_tables': {
        'energy_data': {
            'columns': [
                'id', 'source', 'data_type', 'country', 'region',
                'date', 'value', 'unit', 'indicator_code', 'created_at'
            ],
            'indexes': ['country', 'date', 'data_type']
        },
        'military_data': {
            'columns': [
                'id', 'source', 'country', 'metric_type', 'value', 
                'year', 'ranking', 'currency', 'created_at'
            ],
            'indexes': ['country', 'year', 'metric_type']
        },
        'trade_data': {
            'columns': [
                'id', 'source', 'country', 'trade_type', 'partner_country',
                'value', 'currency', 'year', 'commodity_code', 'created_at'
            ],
            'indexes': ['country', 'year', 'trade_type']
        },
        'historical_conflicts': {
            'columns': [
                'id', 'source', 'conflict_id', 'conflict_name', 'start_date',
                'end_date', 'countries_involved', 'conflict_type', 'intensity',
                'casualties', 'outcome', 'latitude', 'longitude', 'created_at'
            ],
            'indexes': ['start_date', 'conflict_type', 'countries_involved']
        },
        'infrastructure_data': {
            'columns': [
                'id', 'source', 'country', 'infrastructure_type', 'metric',
                'value', 'year', 'coverage_area', 'created_at'
            ],
            'indexes': ['country', 'year', 'infrastructure_type']
        }
    }
}

# === CONFIGURACIÓN DE PROCESAMIENTO ===
PROCESSING_CONFIG = {
    'batch_size': 100,
    'max_workers': 4,
    'timeout_per_request': 30,
    'retry_attempts': 3,
    'delay_between_requests': 1,  # seconds
    'enable_caching': True,
    'cache_duration_hours': 24,
    'enable_background_processing': True,
    'priority_countries': [
        'United States', 'China', 'Russia', 'United Kingdom', 'France',
        'Germany', 'India', 'Japan', 'Brazil', 'Turkey', 'Iran', 'Israel',
        'Ukraine', 'Syria', 'Afghanistan', 'Iraq', 'North Korea', 'South Korea'
    ]
}

# === CONFIGURACIÓN DE CALIDAD DE DATOS ===
DATA_QUALITY = {
    'validation_enabled': True,
    'min_article_length': 100,
    'max_article_age_days': 30,
    'required_fields': ['title', 'content', 'url', 'published_at'],
    'duplicate_detection': True,
    'language_validation': True,
    'content_quality_threshold': 0.6,
    'image_validation_required': True,
    'geographic_validation_required': True
}

# === CONFIGURACIÓN DE MONITOREO ===
MONITORING = {
    'enabled': True,
    'metrics_collection': True,
    'performance_tracking': True,
    'error_reporting': True,
    'health_checks_interval_minutes': 15,
    'log_rotation_days': 30,
    'alert_thresholds': {
        'error_rate_percent': 10,
        'processing_delay_minutes': 60,
        'memory_usage_percent': 85,
        'disk_usage_percent': 90
    }
}

# Función para obtener configuración
def get_config():
    """Retorna la configuración completa"""
    return {
        'specialized_sources': SPECIALIZED_DATA_SOURCES,
        'ai_models': AI_MODELS,
        'image_validation': IMAGE_VALIDATION,
        'geographic_analysis': GEOGRAPHIC_ANALYSIS,
        'rss_sources': SPECIALIZED_RSS_SOURCES,
        'database': DATABASE_CONFIG,
        'processing': PROCESSING_CONFIG,
        'data_quality': DATA_QUALITY,
        'monitoring': MONITORING
    }

# Función para validar configuración
def validate_config():
    """Valida que la configuración sea correcta"""
    errors = []
    
    # Verificar APIs keys si están habilitadas
    if SPECIALIZED_DATA_SOURCES['energy']['eia']['enabled']:
        if not os.getenv('EIA_API_KEY'):
            errors.append("EIA_API_KEY no configurada")
    
    if SPECIALIZED_DATA_SOURCES['historical_conflicts']['acled']['enabled']:
        if not os.getenv('ACLED_API_KEY'):
            errors.append("ACLED_API_KEY no configurada")
    
    return errors
