#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrección URGENTE: Error de restricción NOT NULL en processed_data.title
Este script soluciona el problema detectado donde la tabla processed_data 
requiere una columna title NOT NULL pero se intenta insertar valores NULL.
"""

import sqlite3
import os
import sys
from pathlib import Path

def fix_processed_data_title_constraint():
    """
    Soluciona el problema de NOT NULL constraint failed: processed_data.title
    """
    
    db_path = './data/geopolitical_intel.db'
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    print("🔍 CORRIGIENDO RESTRICCIÓN NOT NULL EN processed_data.title...")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Verificar esquema actual de processed_data
        cursor.execute("PRAGMA table_info(processed_data)")
        columns = cursor.fetchall()
        
        print("📋 Esquema actual de processed_data:")
        for col in columns:
            nullable = "NOT NULL" if col[3] else "NULL"
            print(f"   - {col[1]} ({col[2]}) {nullable}")
        
        # 2. Verificar si hay registros con title NULL
        cursor.execute("SELECT COUNT(*) FROM processed_data WHERE title IS NULL OR title = ''")
        null_count = cursor.fetchone()[0]
        print(f"\n📊 Registros con title NULL/vacío: {null_count}")
        
        # 3. Verificar registros en articles que no tienen correspondencia
        cursor.execute("""
            SELECT COUNT(*) 
            FROM articles a 
            LEFT JOIN processed_data p ON a.id = p.article_id 
            WHERE p.article_id IS NULL
        """)
        missing_processed = cursor.fetchone()[0]
        print(f"📊 Artículos sin procesamiento NLP: {missing_processed}")
        
        # 4. Actualizar registros con title NULL usando datos de articles
        print("\n🔧 APLICANDO CORRECCIONES...")
        
        # Actualizar processed_data records que tienen title NULL
        cursor.execute("""
            UPDATE processed_data 
            SET title = (
                SELECT COALESCE(articles.title, 'Sin título - ID:' || articles.id)
                FROM articles 
                WHERE articles.id = processed_data.article_id
            )
            WHERE (title IS NULL OR title = '') 
            AND article_id IS NOT NULL
        """)
        updated_rows = cursor.rowcount
        print(f"   ✅ Actualizados {updated_rows} registros con título desde articles")
        
        # Actualizar registros huérfanos con título genérico
        cursor.execute("""
            UPDATE processed_data 
            SET title = 'Sin título disponible - Registro:' || id
            WHERE title IS NULL OR title = ''
        """)
        orphan_updated = cursor.rowcount
        print(f"   ✅ Actualizados {orphan_updated} registros huérfanos con título genérico")
        
        # 5. Verificar que title sea obligatorio - recrear tabla si es necesario
        cursor.execute("PRAGMA table_info(processed_data)")
        columns = cursor.fetchall()
        title_column = None
        for col in columns:
            if col[1] == 'title':
                title_column = col
                break
        
        if title_column and not title_column[3]:  # Si title no es NOT NULL
            print("\n🔧 Recreando tabla processed_data con title como NOT NULL...")
            
            # Backup de datos
            cursor.execute("""
                CREATE TEMPORARY TABLE processed_data_backup AS 
                SELECT * FROM processed_data
            """)
            
            # Recrear tabla con title NOT NULL
            cursor.execute("DROP TABLE processed_data")
            
            cursor.execute("""
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
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # Restaurar datos asegurando que title no sea NULL
            cursor.execute("""
                INSERT INTO processed_data 
                SELECT 
                    id, article_id, 
                    COALESCE(NULLIF(title, ''), 'Sin título - ID:' || COALESCE(article_id, id)),
                    processed_content, sentiment_score, entities, keywords,
                    risk_score, classification, confidence_score, processing_time,
                    created_at, updated_at, advanced_nlp, summary, original_language,
                    avg_risk_score
                FROM processed_data_backup
            """)
            
            cursor.execute("DROP TABLE processed_data_backup")
            print("   ✅ Tabla processed_data recreada con restricción NOT NULL en title")
        
        # 6. Verificación final
        cursor.execute("SELECT COUNT(*) FROM processed_data WHERE title IS NULL OR title = ''")
        final_null_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_data")
        total_count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ CORRECCIÓN COMPLETADA")
        print(f"📊 Total de registros: {total_count}")
        print(f"📊 Registros con title NULL después: {final_null_count}")
        
        if final_null_count == 0:
            print("🎉 ¡PROBLEMA SOLUCIONADO! Ya no hay valores NULL en title")
            return True
        else:
            print("⚠️ Aún quedan algunos registros con title NULL")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_processed_data_title_constraint()
    sys.exit(0 if success else 1)