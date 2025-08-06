#!/usr/bin/env python3
"""
Script para traducir todos los artículos en inglés de la base de datos al español.
Utiliza el sistema de traducción existente con LibreTranslate, Groq, OpenAI y DeepSeek.
"""

import sqlite3
import logging
import sys
from pathlib import Path
import time
from typing import List, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from src.utils.translation import TranslationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ArticleTranslator:
    """Traductor de artículos en la base de datos."""
    
    def __init__(self, db_path: str = "data/geopolitical_intel.db"):
        self.db_path = db_path
        self.translation_service = TranslationService()
        
    def get_english_articles(self) -> List[Tuple]:
        """Obtiene todos los artículos en inglés de la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar artículos en inglés que no han sido traducidos
            query = """
            SELECT id, title, content, summary, auto_generated_summary, language
            FROM articles 
            WHERE language = 'en' 
            OR language = 'English'
            OR language LIKE '%en%'
            OR language IS NULL
            ORDER BY id DESC
            """
            
            cursor.execute(query)
            articles = cursor.fetchall()
            
            conn.close()
            
            logger.info(f"Encontrados {len(articles)} artículos en inglés para traducir")
            return articles
            
        except Exception as e:
            logger.error(f"Error obteniendo artículos en inglés: {e}")
            return []
    
    def translate_article_fields(self, article_data: Tuple) -> dict:
        """Traduce los campos de un artículo del inglés al español."""
        article_id, title, content, summary, auto_summary, _ = article_data
        
        try:
            # Preparar datos del artículo
            translated_data = {
                'id': article_id,
                'title_es': title,
                'content_es': content,
                'summary_es': summary,
                'auto_summary_es': auto_summary,
                'language': 'es'
            }
            
            # Traducir título
            if title and len(title.strip()) > 5:
                logger.info(f"Traduciendo título del artículo {article_id}: {title[:50]}...")
                translated_data['title_es'] = self.translation_service.translate(title, 'en', 'es')
                time.sleep(1)  # Evitar rate limiting
            
            # Traducir contenido (solo primeros 2000 caracteres para eficiencia)
            if content and len(content.strip()) > 20:
                content_to_translate = content[:2000] if len(content) > 2000 else content
                logger.info(f"Traduciendo contenido del artículo {article_id}...")
                translated_data['content_es'] = self.translation_service.translate(content_to_translate, 'en', 'es')
                time.sleep(1)  # Evitar rate limiting
            
            # Traducir resumen
            if summary and len(summary.strip()) > 10:
                logger.info(f"Traduciendo resumen del artículo {article_id}...")
                translated_data['summary_es'] = self.translation_service.translate(summary, 'en', 'es')
                time.sleep(1)  # Evitar rate limiting
            
            # Traducir resumen auto-generado
            if auto_summary and len(auto_summary.strip()) > 10:
                logger.info(f"Traduciendo auto-resumen del artículo {article_id}...")
                translated_data['auto_summary_es'] = self.translation_service.translate(auto_summary, 'en', 'es')
                time.sleep(1)  # Evitar rate limiting
            
            return translated_data
            
        except Exception as e:
            logger.error(f"Error traduciendo artículo {article_id}: {e}")
            return {
                'id': article_id,
                'title_es': title or '',
                'content_es': content or '',
                'summary_es': summary or '',
                'auto_summary_es': auto_summary or '',
                'language': 'es'
            }
    
    def update_article_in_db(self, translated_data: dict) -> bool:
        """Actualiza un artículo en la base de datos con las traducciones."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Actualizar el artículo con las traducciones
            update_query = """
            UPDATE articles 
            SET title = ?, 
                content = ?, 
                summary = ?, 
                auto_generated_summary = ?,
                language = ?
            WHERE id = ?
            """
            
            cursor.execute(update_query, (
                translated_data['title_es'],
                translated_data['content_es'],
                translated_data['summary_es'],
                translated_data['auto_summary_es'],
                translated_data['language'],
                translated_data['id']
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Artículo {translated_data['id']} actualizado con traducciones")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando artículo {translated_data['id']}: {e}")
            return False
    
    def translate_all_articles(self, max_articles: int = None):
        """Traduce todos los artículos en inglés de la base de datos."""
        logger.info("Iniciando traducción masiva de artículos...")
        
        # Obtener artículos en inglés
        english_articles = self.get_english_articles()
        
        if not english_articles:
            logger.info("No se encontraron artículos en inglés para traducir")
            return
        
        # Limitar el número de artículos si se especifica
        if max_articles:
            english_articles = english_articles[:max_articles]
            logger.info(f"Limitando traducción a {max_articles} artículos")
        
        translated_count = 0
        failed_count = 0
        
        for i, article in enumerate(english_articles):
            article_id = article[0]
            logger.info(f"\n--- Procesando artículo {i+1}/{len(english_articles)} (ID: {article_id}) ---")
            
            try:
                # Traducir artículo
                translated_data = self.translate_article_fields(article)
                
                if translated_data and any([
                    translated_data['title_es'] != (article[1] or ''),
                    translated_data['content_es'] != (article[2] or ''),
                    translated_data['summary_es'] != (article[3] or ''),
                    translated_data['auto_summary_es'] != (article[4] or '')
                ]):
                    # Solo actualizar si algo fue realmente traducido
                    if self.update_article_in_db(translated_data):
                        translated_count += 1
                        logger.info(f"✓ Artículo {article_id} traducido exitosamente")
                    else:
                        failed_count += 1
                        logger.error(f"✗ Error actualizando artículo {article_id}")
                else:
                    logger.info(f"⚠ Artículo {article_id} no necesita traducción o falló")
                    # No contar como fallo si simplemente no necesita traducción
                
                # Pausa entre artículos para evitar rate limiting
                if i < len(english_articles) - 1:
                    logger.info("Pausando 3 segundos...")
                    time.sleep(3)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"✗ Error procesando artículo {article_id}: {e}")
                continue
        
        # Resumen final
        logger.info("\n=== RESUMEN DE TRADUCCIÓN ===")
        logger.info(f"Total de artículos procesados: {len(english_articles)}")
        logger.info(f"Traducciones exitosas: {translated_count}")
        logger.info(f"Fallos: {failed_count}")
        logger.info(f"Tasa de éxito: {(translated_count/len(english_articles)*100):.1f}%")

def main():
    """Función principal."""
    print("🌍 Traductor de Artículos - Sistema de Inteligencia Geopolítica")
    print("=" * 60)
    
    translator = ArticleTranslator()
    
    # Preguntar cuántos artículos traducir
    try:
        response = input("\n¿Cuántos artículos quieres traducir? (Enter para todos, número para limitar): ").strip()
        max_articles = None if not response else int(response)
    except ValueError:
        print("Número inválido, traduciendo todos los artículos...")
        max_articles = None
    
    # Confirmar acción
    confirm = input(f"\n¿Proceder con la traducción{'de todos los artículos' if not max_articles else f' de {max_articles} artículos'}? (s/N): ").strip().lower()
    
    if confirm in ['s', 'sí', 'si', 'yes', 'y']:
        translator.translate_all_articles(max_articles)
    else:
        print("Traducción cancelada.")

if __name__ == "__main__":
    main()
