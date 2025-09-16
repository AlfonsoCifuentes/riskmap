import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Buscar artículos con image_url que contenga "data" y ver el formato exacto
cursor.execute("SELECT id, title, image_url FROM articles WHERE image_url LIKE '%data%' LIMIT 20")
results = cursor.fetchall()

print(f"Artículos con URLs que contienen 'data': {len(results)}")
print("=" * 70)

for row in results:
    print(f"ID: {row[0]}")
    print(f"Título: {row[1][:60]}...")
    print(f"Image URL original: '{row[2]}'")
    
    # Test de la función de normalización
    url = row[2]
    if url.startswith('data\\images\\') or url.startswith('data/images/'):
        filename = url.replace('data\\images\\', '').replace('data/images/', '')
        normalized_url = f"/data/images/{filename}"
        print(f"URL normalizada: '{normalized_url}'")
    else:
        print(f"URL no necesita normalización: '{url}'")
    
    print("-" * 70)

conn.close()
