#!/usr/bin/env python3
"""
Extractor de imágenes SIMPLE pero EFECTIVO
"""
import sqlite3
import requests
import re
from urllib.parse import urljoin
import time
from datetime import datetime

def extract_image_from_html(url, html_content):
    """Extrae imagen usando regex simple y efectivo"""
    
    image_patterns = [
        # Open Graph
        r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
        
        # Twitter Card  
        r'<meta[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']twitter:image["\']',
        
        # Schema.org
        r'<meta[^>]*itemprop=["\']image["\'][^>]*content=["\']([^"\']+)["\']',
        
        # CNN específico
        r'<img[^>]*src=["\']([^"\']*(?:stellar|dam|prod)[^"\']*\.jpg)["\']',
        
        # BBC específico  
        r'<img[^>]*src=["\']([^"\']*ichef\.bbci\.co\.uk[^"\']*)["\']',
        
        # AP News específico
        r'<img[^>]*src=["\']([^"\']*apnews\.com[^"\']*assets[^"\']*\.jpg)["\']',
        
        # Al Jazeera específico
        r'<img[^>]*src=["\']([^"\']*(?:aljazeera|aje\.io)[^"\']*\.jpg)["\']',
        
        # Reuters específico
        r'<img[^>]*src=["\']([^"\']*reuters\.com[^"\']*\.jpg)["\']',
        
        # Genérico - imágenes grandes
        r'<img[^>]*src=["\']([^"\']*\.jpg)["\'][^>]*(?:width=["\'](?:[5-9]\d\d|1\d\d\d)["\']|height=["\'](?:[3-9]\d\d|1\d\d\d)["\'])',
        
        # Figure/Picture tags
        r'<figure[^>]*>.*?<img[^>]*src=["\']([^"\']+\.jpg)["\']',
        
        # Clases relevantes
        r'<img[^>]*class=["\'][^"\']*(?:hero|main|featured|lead|primary|article)[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
    ]
    
    for pattern in image_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            img_url = match.strip()
            
            if not img_url:
                continue
                
            # Convertir URL relativa
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = urljoin(url, img_url)
            
            # Filtrar URLs malas
            if any(bad in img_url.lower() for bad in [
                'logo', 'icon', 'avatar', 'placeholder', 'default', 
                'loading', 'spinner', 'widget', 'thumbnail-small'
            ]):
                continue
            
            # Debe ser HTTPS
            if not img_url.startswith('https://'):
                continue
                
            # Verificar que sea imagen válida
            if verify_image_url(img_url):
                return img_url
    
    return None

def verify_image_url(img_url):
    """Verifica que una URL de imagen sea válida y accesible"""
    try:
        # HEAD request rápido
        response = requests.head(img_url, timeout=5, allow_redirects=True, 
                               headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if content_type.startswith('image/'):
                return True
        
        # Si HEAD no funciona, probar GET pequeño
        response = requests.get(img_url, timeout=5, stream=True,
                               headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        if response.status_code == 200:
            # Leer solo primeros bytes
            chunk = next(iter(response.iter_content(512)), b'')
            # Verificar magic bytes
            if (chunk.startswith(b'\xff\xd8\xff') or  # JPEG
                chunk.startswith(b'\x89PNG') or      # PNG
                chunk.startswith(b'GIF8')):          # GIF
                return True
        
        return False
        
    except:
        return False

def extract_all_images():
    """Extrae imágenes de todos los artículos"""
    
    print("🎯 EXTRACTOR DE IMÁGENES SIMPLE Y EFECTIVO")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener artículos sin imagen
        cursor.execute("""
            SELECT id, title, url, source 
            FROM articles 
            WHERE image_url IS NULL OR image_url = ''
               OR image_url LIKE '%localhost%'
               OR image_url LIKE '%placeholder%'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        articles = cursor.fetchall()
        
        print(f"📰 Procesando {len(articles)} artículos...")
        
        success_count = 0
        
        for i, (id, title, url, source) in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] ID:{id}")
            print(f"📰 {title[:50]}...")
            print(f"🌐 {source}")
            
            try:
                # Obtener HTML del artículo
                response = session.get(url, timeout=15)
                response.raise_for_status()
                
                # Extraer imagen usando regex
                image_url = extract_image_from_html(url, response.text)
                
                if image_url:
                    # Actualizar base de datos
                    cursor.execute("""
                        UPDATE articles 
                        SET image_url = ?, original_image_url = ?
                        WHERE id = ?
                    """, (image_url, image_url, id))
                    
                    success_count += 1
                    print(f"   ✅ IMAGEN: {image_url[:60]}...")
                    
                else:
                    print(f"   ❌ Sin imagen válida")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}...")
            
            # Pausa entre requests
            time.sleep(1.5)
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 RESULTADOS:")
        print(f"   Procesados: {len(articles)}")
        print(f"   Éxito: {success_count}")
        print(f"   Tasa: {(success_count/len(articles)*100):.1f}%" if articles else "N/A")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verify_current_state():
    """Verifica el estado actual"""
    
    print(f"\n🔍 VERIFICANDO RESULTADO...")
    
    try:
        response = requests.get("http://localhost:5001/api/articles?limit=8", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"📊 Mosaico actual ({len(articles)} artículos):")
            
            with_image = 0
            
            for i, article in enumerate(articles, 1):
                title = article.get('title', '')[:35]
                img_url = article.get('image_url', '')
                
                if img_url and img_url.startswith('https://'):
                    status = "✅"
                    with_image += 1
                else:
                    status = "❌"
                
                print(f"   {i}. {status} {title}...")
                
            total = len(articles)
            percentage = (with_image/total*100) if total > 0 else 0
            
            print(f"\n📈 RESULTADO FINAL:")
            print(f"   ✅ Con imagen: {with_image}")
            print(f"   ❌ Sin imagen: {total - with_image}")
            print(f"   📊 Porcentaje: {percentage:.1f}%")
            
            if percentage == 100:
                print("   🎉 ¡PERFECTO! TODAS las noticias tienen imagen original")
            elif percentage >= 80:
                print("   ✅ EXCELENTE resultado")
            elif percentage >= 60:
                print("   ✅ BUEN resultado")
            else:
                print("   ⚠️ Se necesita más trabajo")
                
    except Exception as e:
        print(f"❌ Error verificando: {e}")

def main():
    """Función principal"""
    
    success = extract_all_images()
    
    if success:
        verify_current_state()
        
        print(f"\n🚀 RECARGA LA PÁGINA (F5) PARA VER EL RESULTADO")
        print(f"   Todas las imágenes son ahora ORIGINALES de sus fuentes")
        
    else:
        print(f"\n❌ No se pudieron extraer imágenes")

if __name__ == "__main__":
    main()