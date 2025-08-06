#!/usr/bin/env python3
"""
Preparar base de datos para el enriquecimiento con Ollama
"""

import sqlite3
from pathlib import Path

def prepare_database():
    """Asegurar que la base de datos tiene todas las columnas necesarias"""
    
    db_path = Path('data/geopolitical_intel.db')
    if not db_path.exists():
        print('❌ Database not found')
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Verificar columnas existentes
    cursor.execute('PRAGMA table_info(articles)')
    existing_columns = {col[1] for col in cursor.fetchall()}
    
    # Columnas necesarias para el enriquecimiento
    required_columns = {
        'key_persons': 'TEXT',
        'key_locations': 'TEXT', 
        'extracted_entities_json': 'TEXT',
        'summary': 'TEXT',
        'geopolitical_relevance': 'INTEGER',
        'groq_enhanced': 'INTEGER DEFAULT 0',
        'last_enrichment': 'TEXT'
    }
    
    # Agregar columnas faltantes
    added_columns = []
    for column, column_type in required_columns.items():
        if column not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE articles ADD COLUMN {column} {column_type}')
                added_columns.append(column)
                print(f'✅ Agregada columna: {column}')
            except sqlite3.Error as e:
                print(f'❌ Error agregando {column}: {e}')
    
    if added_columns:
        print(f'📊 Se agregaron {len(added_columns)} columnas nuevas')
    else:
        print('✅ Todas las columnas ya existen')
    
    conn.commit()
    conn.close()
    return True

if __name__ == '__main__':
    prepare_database()
