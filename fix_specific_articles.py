#!/usr/bin/env python3
"""
Script para corregir artículos específicos problemáticos
"""

import sqlite3

def fix_specific_articles():
    """Corrige artículos específicos mencionados por el usuario"""
    
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Actualizar artículos específicos con mejores imágenes
    updates = [
        {
            'id': 3534,
            'image': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop'
        },
        {
            'id': 3173,
            'image': 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800&h=600&fit=crop'
        },
        {
            'id': 3178,
            'image': 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=600&fit=crop'
        }
    ]
    
    updated_count = 0
    for update in updates:
        cursor.execute('UPDATE articles SET image_url = ? WHERE id = ?', (update['image'], update['id']))
        if cursor.rowcount > 0:
            updated_count += 1
            print(f'✅ Actualizado artículo {update["id"]} con nueva imagen')
    
    # Limpiar logos y texturas problemáticas
    cursor.execute('''
        UPDATE articles 
        SET image_url = CASE 
            WHEN title LIKE '%gaza%' OR title LIKE '%hostage%' OR title LIKE '%israel%' 
                THEN 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop'
            WHEN title LIKE '%russia%' OR title LIKE '%ukraine%' OR title LIKE '%oil%' 
                THEN 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800&h=600&fit=crop'
            WHEN title LIKE '%trump%' OR title LIKE '%political%' 
                THEN 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=600&fit=crop'
            ELSE 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=600&fit=crop'
        END
        WHERE image_url LIKE '%ap-logo%' 
        OR image_url LIKE '%logo%' 
        OR image_url LIKE '%svg%'
        OR image_url LIKE '%texture%'
        OR image_url LIKE '%black%'
        OR image_url = ''
        OR image_url IS NULL
    ''')
    
    logo_cleaned = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f'🎉 COMPLETADO: {updated_count} artículos específicos actualizados, {logo_cleaned} logos/texturas limpiados')
    return updated_count, logo_cleaned

if __name__ == "__main__":
    fix_specific_articles()
