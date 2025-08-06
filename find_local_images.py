import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Buscar artículos con imagen_url que contenga "data"
cursor.execute("SELECT id, title, image_url FROM articles WHERE image_url LIKE '%data%' LIMIT 10")
results = cursor.fetchall()

print(f"Artículos con URLs que contienen 'data': {len(results)}")
for row in results:
    print(f"ID: {row[0]}")
    print(f"Título: {row[1][:60]}...")
    print(f"Image URL: {row[2]}")
    print("-" * 50)

conn.close()
