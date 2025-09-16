"""
Script para traducir automáticamente todos los artículos en inglés de la base de datos
"""
import sqlite3
import logging
import requests
import time
from googletrans import Translator
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def detect_english(text):
    """Detectar si el texto está en inglés"""
    if not text or len(text) < 10:
        return False
    
    # Palabras comunes en inglés
    english_words = [
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
        'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'with',
        'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time',
        'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many',
        'over', 'such', 'take', 'than', 'them', 'well', 'were', 'into', 'that',
        'have', 'will', 'would', 'could', 'should', 'about', 'after', 'before'
    ]
    
    words = text.lower().split()[:20]  # Primeras 20 palabras
    english_matches = sum(1 for word in words if word in english_words)
    
    # También verificar patrones comunes en inglés
    english_patterns = ['ing ', 'ed ', 'tion ', 'ly ', 'the ', 'and ']
    pattern_matches = sum(1 for pattern in english_patterns if pattern in text.lower())
    
    # Considerar inglés si hay suficientes indicadores
    return (english_matches >= 2) or (pattern_matches >= 2)

def translate_with_google(text, target_lang='es'):
    """Traducir texto usando Google Translate gratuito"""
    try:
        translator = Translator()
        result = translator.translate(text, dest=target_lang)
        return result.text
    except Exception as e:
        logger.error(f"Error con Google Translate: {e}")
        return None

def translate_articles():
    """Traducir todos los artículos en inglés de la base de datos"""
    
    # Conectar a la base de datos
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    try:
        # Obtener todos los artículos
        cursor.execute("""
            SELECT id, title, content, summary 
            FROM articles 
            ORDER BY id
        """)
        
        articles = cursor.fetchall()
        total_articles = len(articles)
        
        logger.info(f"Revisando {total_articles} artículos para detectar inglés...")
        
        # Contadores
        stats = {
            'total': total_articles,
            'english_detected': 0,
            'translated': 0,
            'failed': 0
        }
        
        for i, (article_id, title, content, summary) in enumerate(articles, 1):
            try:
                needs_translation = False
                translated_title = title
                translated_content = content
                translated_summary = summary
                
                # Verificar título
                if title and detect_english(title):
                    logger.info(f"Detectado título en inglés para artículo {article_id}: {title[:50]}...")
                    translated_title = translate_with_google(title)
                    if translated_title:
                        needs_translation = True
                        logger.info(f"Título traducido: {translated_title[:50]}...")
                    else:
                        translated_title = title  # Mantener original si falla
                
                # Verificar contenido
                if content and detect_english(content):
                    logger.info(f"Detectado contenido en inglés para artículo {article_id}")
                    translated_content = translate_with_google(content)
                    if translated_content:
                        needs_translation = True
                        logger.info(f"Contenido traducido: {translated_content[:50]}...")
                    else:
                        translated_content = content  # Mantener original si falla
                
                # Verificar resumen
                if summary and detect_english(summary):
                    logger.info(f"Detectado resumen en inglés para artículo {article_id}")
                    translated_summary = translate_with_google(summary)
                    if translated_summary:
                        needs_translation = True
                        logger.info(f"Resumen traducido: {translated_summary[:50]}...")
                    else:
                        translated_summary = summary  # Mantener original si falla
                
                if needs_translation:
                    stats['english_detected'] += 1
                    
                    # Actualizar en la base de datos
                    cursor.execute("""
                        UPDATE articles 
                        SET title = ?, content = ?, summary = ?, 
                            last_enriched = ?
                        WHERE id = ?
                    """, (translated_title, translated_content, translated_summary, 
                          datetime.now().isoformat(), article_id))
                    
                    stats['translated'] += 1
                    logger.info(f"✅ Artículo {article_id} traducido exitosamente")
                    
                    # Pausa para evitar rate limiting
                    time.sleep(0.1)
                
                # Log progreso cada 50 artículos
                if i % 50 == 0:
                    logger.info(f"Progreso: {i}/{total_articles} artículos revisados...")
                    
            except Exception as e:
                logger.error(f"Error procesando artículo {article_id}: {e}")
                stats['failed'] += 1
                continue
        
        # Commit cambios
        conn.commit()
        
        # Mostrar estadísticas finales
        logger.info("\n" + "="*60)
        logger.info("TRADUCCIÓN COMPLETADA")
        logger.info("="*60)
        logger.info(f"Total artículos revisados: {stats['total']}")
        logger.info(f"Artículos en inglés detectados: {stats['english_detected']}")
        logger.info(f"Artículos traducidos exitosamente: {stats['translated']}")
        logger.info(f"Errores: {stats['failed']}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error durante la traducción: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Instalar googletrans si no está disponible
    try:
        from googletrans import Translator
    except ImportError:
        logger.info("Instalando googletrans...")
        import subprocess
        subprocess.check_call(["pip", "install", "googletrans==4.0.0rc1"])
        from googletrans import Translator
    
    translate_articles()
