#!/usr/bin/env python3
"""
Script para arreglar imágenes problemáticas en la base de datos.
Reemplaza imágenes de Unsplash y fallback con imágenes originales de sus fuentes.
"""

import os
import sys
import sqlite3
import logging
from advanced_image_extractor import extract_original_image_for_article, ImageExtractor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_problematic_images():
    """Arreglar imágenes problemáticas en la base de datos"""
    
    db_path = 'data/geopolitical_intel.db'
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 ARREGLANDO IMÁGENES PROBLEMÁTICAS...")
    print("=" * 50)
    
    # Buscar artículos con imágenes problemáticas
    problematic_query = """
        SELECT id, title, url, image_url, source
        FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url LIKE '%unsplash.com%' 
             OR image_url LIKE '%placeholder%' 
             OR image_url LIKE '%fallback%'
             OR image_url LIKE '%stock%'
             OR image_url LIKE 'data:image%')
        AND url IS NOT NULL AND url != ''
        ORDER BY 
            CASE 
                WHEN risk_level = 'high' THEN 1
                WHEN risk_level = 'medium' THEN 2
                ELSE 3
            END
        LIMIT 50
    """
    
    cursor.execute(problematic_query)
    problematic_articles = cursor.fetchall()
    
    if not problematic_articles:
        print("✅ No se encontraron artículos con imágenes problemáticas")
        conn.close()
        return
    
    print(f"🔍 Encontrados {len(problematic_articles)} artículos con imágenes problemáticas")
    
    extractor = ImageExtractor()
    fixed_count = 0
    
    for article in problematic_articles:
        article_id, title, url, current_image, source = article
        
        print(f"\n📰 Procesando artículo {article_id}: {title[:60]}...")
        print(f"   Fuente: {source}")
        print(f"   URL: {url}")
        print(f"   Imagen actual: {current_image[:60]}...")
        
        try:
            # Intentar extraer imagen original
            article_data = {
                'id': article_id,
                'title': title,
                'url': url,
                'source': source
            }
            
            original_image = extract_original_image_for_article(article_data)
            
            if original_image and original_image.get('url'):
                new_image_url = original_image['url']
                
                # Verificar que la nueva imagen es diferente y no problemática
                if (new_image_url != current_image and 
                    'unsplash.com' not in new_image_url and 
                    'placeholder' not in new_image_url.lower() and
                    'fallback' not in new_image_url.lower()):
                    
                    # Actualizar en la base de datos
                    cursor.execute("""
                        UPDATE articles 
                        SET image_url = ?, 
                            image_fingerprint = ?
                        WHERE id = ?
                    """, (new_image_url, original_image.get('fingerprint', ''), article_id))
                    
                    print(f"   ✅ ARREGLADO: Nueva imagen: {new_image_url[:60]}...")
                    fixed_count += 1
                else:
                    print(f"   ⚠️ Nueva imagen también problemática o igual: {new_image_url[:60]}...")
            else:
                print(f"   ❌ No se pudo obtener imagen original")
                
        except Exception as e:
            print(f"   ❌ Error procesando artículo {article_id}: {e}")
            continue
    
    # Confirmar cambios
    conn.commit()
    conn.close()
    
    print(f"\n🎉 PROCESO COMPLETADO:")
    print(f"   📊 Artículos procesados: {len(problematic_articles)}")
    print(f"   ✅ Imágenes arregladas: {fixed_count}")
    print(f"   📈 Tasa de éxito: {(fixed_count/len(problematic_articles)*100):.1f}%")

def remove_duplicate_images():
    """Remover artículos con imágenes duplicadas del mosaico"""
    
    db_path = 'data/geopolitical_intel.db'
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔄 REMOVIENDO DUPLICADOS...")
    print("=" * 30)
    
    # Encontrar imágenes duplicadas
    cursor.execute("""
        SELECT image_url, COUNT(*) as count, GROUP_CONCAT(id) as article_ids
        FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url IS NOT NULL AND image_url != '')
        GROUP BY image_url
        HAVING count > 1
        ORDER BY count DESC
    """)
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"🔍 Encontradas {len(duplicates)} imágenes duplicadas")
        
        for image_url, count, article_ids in duplicates:
            ids = article_ids.split(',')
            # Mantener solo el primer artículo, marcar el resto como excluidos
            keep_id = ids[0]
            exclude_ids = ids[1:]
            
            if len(exclude_ids) > 0:
                # Marcar como excluidos los duplicados
                for exclude_id in exclude_ids:
                    cursor.execute("""
                        UPDATE articles 
                        SET is_excluded = 1, 
                            excluded_reason = 'Imagen duplicada'
                        WHERE id = ?
                    """, (exclude_id,))
                
                print(f"   ✅ Mantenido artículo {keep_id}, excluidos {len(exclude_ids)} duplicados de: {image_url[:60]}...")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    try:
        fix_problematic_images()
        remove_duplicate_images()
        print("\n🎯 ¡MISIÓN CUMPLIDA! Las imágenes han sido arregladas.")
    except Exception as e:
        print(f"\n❌ Error durante el proceso: {e}")
        sys.exit(1)
