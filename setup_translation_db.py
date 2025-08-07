#!/usr/bin/env python3
"""
Script para agregar columnas de traducción a la base de datos
"""

import sqlite3
import os

def add_translation_columns():
    """Agregar columnas necesarias para traducción"""
    try:
        db_path = "data/geopolitical_intel.db"
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Agregando columnas de traducción...")
        
        # Verificar qué columnas ya existen
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"Columnas existentes: {existing_columns}")
        
        # Agregar columna original_language si no existe
        if 'original_language' not in existing_columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN original_language TEXT")
            print("✅ Columna 'original_language' agregada")
        else:
            print("ℹ️ Columna 'original_language' ya existe")
        
        # Agregar columna is_translated si no existe
        if 'is_translated' not in existing_columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN is_translated INTEGER DEFAULT 0")
            print("✅ Columna 'is_translated' agregada")
        else:
            print("ℹ️ Columna 'is_translated' ya existe")
        
        # Agregar columna original_title si no existe (para guardar título original)
        if 'original_title' not in existing_columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN original_title TEXT")
            print("✅ Columna 'original_title' agregada")
        else:
            print("ℹ️ Columna 'original_title' ya existe")
        
        # Agregar columna original_content si no existe
        if 'original_content' not in existing_columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN original_content TEXT")
            print("✅ Columna 'original_content' agregada")
        else:
            print("ℹ️ Columna 'original_content' ya existe")
        
        conn.commit()
        
        # Verificar columnas finales
        cursor.execute("PRAGMA table_info(articles)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"Columnas finales: {final_columns}")
        
        # Obtener estadísticas
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE original_language IS NOT NULL")
        articles_with_lang = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_translated = 1")
        translated_articles = cursor.fetchone()[0]
        
        print(f"\n📊 Estadísticas:")
        print(f"Total artículos: {total_articles}")
        print(f"Con idioma detectado: {articles_with_lang}")
        print(f"Traducidos: {translated_articles}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def detect_languages_sample():
    """Detectar idiomas en una muestra de artículos"""
    try:
        db_path = "data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 Detectando idiomas en muestra de artículos...")
        
        # Obtener muestra de artículos sin idioma detectado
        cursor.execute("""
            SELECT id, title, content
            FROM articles 
            WHERE original_language IS NULL
            AND (title IS NOT NULL AND title != '')
            ORDER BY id DESC
            LIMIT 10
        """)
        
        articles = cursor.fetchall()
        
        for article_id, title, content in articles:
            # Detectar idioma simple
            if title:
                english_indicators = ['the ', 'and ', 'for ', 'with ', 'from ', 'that ', 'this ', 'breaking']
                spanish_indicators = ['el ', 'la ', 'de ', 'que ', 'en ', 'con ', 'para ', 'del ']
                
                title_lower = title.lower()
                english_count = sum(1 for word in english_indicators if word in title_lower)
                spanish_count = sum(1 for word in spanish_indicators if word in title_lower)
                
                detected_lang = 'unknown'
                if english_count > spanish_count and english_count >= 2:
                    detected_lang = 'en'
                elif spanish_count > english_count and spanish_count >= 2:
                    detected_lang = 'es'
                
                print(f"ID {article_id}: {detected_lang} - {title[:60]}...")
                
                # Actualizar idioma detectado
                cursor.execute("""
                    UPDATE articles 
                    SET original_language = ?
                    WHERE id = ?
                """, (detected_lang, article_id))
        
        conn.commit()
        conn.close()
        print("✅ Detección de idiomas completada")
        
    except Exception as e:
        print(f"❌ Error detectando idiomas: {e}")

def main():
    print("🌍 Configuración de Base de Datos para Traducción")
    print("=" * 50)
    
    success = add_translation_columns()
    if success:
        detect_languages_sample()
    
    print("\n✅ Configuración completada")

if __name__ == "__main__":
    main()
