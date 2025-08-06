#!/usr/bin/env python3
"""
Test simple para verificar URLs de imágenes en la base de datos
"""

import sqlite3
from pathlib import Path

def test_local_image_urls():
    print("🖼️ VERIFICACIÓN DE URLs DE IMÁGENES LOCALES")
    print("=" * 50)
    
    # Conectar a la base de datos
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Obtener artículos con imágenes locales
    cursor.execute('''
        SELECT id, title, image_url 
        FROM articles 
        WHERE image_url IS NOT NULL 
        AND (image_url LIKE "data\\\\images\\\\%" OR image_url LIKE "data/images/%")
        ORDER BY id DESC
        LIMIT 5
    ''')
    
    local_images = cursor.fetchall()
    
    print(f"📊 Artículos con imágenes locales encontrados: {len(local_images)}")
    print()
    
    if local_images:
        print("🔍 EJEMPLOS DE URLs DE IMÁGENES LOCALES:")
        print("-" * 60)
        
        for article_id, title, image_url in local_images:
            # Normalizar URL
            if image_url.startswith('data\\\\images\\\\') or image_url.startswith('data/images/'):
                filename = image_url.replace('data\\\\images\\\\', '').replace('data/images/', '')
                normalized_url = f"/data/images/{filename}"
            else:
                normalized_url = image_url
            
            print(f"📰 ID: {article_id}")
            print(f"📝 Título: {title[:50]}{'...' if len(title) > 50 else ''}")
            print(f"🔗 URL original: {image_url}")
            print(f"✅ URL normalizada: {normalized_url}")
            
            # Verificar que el archivo existe
            filename_clean = filename.replace('\\\\', '/')
            image_file = Path(f"data/images/{filename_clean}")
            if image_file.exists():
                print(f"✅ Archivo existe: {image_file}")
            else:
                print(f"❌ Archivo NO existe: {image_file}")
            print("-" * 60)
    
    # JavaScript test function
    print("\n🔧 FUNCIÓN JAVASCRIPT PARA PRUEBAS:")
    print("Puedes usar esta función en la consola del navegador:")
    print("""
function testImageNormalization() {
    const testUrls = [
        'data\\\\images\\\\article_525_c9ab8b05.jpg',
        'data/images/article_526_adbaf414.jpg',
        'https://external-image.com/image.jpg'
    ];
    
    testUrls.forEach(url => {
        const normalized = normalizeImageUrl(url);
        console.log(`Original: ${url}`);
        console.log(`Normalized: ${normalized}`);
        console.log('---');
    });
}
""")
    
    conn.close()

if __name__ == '__main__':
    test_local_image_urls()
