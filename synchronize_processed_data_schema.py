#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronización COMPLETA del esquema de processed_data
Este script asegura que el esquema de la tabla coincida exactamente 
con lo que el código NLP espera insertar.
"""

import sqlite3
import os
import sys
from pathlib import Path

def synchronize_processed_data_schema():
    """
    Sincroniza el esquema de processed_data con las expectativas del código NLP
    """
    
    db_path = './data/geopolitical_intel.db'
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    print("🔄 SINCRONIZANDO ESQUEMA DE processed_data CON CÓDIGO NLP...")
    print("=" * 75)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Verificar esquema actual
        cursor.execute("PRAGMA table_info(processed_data)")
        current_columns = {col[1]: col for col in cursor.fetchall()}
        
        print("📋 Esquema actual:")
        for name, col in current_columns.items():
            nullable = "NOT NULL" if col[3] else "NULL"
            print(f"   - {name} ({col[2]}) {nullable}")
        
        # 2. Definir el esquema correcto que espera el código NLP
        expected_schema = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'article_id': 'INTEGER',
            'title': 'TEXT NOT NULL',
            'processed_content': 'TEXT',
            'sentiment_score': 'REAL DEFAULT 0.0',
            'entities': 'TEXT',
            'keywords': 'TEXT',
            'risk_score': 'REAL DEFAULT 0.0',
            'classification': 'TEXT',
            'confidence_score': 'REAL DEFAULT 0.0',
            'processing_time': 'REAL',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'advanced_nlp': 'TEXT',
            'summary': 'TEXT',
            'original_language': 'TEXT',
            'avg_risk_score': 'REAL DEFAULT 0.0',
            # Columnas adicionales que pueden existir
            'content': 'TEXT',
            'url': 'TEXT',
            'source': 'TEXT',
            'published_date': 'TEXT',
            'processed_date': 'TEXT',
            'category': 'TEXT',
            'sentiment': 'REAL',
            'geolocation': 'TEXT',
            'language': 'TEXT',
            'raw_data': 'TEXT',
            'topics': 'TEXT',
            'model_version': 'TEXT'
        }
        
        print("\n📋 Esquema esperado por NLP:")
        for name, definition in expected_schema.items():
            print(f"   - {name} ({definition})")
        
        # 3. Verificar si la tabla tiene datos
        cursor.execute("SELECT COUNT(*) FROM processed_data")
        row_count = cursor.fetchone()[0]
        print(f"\n📊 Registros actuales en processed_data: {row_count}")
        
        # 4. Backup de datos si existen
        backup_needed = row_count > 0
        if backup_needed:
            print("💾 Creando backup de datos existentes...")
            cursor.execute("""
                CREATE TEMPORARY TABLE processed_data_backup AS 
                SELECT * FROM processed_data
            """)
        
        # 5. Recrear la tabla con el esquema correcto
        print("🔧 Recreando tabla con esquema correcto...")
        cursor.execute("DROP TABLE processed_data")
        
        # Crear la nueva tabla
        create_sql = """
            CREATE TABLE processed_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                title TEXT NOT NULL DEFAULT 'Sin título',
                processed_content TEXT,
                sentiment_score REAL DEFAULT 0.0,
                entities TEXT,
                keywords TEXT,
                risk_score REAL DEFAULT 0.0,
                classification TEXT,
                confidence_score REAL DEFAULT 0.0,
                processing_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                advanced_nlp TEXT,
                summary TEXT,
                original_language TEXT,
                avg_risk_score REAL DEFAULT 0.0,
                content TEXT,
                url TEXT,
                source TEXT,
                published_date TEXT,
                processed_date TEXT,
                category TEXT,
                sentiment REAL,
                geolocation TEXT,
                language TEXT,
                raw_data TEXT,
                topics TEXT,
                model_version TEXT,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        """
        
        cursor.execute(create_sql)
        print("   ✅ Nueva tabla creada con esquema completo")
        
        # 6. Restaurar datos si existían
        if backup_needed:
            print("🔄 Restaurando datos con validación...")
            
            # Obtener columnas del backup
            cursor.execute("PRAGMA table_info(processed_data_backup)")
            backup_columns = [col[1] for col in cursor.fetchall()]
            
            # Preparar columnas para INSERT
            insert_columns = []
            select_columns = []
            
            for col_name in ['id', 'article_id', 'title', 'processed_content', 'sentiment_score', 
                           'entities', 'keywords', 'risk_score', 'classification', 'confidence_score',
                           'processing_time', 'created_at', 'updated_at', 'advanced_nlp', 'summary',
                           'original_language', 'avg_risk_score', 'content', 'url', 'source',
                           'published_date', 'processed_date', 'category', 'sentiment', 'geolocation',
                           'language', 'raw_data', 'topics', 'model_version']:
                insert_columns.append(col_name)
                if col_name in backup_columns:
                    if col_name == 'title':
                        select_columns.append("COALESCE(NULLIF(title, ''), 'Sin título - ID:' || COALESCE(article_id, id))")
                    else:
                        select_columns.append(col_name)
                else:
                    if col_name == 'title':
                        select_columns.append("'Título recuperado - ID:' || COALESCE(article_id, id)")
                    elif col_name in ['sentiment_score', 'risk_score', 'confidence_score', 'avg_risk_score']:
                        select_columns.append("0.0")
                    else:
                        select_columns.append("NULL")
            
            restore_sql = f"""
                INSERT INTO processed_data ({', '.join(insert_columns)})
                SELECT {', '.join(select_columns)}
                FROM processed_data_backup
            """
            
            cursor.execute(restore_sql)
            restored_count = cursor.rowcount
            print(f"   ✅ Restaurados {restored_count} registros")
            
            cursor.execute("DROP TABLE processed_data_backup")
        
        # 7. Verificación final
        cursor.execute("PRAGMA table_info(processed_data)")
        final_columns = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) FROM processed_data")
        final_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_data WHERE title IS NULL OR title = ''")
        null_titles = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 75)
        print("✅ SINCRONIZACIÓN COMPLETADA")
        print(f"📊 Columnas finales: {len(final_columns)}")
        print(f"📊 Registros totales: {final_count}")
        print(f"📊 Títulos NULL: {null_titles}")
        
        print("\n📋 Esquema final:")
        for col in final_columns:
            nullable = "NOT NULL" if col[3] else "NULL"
            default = f" DEFAULT {col[4]}" if col[4] is not None else ""
            print(f"   {col[0]:2d}. {col[1]:20s} {col[2]:10s} {nullable:8s}{default}")
        
        print("\n🎉 ¡ESQUEMA SINCRONIZADO! El código NLP ahora puede insertar datos correctamente")
        return True
            
    except Exception as e:
        print(f"❌ Error durante sincronización: {e}")
        return False

if __name__ == "__main__":
    success = synchronize_processed_data_schema()
    sys.exit(0 if success else 1)