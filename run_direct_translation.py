#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar traducción directa de artículos en inglés a español
"""

import sys
import os
import sqlite3
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('translation_direct.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def detect_language_simple(text):
    """Detectar idioma de forma simple"""
    if not text:
        return 'unknown'
    
    # Palabras comunes en inglés
    english_words = ['the', 'and', 'for', 'are', 'with', 'his', 'they', 'this', 'have', 'from', 'that', 'not', 'but', 'what', 'can', 'out', 'other', 'were', 'all', 'there', 'when', 'your', 'how', 'said', 'each', 'which', 'she', 'their', 'time', 'will', 'about', 'would', 'been', 'many', 'some', 'breaking', 'news', 'report', 'reports', 'says', 'according', 'sources']
    
    # Palabras comunes en español
    spanish_words = ['el', 'la', 'de', 'que', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'han', 'fue', 'ser', 'está', 'son', 'como', 'más']
    
    text_lower = text.lower()
    words = text_lower.split()[:20]  # Analizar primeras 20 palabras
    
    english_count = sum(1 for word in words if word in english_words)
    spanish_count = sum(1 for word in words if word in spanish_words)
    
    if english_count > spanish_count and english_count >= 2:
        return 'en'
    elif spanish_count > english_count and spanish_count >= 2:
        return 'es'
    else:
        return 'unknown'

def basic_translate(text):
    """Traducción básica usando diccionario simple"""
    if not text:
        return text
    
    # Diccionario básico de traducciones comunes
    translations = {
        'breaking news': 'noticias de última hora',
        'breaking': 'de última hora',
        'news': 'noticias',
        'report': 'informe',
        'reports': 'informes',
        'according to': 'según',
        'sources': 'fuentes',
        'the': 'el/la',
        'and': 'y',
        'for': 'para',
        'with': 'con',
        'from': 'desde',
        'this': 'este/esta',
        'that': 'ese/esa',
        'what': 'qué',
        'when': 'cuando',
        'where': 'donde',
        'how': 'cómo',
        'why': 'por qué',
        'government': 'gobierno',
        'military': 'militar',
        'conflict': 'conflicto',
        'war': 'guerra',
        'peace': 'paz',
        'security': 'seguridad',
        'international': 'internacional',
        'crisis': 'crisis',
        'emergency': 'emergencia',
        'attack': 'ataque',
        'threat': 'amenaza',
        'president': 'presidente',
        'minister': 'ministro',
        'leader': 'líder',
        'country': 'país',
        'nation': 'nación',
        'world': 'mundo',
        'global': 'global'
    }
    
    result = text
    for english, spanish in translations.items():
        result = result.replace(english, spanish)
        result = result.replace(english.capitalize(), spanish.capitalize())
    
    return result

def translate_articles():
    """Función principal para traducir artículos"""
    try:
        # Conectar a la base de datos
        db_path = r"data\geopolitical_intel.db"
        if not os.path.exists(db_path):
            logger.error(f"❌ Base de datos no encontrada: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar que existen las columnas de traducción
        cursor.execute("PRAGMA table_info(articles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        required_columns = ['original_language', 'is_translated', 'original_title', 'original_content']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            logger.warning(f"⚠️ Faltan columnas: {missing_columns}")
            # Agregar columnas faltantes
            for col in missing_columns:
                if col in ['original_language']:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col} TEXT")
                elif col in ['is_translated']:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col} INTEGER DEFAULT 0")
                else:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col} TEXT")
            conn.commit()
            logger.info("✅ Columnas de traducción agregadas")
        
        # Buscar artículos en inglés que necesitan traducción
        query = """
            SELECT id, title, content, summary, original_language, is_translated
            FROM articles 
            WHERE (original_language IS NULL OR original_language = '' OR original_language = 'unknown')
               OR (original_language = 'en' AND (is_translated IS NULL OR is_translated = 0))
        """
        
        cursor.execute(query)
        articles_to_translate = cursor.fetchall()
        
        logger.info(f"📋 Encontrados {len(articles_to_translate)} artículos para procesar")
        
        translated_count = 0
        detected_count = 0
        
        for article in articles_to_translate:
            article_id, title, content, summary, original_language, is_translated = article
            
            # Detectar idioma si no está detectado
            if not original_language or original_language in ['', 'unknown']:
                detected_lang = detect_language_simple(title or content or '')
                cursor.execute(
                    "UPDATE articles SET original_language = ? WHERE id = ?",
                    (detected_lang, article_id)
                )
                detected_count += 1
                logger.info(f"🔍 Artículo {article_id}: idioma detectado como '{detected_lang}'")
            else:
                detected_lang = original_language
            
            # Traducir si está en inglés y no ha sido traducido
            if detected_lang == 'en' and (not is_translated or is_translated == 0):
                try:
                    # Guardar originales si no existen
                    cursor.execute(
                        "SELECT original_title, original_content FROM articles WHERE id = ?",
                        (article_id,)
                    )
                    originals = cursor.fetchone()
                    
                    if not originals or not originals[0]:  # Si no hay título original guardado
                        cursor.execute(
                            "UPDATE articles SET original_title = ?, original_content = ? WHERE id = ?",
                            (title, content, article_id)
                        )
                    
                    # Traducir título
                    translated_title = title
                    if title:
                        translated_title = basic_translate(title)
                    
                    # Traducir contenido (solo primeros 500 caracteres para eficiencia)
                    translated_content = content
                    if content:
                        content_snippet = content[:500]
                        translated_snippet = basic_translate(content_snippet)
                        translated_content = translated_snippet + (content[500:] if len(content) > 500 else '')
                    
                    # Traducir resumen
                    translated_summary = summary
                    if summary:
                        translated_summary = basic_translate(summary)
                    
                    # Actualizar en la base de datos
                    cursor.execute("""
                        UPDATE articles 
                        SET title = ?, content = ?, summary = ?, is_translated = 1
                        WHERE id = ?
                    """, (translated_title, translated_content, translated_summary, article_id))
                    
                    translated_count += 1
                    logger.info(f"✅ Artículo {article_id} traducido: '{title[:50]}...' -> '{translated_title[:50]}...'")
                    
                except Exception as e:
                    logger.error(f"❌ Error traduciendo artículo {article_id}: {e}")
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        logger.info(f"🎉 Proceso completado:")
        logger.info(f"   - Idiomas detectados: {detected_count}")
        logger.info(f"   - Artículos traducidos: {translated_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error general en traducción: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando traducción directa de artículos...")
    success = translate_articles()
    if success:
        logger.info("✅ Traducción completada exitosamente")
    else:
        logger.error("❌ Traducción falló")
    
    # Mostrar estadísticas finales
    try:
        db_path = r"data\geopolitical_intel.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE original_language = 'en'")
            english_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE original_language = 'en' AND is_translated = 1")
            translated_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE original_language = 'es'")
            spanish_articles = cursor.fetchone()[0]
            
            logger.info(f"📊 Estadísticas finales:")
            logger.info(f"   - Artículos en inglés: {english_articles}")
            logger.info(f"   - Artículos en inglés traducidos: {translated_articles}")
            logger.info(f"   - Artículos en español: {spanish_articles}")
            
            conn.close()
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
