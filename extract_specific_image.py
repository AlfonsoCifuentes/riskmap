#!/usr/bin/env python3
"""
Script específico para extraer imagen del artículo de Israel-Gaza (ID: 657)
"""
import sqlite3
import os
import requests
import re
from urllib.parse import urljoin, urlparse
import time
import hashlib
from PIL import Image
from io import BytesIO

def extract_image_for_article_657():
    """Extrae imagen específicamente para el artículo ID 657"""
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener detalles del artículo 657
        cursor.execute("SELECT id, title, url FROM articles WHERE id = 657")
        result = cursor.fetchone()
        
        if not result:
            print("❌ Artículo ID 657 no encontrado")
            return
            
        article_id, title, url = result
        print(f"🔍 Procesando artículo ID {article_id}")
        print(f"📰 Título: {title}")
        print(f"🔗 URL: {url}")
        
        # Intentar extraer imágenes
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        content = response.text
        
        # Buscar imágenes
        img_patterns = [
            r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\'][^>]*>',
            r'"image":\s*"([^"]+)"',
            r'"thumbnail":\s*"([^"]+)"'
        ]
        
        image_urls = []
        for pattern in img_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                img_url = urljoin(url, match)
                if is_valid_image_url(img_url):
                    image_urls.append(img_url)
        
        print(f"🖼️  Encontradas {len(image_urls)} imágenes potenciales")
        
        if not image_urls:
            print("❌ No se encontraron imágenes válidas")
            return
        
        # Intentar descargar la primera imagen válida
        static_dir = "src/web/static/images/news/"
        os.makedirs(static_dir, exist_ok=True)
        
        for i, img_url in enumerate(image_urls[:3], 1):
            print(f"   🔄 Intentando imagen {i}: {img_url[:60]}...")
            
            try:
                img_response = requests.get(img_url, headers=headers, timeout=15, stream=True)
                img_response.raise_for_status()
                
                # Verificar content-type
                content_type = img_response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"      ❌ No es imagen válida: {content_type}")
                    continue
                
                # Generar nombre único
                url_hash = hashlib.md5(img_url.encode()).hexdigest()[:8]
                filename = f"news_{article_id}_{url_hash}.jpg"
                filepath = os.path.join(static_dir, filename)
                
                # Descargar
                with open(filepath, 'wb') as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verificar descarga
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    print(f"      ✅ Imagen descargada: {filename}")
                    
                    # Actualizar base de datos
                    cursor.execute("""
                        UPDATE articles 
                        SET original_image_url = ?, 
                            image_source = 'extracted',
                            has_image = 1
                        WHERE id = ?
                    """, (filename, article_id))
                    
                    conn.commit()
                    print(f"      ✅ Base de datos actualizada para artículo {article_id}")
                    conn.close()
                    return True
                else:
                    os.remove(filepath) if os.path.exists(filepath) else None
                    print(f"      ❌ Imagen inválida o muy pequeña")
                    
            except Exception as e:
                print(f"      ❌ Error descargando: {e}")
                continue
        
        print("❌ No se pudo descargar ninguna imagen válida")
        conn.close()
        return False
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def is_valid_image_url(url):
    """Verifica si una URL parece ser una imagen válida"""
    if not url or len(url) < 10:
        return False
        
    bad_patterns = ['placeholder', 'default', 'avatar', 'logo', 'icon', 'data:', 'blob:', 'advertisement']
    url_lower = url.lower()
    
    if any(pattern in url_lower for pattern in bad_patterns):
        return False
    
    # Verificar extensiones o dominios de imagen
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    image_domains = ['images.', 'img.', 'media.', 'photo.', 'pic.', 'cdn.']
    
    return (any(ext in url_lower for ext in image_extensions) or 
            any(domain in url_lower for domain in image_domains))

if __name__ == "__main__":
    print("🎯 EXTRACCIÓN ESPECÍFICA PARA ARTÍCULO ISRAEL-GAZA")
    print("=" * 50)
    success = extract_image_for_article_657()
    print("=" * 50)
    if success:
        print("✅ ÉXITO: Imagen extraída para artículo geopolítico")
        print("🔄 Reinicia la aplicación para ver los cambios")
    else:
        print("❌ FALLO: No se pudo extraer imagen")