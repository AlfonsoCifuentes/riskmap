#!/usr/bin/env python3
"""
Script rápido para mejorar imágenes de artículos específicos
Soluciona el problema de texturas negras y falta de imágenes
"""

import sqlite3
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_and_fix_problematic_articles():
    """Encuentra y corrige artículos con problemas de imagen específicos"""
    
    # Conectar a la base de datos
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Buscar artículos problemáticos específicos
    problematic_patterns = [
        "Videos of emaciated Israeli hostages in Gaza increase pressure on Netanyahu for a ceasefire",
        "Russian oil depot in Sochi set ablaze by Ukrainian drone strike",
        "No piecemeal deals': Witkoff tells hostage families Trump wants full Gaza agreement"
    ]
    
    # Imágenes de fallback inteligentes
    fallback_images = {
        'gaza': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop',
        'hostage': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop',
        'israeli': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop',
        'russian': 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800&h=600&fit=crop',
        'ukraine': 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800&h=600&fit=crop',
        'oil': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=600&fit=crop',
        'depot': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=600&fit=crop',
        'trump': 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=600&fit=crop',
        'agreement': 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=600&fit=crop',
        'ap news': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=600&fit=crop',
        'financial times': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=600&fit=crop',
        'axios': 'https://images.unsplash.com/photo-1495020689067-958852a7e369?w=800&h=600&fit=crop'
    }
    
    def get_smart_fallback(title, source):
        """Obtiene una imagen de fallback inteligente"""
        title_lower = title.lower()
        source_lower = source.lower() if source else ''
        
        # Verificar por fuente primero
        for key, image in fallback_images.items():
            if key in source_lower:
                return image
        
        # Verificar por contenido del título
        for key, image in fallback_images.items():
            if key in title_lower:
                return image
        
        # Fallback general
        return 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=600&fit=crop'
    
    # Buscar artículos sin imagen o con imágenes problemáticas
    cursor.execute('''
        SELECT id, title, url, source, image_url
        FROM articles 
        WHERE (
            image_url IS NULL 
            OR image_url = '' 
            OR image_url LIKE '%texture%'
            OR image_url LIKE '%black%'
            OR image_url LIKE '%fallback%'
            OR image_url LIKE '%placeholder%'
            OR image_url LIKE '%1x1%'
            OR image_url LIKE '%transparent%'
        )
        ORDER BY created_at DESC 
        LIMIT 30
    ''')
    
    articles = cursor.fetchall()
    logger.info(f"🔍 Encontrados {len(articles)} artículos con problemas de imagen")
    
    updated_count = 0
    for article_id, title, url, source, current_image in articles:
        try:
            logger.info(f"📰 Procesando: {title[:60]}...")
            
            # Obtener nueva imagen inteligente
            new_image = get_smart_fallback(title, source)
            
            # Actualizar en la base de datos
            cursor.execute('''
                UPDATE articles 
                SET image_url = ? 
                WHERE id = ?
            ''', (new_image, article_id))
            
            updated_count += 1
            logger.info(f"✅ Actualizado artículo {article_id} con imagen: {new_image}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando artículo {article_id}: {e}")
            continue
    
    # Eliminar imágenes específicamente problemáticas
    cursor.execute('''
        UPDATE articles 
        SET image_url = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=600&fit=crop'
        WHERE image_url LIKE '%texture%'
        OR image_url LIKE '%black%'
        OR image_url LIKE '%1x1%'
        OR image_url = ''
    ''')
    
    cleaned_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    logger.info(f"🎉 Proceso completado: {updated_count} artículos actualizados, {cleaned_count} imágenes problemáticas limpiadas")
    return updated_count, cleaned_count

def extract_image_from_ap_news(url):
    """Extractor específico para AP News"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar meta tags Open Graph
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Buscar imágenes en el contenido
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and 'apnews.com' in src and 'large' in src.lower():
                return src
        
        return None
        
    except Exception as e:
        logger.error(f"Error extrayendo de AP News: {e}")
        return None

def update_specific_articles():
    """Actualiza artículos específicos mencionados"""
    
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Artículos específicos con mejores imágenes
    specific_updates = [
        {
            'title_pattern': '%hostages%Gaza%pressure%Netanyahu%',
            'new_image': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop'
        },
        {
            'title_pattern': '%Russian%oil%depot%Sochi%Ukrainian%drone%',
            'new_image': 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800&h=600&fit=crop'
        },
        {
            'title_pattern': '%piecemeal%deals%Witkoff%hostage%families%Trump%Gaza%',
            'new_image': 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=600&fit=crop'
        }
    ]
    
    updated_specific = 0
    for update in specific_updates:
        cursor.execute('''
            UPDATE articles 
            SET image_url = ? 
            WHERE title LIKE ?
            AND (image_url IS NULL OR image_url = '' OR image_url LIKE '%texture%' OR image_url LIKE '%black%')
        ''', (update['new_image'], update['title_pattern']))
        
        if cursor.rowcount > 0:
            updated_specific += cursor.rowcount
            logger.info(f"✅ Actualizado {cursor.rowcount} artículo(s) con patrón: {update['title_pattern']}")
    
    conn.commit()
    conn.close()
    
    return updated_specific

def main():
    """Función principal"""
    logger.info("🚀 Iniciando corrección rápida de imágenes problemáticas...")
    
    # Paso 1: Corregir artículos específicos
    specific_count = update_specific_articles()
    
    # Paso 2: Limpiar artículos problemáticos en general
    updated_count, cleaned_count = find_and_fix_problematic_articles()
    
    total_updated = specific_count + updated_count
    
    logger.info(f"🎉 COMPLETADO: {total_updated} artículos actualizados, {cleaned_count} imágenes problemáticas limpiadas")
    
    return total_updated, cleaned_count

if __name__ == "__main__":
    main()
