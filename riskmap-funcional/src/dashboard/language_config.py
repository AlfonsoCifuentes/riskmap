#!/usr/bin/env python3
"""
Language Configuration for Dashboard
"""

import json
from pathlib import Path

# Language configurations
LANGUAGES = {
    'es': {
        'name': 'Español',
        'code': 'es',
        'flag': '🇪🇸',
        'translations': {
            'dashboard_title': 'Inteligencia Geopolítica',
            'latest_articles': 'Últimos Artículos',
            'high_risk_articles': 'Artículos de Alto Riesgo',
            'featured_article': 'Artículo Destacado',
            'weekly_analysis': 'Análisis Semanal',
            'risk_level': 'Nivel de Riesgo',
            'high': 'Alto',
            'medium': 'Medio',
            'low': 'Bajo',
            'read_full_article': 'Leer Artículo Completo',
            'source': 'Fuente',
            'date': 'Fecha',
            'location': 'Ubicación',
            'category': 'Categoría',
            'total_articles': 'Total de Artículos',
            'high_risk_events': 'Eventos de Alto Riesgo',
            'processed_today': 'Procesados Hoy',
            'active_regions': 'Regiones Activas'
        }
    },
    'en': {
        'name': 'English',
        'code': 'en',
        'flag': '🇺🇸',
        'translations': {
            'dashboard_title': 'Geopolitical Intelligence',
            'latest_articles': 'Latest Articles',
            'high_risk_articles': 'High Risk Articles',
            'featured_article': 'Featured Article',
            'weekly_analysis': 'Weekly Analysis',
            'risk_level': 'Risk Level',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
            'read_full_article': 'Read Full Article',
            'source': 'Source',
            'date': 'Date',
            'location': 'Location',
            'category': 'Category',
            'total_articles': 'Total Articles',
            'high_risk_events': 'High Risk Events',
            'processed_today': 'Processed Today',
            'active_regions': 'Active Regions'
        }
    },
    'fr': {
        'name': 'Français',
        'code': 'fr',
        'flag': '🇫🇷',
        'translations': {
            'dashboard_title': 'Intelligence Géopolitique',
            'latest_articles': 'Derniers Articles',
            'high_risk_articles': 'Articles à Haut Risque',
            'featured_article': 'Article en Vedette',
            'weekly_analysis': 'Analyse Hebdomadaire',
            'risk_level': 'Niveau de Risque',
            'high': 'Élevé',
            'medium': 'Moyen',
            'low': 'Faible',
            'read_full_article': 'Lire l\'Article Complet',
            'source': 'Source',
            'date': 'Date',
            'location': 'Emplacement',
            'category': 'Catégorie',
            'total_articles': 'Total des Articles',
            'high_risk_events': 'Événements à Haut Risque',
            'processed_today': 'Traités Aujourd\'hui',
            'active_regions': 'Régions Actives'
        }
    },
    'de': {
        'name': 'Deutsch',
        'code': 'de',
        'flag': '🇩🇪',
        'translations': {
            'dashboard_title': 'Geopolitische Intelligenz',
            'latest_articles': 'Neueste Artikel',
            'high_risk_articles': 'Hochrisiko-Artikel',
            'featured_article': 'Hauptartikel',
            'weekly_analysis': 'Wöchentliche Analyse',
            'risk_level': 'Risikoniveau',
            'high': 'Hoch',
            'medium': 'Mittel',
            'low': 'Niedrig',
            'read_full_article': 'Vollständigen Artikel Lesen',
            'source': 'Quelle',
            'date': 'Datum',
            'location': 'Standort',
            'category': 'Kategorie',
            'total_articles': 'Artikel Gesamt',
            'high_risk_events': 'Hochrisiko-Ereignisse',
            'processed_today': 'Heute Verarbeitet',
            'active_regions': 'Aktive Regionen'
        }
    },
    'pt': {
        'name': 'Português',
        'code': 'pt',
        'flag': '🇧🇷',
        'translations': {
            'dashboard_title': 'Inteligência Geopolítica',
            'latest_articles': 'Últimos Artigos',
            'high_risk_articles': 'Artigos de Alto Risco',
            'featured_article': 'Artigo em Destaque',
            'weekly_analysis': 'Análise Semanal',
            'risk_level': 'Nível de Risco',
            'high': 'Alto',
            'medium': 'Médio',
            'low': 'Baixo',
            'read_full_article': 'Ler Artigo Completo',
            'source': 'Fonte',
            'date': 'Data',
            'location': 'Localização',
            'category': 'Categoria',
            'total_articles': 'Total de Artigos',
            'high_risk_events': 'Eventos de Alto Risco',
            'processed_today': 'Processados Hoje',
            'active_regions': 'Regiões Ativas'
        }
    }
}

def get_language_config(lang_code: str = 'es') -> dict:
    """Get language configuration."""
    return LANGUAGES.get(lang_code, LANGUAGES['es'])

def get_available_languages() -> list:
    """Get list of available languages."""
    return [
        {
            'code': code,
            'name': config['name'],
            'flag': config['flag']
        }
        for code, config in LANGUAGES.items()
    ]

def save_language_config():
    """Save language configurations to JSON files."""
    config_dir = Path(__file__).parent / 'i18n'
    config_dir.mkdir(exist_ok=True)
    
    for lang_code, config in LANGUAGES.items():
        file_path = config_dir / f'{lang_code}.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config['translations'], f, ensure_ascii=False, indent=2)
    
    # Save language list
    lang_list_path = config_dir / 'languages.json'
    with open(lang_list_path, 'w', encoding='utf-8') as f:
        json.dump(get_available_languages(), f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    save_language_config()
    print("✅ Language configurations saved!")