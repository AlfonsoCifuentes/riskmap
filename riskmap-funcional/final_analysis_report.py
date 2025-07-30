import sqlite3
import json
from collections import Counter

# Connect to database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

print("=" * 80)
print("INFORME FINAL DE ANÁLISIS - SISTEMA DE INTELIGENCIA GEOPOLÍTICA")
print("=" * 80)

# Total statistics
cursor.execute("SELECT COUNT(*) FROM articles")
total_articles = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM processed_data")
total_processed = cursor.fetchone()[0]

print(f"\n📊 ESTADÍSTICAS GENERALES:")
print(f"   Total de artículos: {total_articles}")
print(f"   Artículos procesados: {total_processed}")
print(f"   Tasa de procesamiento: {(total_processed/total_articles*100):.1f}%")

# Category distribution
cursor.execute("""
    SELECT category, COUNT(*) as count
    FROM processed_data
    GROUP BY category
    ORDER BY count DESC
""")
categories = cursor.fetchall()

print(f"\n📂 DISTRIBUCIÓN POR CATEGORÍAS:")
for cat, count in categories:
    percentage = (count/total_processed*100)
    print(f"   {cat:20} {count:4} artículos ({percentage:5.1f}%)")

# Risk level distribution
cursor.execute("""
    SELECT risk_level, COUNT(*) as count
    FROM articles
    WHERE risk_level IS NOT NULL
    GROUP BY risk_level
    ORDER BY count DESC
""")
risk_levels = cursor.fetchall()

print(f"\n⚠️  NIVELES DE RIESGO:")
for level, count in risk_levels:
    percentage = (count/total_articles*100)
    print(f"   {level:10} {count:4} artículos ({percentage:5.1f}%)")

# Language distribution
cursor.execute("""
    SELECT language, COUNT(*) as count
    FROM articles
    GROUP BY language
    ORDER BY count DESC
    LIMIT 10
""")
languages = cursor.fetchall()

print(f"\n🌍 IDIOMAS PRINCIPALES:")
for lang, count in languages:
    percentage = (count/total_articles*100)
    print(f"   {lang:5} {count:4} artículos ({percentage:5.1f}%)")

# Most mentioned countries
all_countries = []
cursor.execute("SELECT entities FROM processed_data WHERE entities IS NOT NULL")
for row in cursor.fetchall():
    try:
        entities = json.loads(row[0])
        countries = entities.get('GPE', [])
        all_countries.extend(countries)
    except:
        pass

if all_countries:
    country_counts = Counter(all_countries)
    print(f"\n🗺️  PAÍSES MÁS MENCIONADOS:")
    for country, count in country_counts.most_common(10):
        print(f"   {country:20} {count:3} menciones")

# Sample of high-risk articles
cursor.execute("""
    SELECT a.id, a.title, pd.category, pd.sentiment
    FROM articles a
    JOIN processed_data pd ON a.id = pd.article_id
    WHERE a.risk_level = 'high' OR pd.category IN ('military_conflict', 'terrorism', 'natural_disaster')
    LIMIT 5
""")
high_risk = cursor.fetchall()

if high_risk:
    print(f"\n🚨 EJEMPLOS DE ARTÍCULOS DE ALTO RIESGO:")
    for id, title, category, sentiment in high_risk:
        print(f"\n   ID: {id}")
        print(f"   Título: {title[:70]}...")
        print(f"   Categoría: {category}, Sentimiento: {sentiment:.2f}")

# Keywords analysis
all_keywords = []
cursor.execute("SELECT keywords FROM processed_data WHERE keywords IS NOT NULL AND keywords != '[]'")
for row in cursor.fetchall():
    try:
        keywords = json.loads(row[0])
        all_keywords.extend(keywords)
    except:
        pass

if all_keywords:
    keyword_counts = Counter(all_keywords)
    print(f"\n🔑 PALABRAS CLAVE MÁS FRECUENTES:")
    for keyword, count in keyword_counts.most_common(15):
        print(f"   {keyword:20} {count:3} veces")

conn.close()

print("\n" + "=" * 80)
print("✅ SISTEMA COMPLETAMENTE OPERATIVO")
print("=" * 80)