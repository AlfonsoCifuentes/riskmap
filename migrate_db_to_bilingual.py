import sqlite3
import logging
from googletrans import Translator
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = 'data/geopolitical_intel.db'

def detect_language(text):
    """Detectar idioma simple (en o es)"""
    if not text:
        return 'es'  # Default a español
    english_words = ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all']
    spanish_words = ['el', 'la', 'de', 'en', 'que', 'y', 'a', 'es']
    words = text.lower().split()[:20]
    en_count = sum(1 for w in words if w in english_words)
    es_count = sum(1 for w in words if w in spanish_words)
    return 'en' if en_count > es_count else 'es'

def translate_text(text, target_lang):
    """Traducir texto usando googletrans"""
    try:
        translator = Translator()
        result = translator.translate(text, dest=target_lang)
        return result.text
    except Exception as e:
        logger.error(f"Error traduciendo: {e}")
        return text  # Retornar original si falla

def migrate_database():
    """Migrar DB a bilingual y actualizar datos existentes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Paso 1: Agregar columnas nuevas si no existen
        new_columns = [
            ('title_en', 'TEXT'),
            ('content_en', 'TEXT'),
            ('summary_en', 'TEXT'),
            ('original_language', "TEXT DEFAULT 'es'"),
            ('last_translated', 'TEXT')
        ]
        
        for col_name, col_type in new_columns:
            try:
                cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_type}")
                logger.info(f"Columna {col_name} agregada.")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    logger.info(f"Columna {col_name} ya existe, omitiendo.")
                else:
                    raise
        
        # Commit cambios de estructura
        conn.commit()
        
        # Paso 2: Actualizar datos existentes
        cursor.execute("SELECT id, title, content, summary FROM articles")
        articles = cursor.fetchall()
        total = len(articles)
        updated = 0
        
        for i, (art_id, title, content, summary) in enumerate(articles, 1):
            lang = detect_language(title + ' ' + (content or '')[:100])
            
            if lang == 'es':
                # Traducir a inglés
                title_en = translate_text(title, 'en') if title else ''
                content_en = translate_text(content, 'en') if content else ''
                summary_en = translate_text(summary, 'en') if summary else ''
            else:
                # Si es inglés, asumir columnas principales son traducción, traducir de vuelta? No, mejor asumir principales son es, y traducir a en
                title_en = translate_text(title, 'en') if title else ''
                content_en = translate_text(content, 'en') if content else ''
                summary_en = translate_text(summary, 'en') if summary else ''
            
            cursor.execute("""
                UPDATE articles 
                SET title_en = ?, content_en = ?, summary_en = ?,
                    original_language = ?, last_translated = ?
                WHERE id = ?
            """, (title_en, content_en, summary_en, lang, datetime.now().isoformat(), art_id))
            
            updated += 1
            if i % 50 == 0:
                logger.info(f"Progreso: {i}/{total} artículos actualizados")
        
        conn.commit()
        logger.info(f"Migración completada: {updated} artículos actualizados con versiones bilingües.")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en migración: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
