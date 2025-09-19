import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Buscar artículos con URLs externas sin análisis CV
cursor.execute("""
    SELECT id, title, image_url 
    FROM articles 
    WHERE image_url LIKE 'http%' 
    AND visual_analysis_json IS NULL 
    LIMIT 5
""")

results = cursor.fetchall()
for row in results:
    print(f'ID: {row[0]}, Title: {row[1][:50]}, URL: {row[2]}')

conn.close()
