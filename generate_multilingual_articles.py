#!/usr/bin/env python3
"""
Script para generar más artículos de prueba con datos realistas
en múltiples idiomas para el sistema de inteligencia geopolítica
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
import os
import sys

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def generate_multilingual_articles():
    """Genera artículos en múltiples idiomas para poblar la base de datos"""
    
    # Conectar a la base de datos
    db_path = os.path.join('data', 'geopolitical_intel.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Plantillas de artículos por idioma y región
    article_templates = {
        'en': [
            {
                'title': 'Escalating Tensions in South China Sea Prompt International Concern',
                'content': 'Military buildup in the South China Sea has reached unprecedented levels as territorial disputes intensify...',
                'country': 'China',
                'region': 'East Asia',
                'key_locations': 'South China Sea, Spratly Islands, Paracel Islands',
                'conflict_type': 'territorial_dispute',
                'risk_level': 'HIGH'
            },
            {
                'title': 'Border Clashes Between Armenia and Azerbaijan Resume',
                'content': 'Fresh hostilities have erupted along the Armenia-Azerbaijan border following...',
                'country': 'Armenia',
                'region': 'Caucasus',
                'key_locations': 'Nagorno-Karabakh, Syunik Province, Tavush',
                'conflict_type': 'military_conflict',
                'risk_level': 'CRITICAL'
            },
            {
                'title': 'Cyberattacks Target Critical Infrastructure in Eastern Europe',
                'content': 'A sophisticated cyberattack campaign has targeted power grids and financial systems...',
                'country': 'Ukraine',
                'region': 'Eastern Europe',
                'key_locations': 'Kiev, Kharkiv, Odesa',
                'conflict_type': 'cyber_warfare',
                'risk_level': 'HIGH'
            }
        ],
        'es': [
            {
                'title': 'Crisis Migratoria en la Frontera Sur Alcanza Niveles Críticos',
                'content': 'La situación en la frontera sur se deteriora mientras miles de migrantes...',
                'country': 'Mexico',
                'region': 'North America',
                'key_locations': 'Tijuana, Ciudad Juárez, Matamoros',
                'conflict_type': 'humanitarian_crisis',
                'risk_level': 'HIGH'
            },
            {
                'title': 'Protestas en Colombia Dejan Múltiples Víctimas en Bogotá',
                'content': 'Las manifestaciones contra las políticas gubernamentales han resultado en...',
                'country': 'Colombia',
                'region': 'South America',
                'key_locations': 'Bogotá, Medellín, Cali',
                'conflict_type': 'civil_unrest',
                'risk_level': 'MEDIUM'
            },
            {
                'title': 'Tensiones Comerciales Entre Argentina y Brasil Escalan',
                'content': 'Las disputas comerciales entre Argentina y Brasil han alcanzado un punto crítico...',
                'country': 'Argentina',
                'region': 'South America',
                'key_locations': 'Buenos Aires, São Paulo, Montevideo',
                'conflict_type': 'economic_dispute',
                'risk_level': 'MEDIUM'
            }
        ],
        'fr': [
            {
                'title': 'Instabilité Croissante au Sahel Menace la Sécurité Régionale',
                'content': 'La situation sécuritaire au Sahel continue de se détériorer avec...',
                'country': 'Mali',
                'region': 'West Africa',
                'key_locations': 'Bamako, Gao, Timbuktu',
                'conflict_type': 'terrorism',
                'risk_level': 'CRITICAL'
            },
            {
                'title': 'Tensions Diplomatiques Entre la France et l\'Algérie',
                'content': 'Les relations franco-algériennes atteignent un point bas suite à...',
                'country': 'Algeria',
                'region': 'North Africa',
                'key_locations': 'Alger, Oran, Constantine',
                'conflict_type': 'diplomatic_crisis',
                'risk_level': 'MEDIUM'
            }
        ],
        'de': [
            {
                'title': 'Energiekrise in Deutschland Verschärft Sich',
                'content': 'Die Energieversorgung Deutschlands steht vor beispiellosen Herausforderungen...',
                'country': 'Germany',
                'region': 'Western Europe',
                'key_locations': 'Berlin, Munich, Hamburg',
                'conflict_type': 'energy_crisis',
                'risk_level': 'HIGH'
            },
            {
                'title': 'Proteste in Österreich Gegen Neue Sicherheitsgesetze',
                'content': 'Tausende demonstrieren in Wien gegen die geplanten Änderungen...',
                'country': 'Austria',
                'region': 'Western Europe',
                'key_locations': 'Vienna, Salzburg, Innsbruck',
                'conflict_type': 'civil_unrest',
                'risk_level': 'LOW'
            }
        ],
        'ru': [
            {
                'title': 'Конфликт в Центральной Азии Обостряется',
                'content': 'Напряженность между соседними государствами достигла критического уровня...',
                'country': 'Kazakhstan',
                'region': 'Central Asia',
                'key_locations': 'Алматы, Нур-Султан, Шымкент',
                'conflict_type': 'territorial_dispute',
                'risk_level': 'HIGH'
            },
            {
                'title': 'Экономические Санкции Влияют на Региональную Стабильность',
                'content': 'Введенные санкции оказывают серьезное влияние на экономику региона...',
                'country': 'Russia',
                'region': 'Eastern Europe',
                'key_locations': 'Москва, Санкт-Петербург, Новосибирск',
                'conflict_type': 'economic_warfare',
                'risk_level': 'MEDIUM'
            }
        ],
        'ar': [
            {
                'title': 'التوترات في الشرق الأوسط تتصاعد',
                'content': 'تشهد منطقة الشرق الأوسط تصاعداً في التوترات الإقليمية...',
                'country': 'Syria',
                'region': 'Middle East',
                'key_locations': 'دمشق, حلب, حمص',
                'conflict_type': 'military_conflict',
                'risk_level': 'CRITICAL'
            },
            {
                'title': 'أزمة اللاجئين في لبنان تتفاقم',
                'content': 'تواجه لبنان أزمة إنسانية متصاعدة مع تدفق اللاجئين...',
                'country': 'Lebanon',
                'region': 'Middle East',
                'key_locations': 'بيروت, طرابلس, صيدا',
                'conflict_type': 'humanitarian_crisis',
                'risk_level': 'HIGH'
            }
        ],
        'zh': [
            {
                'title': '台海紧张局势持续升级',
                'content': '台湾海峡地区的紧张局势继续恶化，引发国际关注...',
                'country': 'Taiwan',
                'region': 'East Asia',
                'key_locations': '台北, 高雄, 台中',
                'conflict_type': 'territorial_dispute',
                'risk_level': 'CRITICAL'
            },
            {
                'title': '香港抗议活动影响地区稳定',
                'content': '持续的抗议活动对香港和周边地区的稳定产生重大影响...',
                'country': 'Hong Kong',
                'region': 'East Asia',
                'key_locations': '香港, 深圳, 广州',
                'conflict_type': 'civil_unrest',
                'risk_level': 'HIGH'
            }
        ]
    }
    
    # URLs y fuentes realistas
    sources = {
        'en': ['Reuters', 'Associated Press', 'BBC News', 'CNN International', 'Al Jazeera English'],
        'es': ['El País', 'La Nación', 'BBC Mundo', 'Univision', 'El Universal'],
        'fr': ['Le Monde', 'Le Figaro', 'France 24', 'RFI', 'Liberation'],
        'de': ['Deutsche Welle', 'Der Spiegel', 'Die Zeit', 'Süddeutsche Zeitung', 'FAZ'],
        'ru': ['RT', 'TASS', 'Sputnik', 'RIA Novosti', 'Kommersant'],
        'ar': ['Al Arabiya', 'Al Jazeera', 'Sky News Arabia', 'BBC Arabic', 'France 24 Arabic'],
        'zh': ['Xinhua', 'CGTN', 'South China Morning Post', 'China Daily', 'People\'s Daily']
    }
    
    articles_generated = 0
    
    # Generar variaciones de cada plantilla
    for language, templates in article_templates.items():
        source_list = sources[language]
        
        for template in templates:
            # Generar 8-12 variaciones de cada plantilla
            variations = random.randint(8, 12)
            
            for i in range(variations):
                # Crear variaciones del título y contenido
                title_vars = [
                    template['title'],
                    template['title'].replace('Escalating', 'Rising'),
                    template['title'].replace('Crisis', 'Emergency'),
                    template['title'].replace('Tensions', 'Conflicts'),
                    f"BREAKING: {template['title']}"
                ]
                
                content_base = template['content']
                content_extensions = [
                    " International observers express growing concern about regional stability.",
                    " Local authorities have called for immediate international intervention.",
                    " The situation continues to evolve rapidly with new developments expected.",
                    " Regional allies are monitoring the situation closely.",
                    " Economic implications are being felt across neighboring countries."
                ]
                
                # Generar datos del artículo
                title = random.choice(title_vars)
                content = content_base + random.choice(content_extensions)
                source = random.choice(source_list)
                
                # Fecha aleatoria en los últimos 30 días
                days_ago = random.randint(0, 30)
                published_at = datetime.now() - timedelta(days=days_ago)
                
                # Generar scores realistas
                risk_levels = {'LOW': 2, 'MEDIUM': 4, 'HIGH': 7, 'CRITICAL': 9}
                risk_score = risk_levels[template['risk_level']] + random.uniform(-1, 1)
                sentiment_score = random.uniform(-0.8, 0.3)  # Generalmente negativo para noticias
                
                sentiment_label = 'negative' if sentiment_score < -0.1 else 'neutral' if sentiment_score < 0.1 else 'positive'
                
                # Generar entidades JSON
                entities = {
                    "persons": [f"Official {i}", f"Leader {i}"] if random.random() > 0.5 else [],
                    "organizations": [f"Government {i}", "Military Command"] if random.random() > 0.6 else [],
                    "locations": template['key_locations'].split(', ')
                }
                
                # URL realista
                url = f"https://{source.lower().replace(' ', '').replace('ñ', 'n')}.com/article-{random.randint(10000, 99999)}"
                
                # Insertar en la base de datos
                cursor.execute("""
                    INSERT INTO articles (
                        title, content, url, source, published_at, language, country,
                        region, risk_level, conflict_type, sentiment_score, risk_score,
                        sentiment_label, entities_json, key_persons, key_locations,
                        conflict_indicators, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title, content, url, source, published_at.isoformat(),
                    language, template['country'], template['region'],
                    template['risk_level'], template['conflict_type'],
                    sentiment_score, risk_score, sentiment_label,
                    json.dumps(entities),
                    json.dumps(entities.get('persons', [])),
                    template['key_locations'],
                    json.dumps([template['conflict_type']]),
                    datetime.now().isoformat()
                ))
                
                articles_generated += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ Generated {articles_generated} new articles across {len(article_templates)} languages")
    print(f"📊 Articles per language: ~{articles_generated // len(article_templates)}")
    
    # Verificar totales
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language ORDER BY COUNT(*) DESC")
    by_lang = cursor.fetchall()
    
    print(f"📈 Total articles in database: {total}")
    print("🌍 Distribution by language:")
    for lang, count in by_lang:
        print(f"   {lang}: {count}")
    
    conn.close()

if __name__ == "__main__":
    generate_multilingual_articles()
