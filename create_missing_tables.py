"""
Script para crear tablas faltantes en la base de datos para el sistema de ingesta RSS
"""

import sqlite3
import json
from datetime import datetime

def create_missing_tables():
    """Crear las tablas que faltan para el sistema de ingesta"""
    
    db_path = 'data/geopolitical_intel.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📋 Creando tablas faltantes para sistema de ingesta...")
    
    # 1. Tabla 'sources' para fuentes RSS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            language TEXT DEFAULT 'en',
            region TEXT,
            priority INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_fetched TIMESTAMP,
            total_articles INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            metadata TEXT  -- JSON for additional info
        )
    ''')
    print("✅ Tabla 'sources' creada")
    
    # 2. Tabla 'processed_data' para tracking de procesamiento
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            processing_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            result TEXT,  -- JSON result
            error_message TEXT,
            FOREIGN KEY (article_id) REFERENCES unified_articles(id)
        )
    ''')
    print("✅ Tabla 'processed_data' creada")
    
    # 3. Insertar fuentes RSS por defecto
    default_sources = [
        ('BBC World', 'https://feeds.bbci.co.uk/news/world/rss.xml', 'en', 'Global', 1),
        ('CNN World', 'https://rss.cnn.com/rss/edition.rss', 'en', 'Global', 1),
        ('Reuters World', 'https://feeds.reuters.com/reuters/worldNews', 'en', 'Global', 1),
        ('Al Jazeera', 'https://www.aljazeera.com/xml/rss/all.xml', 'en', 'Middle East', 2),
        ('DW News', 'https://rss.dw.com/xml/rss-en-all', 'en', 'Europe', 2),
        ('France24 International', 'https://www.france24.com/en/rss', 'en', 'Europe', 2)
    ]
    
    # Verificar si ya existen fuentes
    cursor.execute("SELECT COUNT(*) FROM sources")
    existing_count = cursor.fetchone()[0]
    
    if existing_count == 0:
        print("📰 Insertando fuentes RSS por defecto...")
        cursor.executemany('''
            INSERT INTO sources (name, url, language, region, priority) 
            VALUES (?, ?, ?, ?, ?)
        ''', default_sources)
        print(f"✅ {len(default_sources)} fuentes RSS insertadas")
    else:
        print(f"ℹ️  Ya existen {existing_count} fuentes en la base de datos")
    
    # 4. Verificar que unified_articles tiene las columnas necesarias
    cursor.execute("PRAGMA table_info(unified_articles)")
    columns = [col[1] for col in cursor.fetchall()]
    
    required_columns = [
        'geopolitical_relevance', 'published_at', 'enrichment_status', 
        'processing_confidence', 'ai_importance', 'language'
    ]
    
    missing_columns = [col for col in required_columns if col not in columns]
    
    if missing_columns:
        print(f"⚠️  Columnas faltantes en unified_articles: {missing_columns}")
        # Añadir columnas faltantes
        for col in missing_columns:
            if col == 'geopolitical_relevance':
                cursor.execute("ALTER TABLE unified_articles ADD COLUMN geopolitical_relevance INTEGER DEFAULT 0")
            elif col == 'published_at':
                cursor.execute("ALTER TABLE unified_articles ADD COLUMN published_at DATETIME")
            elif col == 'enrichment_status':
                cursor.execute("ALTER TABLE unified_articles ADD COLUMN enrichment_status TEXT")
            elif col == 'processing_confidence':
                cursor.execute("ALTER TABLE unified_articles ADD COLUMN processing_confidence REAL")
            elif col == 'ai_importance':
                cursor.execute("ALTER TABLE unified_articles ADD COLUMN ai_importance REAL")
            elif col == 'language':
                cursor.execute("ALTER TABLE unified_articles ADD COLUMN language TEXT DEFAULT 'es'")
            print(f"✅ Columna '{col}' añadida a unified_articles")
    else:
        print("✅ unified_articles tiene todas las columnas necesarias")
    
    conn.commit()
    conn.close()
    
    print("🎉 Tablas creadas exitosamente!")
    return True

if __name__ == "__main__":
    create_missing_tables()