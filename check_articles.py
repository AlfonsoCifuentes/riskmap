import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

print("=== REVISIÓN DE ARTÍCULOS ===")
cursor.execute('SELECT title, country, risk_level, created_at FROM articles LIMIT 10')
rows = cursor.fetchall()

for i, row in enumerate(rows, 1):
    print(f"\n{i}. Título: {row[0][:80] if row[0] else 'Sin título'}...")
    print(f"   País: {row[1] or 'N/A'}")
    print(f"   Riesgo: {row[2] or 'N/A'}")
    print(f"   Fecha: {row[3] or 'N/A'}")

print(f"\n=== ESTADÍSTICAS ===")
cursor.execute('SELECT COUNT(*) FROM articles')
total = cursor.fetchone()[0]
print(f"Total artículos: {total}")

cursor.execute('SELECT COUNT(*) FROM articles WHERE risk_level = "high"')
high_risk = cursor.fetchone()[0]
print(f"Alto riesgo: {high_risk}")

cursor.execute('SELECT COUNT(DISTINCT country) FROM articles WHERE country IS NOT NULL')
countries = cursor.fetchone()[0]
print(f"Países únicos: {countries}")

conn.close()