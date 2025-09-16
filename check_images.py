#!/usr/bin/env python3
import sqlite3

def check_images_in_db():
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Contar artículos con imagen
    cursor.execute('SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ""')
    total_with_images = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]
    
    print(f'Artículos con imagen: {total_with_images}/{total_articles}')
    
    # Mostrar ejemplos
    cursor.execute('SELECT title, image_url FROM articles WHERE image_url IS NOT NULL AND image_url != "" LIMIT 5')
    print('\nEjemplos de artículos con imagen:')
    for row in cursor.fetchall():
        print(f'{row[0][:50]}... -> {row[1]}')
    
    # Mostrar ejemplos sin imagen
    cursor.execute('SELECT id, title, url FROM articles WHERE image_url IS NULL OR image_url = "" LIMIT 5')
    print('\nEjemplos de artículos SIN imagen:')
    for row in cursor.fetchall():
        print(f'ID: {row[0]} | {row[1][:50]}... | URL: {row[2]}')
    
    conn.close()

if __name__ == "__main__":
    check_images_in_db()
