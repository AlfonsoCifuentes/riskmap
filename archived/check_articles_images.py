import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Verificar artículos de alto riesgo
cursor.execute("""
    SELECT COUNT(*) 
    FROM articles 
    WHERE risk_level = 'high' 
    AND (is_excluded IS NULL OR is_excluded != 1)
""")
high_risk_count = cursor.fetchone()[0]
print(f"Artículos de alto riesgo disponibles: {high_risk_count}")

# Ejemplos de artículos de alto riesgo
cursor.execute("""
    SELECT id, title, risk_level, published_at, image_url
    FROM articles 
    WHERE risk_level = 'high' 
    AND (is_excluded IS NULL OR is_excluded != 1)
    ORDER BY datetime(published_at) DESC 
    LIMIT 5
""")
articles = cursor.fetchall()
print("\nEjemplos de artículos de ALTO RIESGO:")
for a in articles:
    print(f"ID: {a[0]}, Risk: {a[2]}, Date: {a[3]}")
    print(f"Title: {a[1][:80]}...")
    print(f"¿Tiene imagen?: {'SÍ' if a[4] else 'NO'}")
    print("-" * 80)

# Verificar que existen artículos de alto riesgo con imagen
cursor.execute("""
    SELECT COUNT(*) 
    FROM articles 
    WHERE risk_level = 'high' 
    AND (is_excluded IS NULL OR is_excluded != 1)
    AND (image_url IS NOT NULL AND image_url != '' AND image_url NOT LIKE '%placeholder%')
""")
high_risk_with_image = cursor.fetchone()[0]
print(f"\nArtículos de alto riesgo CON IMAGEN: {high_risk_with_image}")

# Probar la consulta exacta del hero
cursor.execute("""
    SELECT id, title, risk_level, published_at
    FROM articles 
    WHERE (is_excluded IS NULL OR is_excluded != 1)
    AND (image_url IS NOT NULL AND image_url != '' 
         AND image_url NOT LIKE '%placeholder%')
    ORDER BY 
        CASE 
            WHEN risk_level = 'high' THEN 1
            WHEN risk_level = 'medium' THEN 2
            WHEN risk_level = 'low' THEN 3
            ELSE 4
        END,
        datetime(published_at) DESC,
        id DESC
    LIMIT 1
""")
hero_result = cursor.fetchone()
if hero_result:
    print(f"\nArtículo HERO seleccionado:")
    print(f"ID: {hero_result[0]}, Risk: {hero_result[2]}, Date: {hero_result[3]}")
    print(f"Title: {hero_result[1][:80]}...")
else:
    print("\n❌ NO se encontró artículo hero")

conn.close()
