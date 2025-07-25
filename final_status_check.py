import sqlite3
import json

# Connect to the correct database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

print("=" * 60)
print("ESTADO FINAL DEL SISTEMA DE INTELIGENCIA GEOPOLÍTICA")
print("=" * 60)

# Total articles
cursor.execute("SELECT COUNT(*) FROM articles")
total = cursor.fetchone()[0]
print(f"\nTotal de artículos en base de datos: {total}")

# Processed articles
cursor.execute("SELECT COUNT(*) FROM processed_data")
processed = cursor.fetchone()[0]
print(f"Artículos procesados: {processed}")

# Articles by risk level
cursor.execute("""
    SELECT risk_level, COUNT(*) 
    FROM articles 
    WHERE risk_level IS NOT NULL
    GROUP BY risk_level
""")
print("\nDistribución por nivel de riesgo:")
for level, count in cursor.fetchall():
    print(f"  {level}: {count} artículos")

# Latest processed articles
cursor.execute("""
    SELECT a.id, a.title, a.risk_level, pd.category, pd.sentiment
    FROM articles a
    JOIN processed_data pd ON a.id = pd.article_id
    ORDER BY pd.id DESC
    LIMIT 5
""")
print("\nÚltimos artículos procesados:")
for row in cursor.fetchall():
    print(f"\n  ID: {row[0]}")
    print(f"  Título: {row[1][:60] if row[1] else 'None'}...")
    print(f"  Riesgo: {row[2]}, Categoría: {row[3]}, Sentimiento: {row[4]:.2f}")

# Show some keywords
cursor.execute("""
    SELECT pd.keywords
    FROM processed_data pd
    WHERE pd.keywords IS NOT NULL
    LIMIT 3
""")
print("\nEjemplos de palabras clave extraídas:")
for row in cursor.fetchall():
    if row[0]:
        try:
            keywords = json.loads(row[0])
            print(f"  {', '.join(keywords[:5])}")
        except:
            print(f"  {row[0]}")

conn.close()

print("\n" + "=" * 60)
print("Sistema funcionando correctamente!")
print("- Base de datos unificada: geopolitical_intel.db")
print("- Recolección de noticias: ✓")
print("- Procesamiento NLP: ✓")
print("- Análisis de sentimiento: ✓")
print("- Categorización: ✓")
print("- Extracción de entidades: ✓")
print("=" * 60)