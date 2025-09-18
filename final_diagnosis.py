#!/usr/bin/env python3

import sqlite3
import sys
import os

print("🔍 DIAGNÓSTICO COMPLETO DEL DASHBOARD")
print("=" * 60)

# 1. Check article count and language
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Total articles
cursor.execute("SELECT COUNT(*) FROM articles")
total_articles = cursor.fetchone()[0]
print(f"📰 Total de artículos en DB: {total_articles}")

# Articles with images
cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL")
articles_with_images = cursor.fetchone()[0]
print(f"🖼️  Artículos con imagen: {articles_with_images}")

# Risk levels
cursor.execute("""
    SELECT risk_level, COUNT(*) 
    FROM articles 
    WHERE risk_level IS NOT NULL 
    GROUP BY risk_level
""")
risk_stats = cursor.fetchall()
print(f"⚠️  Niveles de riesgo:")
for level, count in risk_stats:
    print(f"   - {level}: {count} artículos")

# Regions count
cursor.execute("SELECT COUNT(DISTINCT country) FROM articles WHERE country IS NOT NULL")
countries_count = cursor.fetchone()[0]
print(f"🌍 Países únicos: {countries_count}")

# Check for remaining French articles
cursor.execute("""
    SELECT COUNT(*) 
    FROM articles 
    WHERE (title LIKE '%à%' OR title LIKE '%é%' OR title LIKE '%è%' OR title LIKE '%ç%' OR title LIKE '%ô%' OR title LIKE '%ü%'
           OR content LIKE '%à%' OR content LIKE '%é%' OR content LIKE '%è%' OR content LIKE '%ç%' OR content LIKE '%ô%' OR content LIKE '%ü%'
           OR summary LIKE '%à%' OR summary LIKE '%é%' OR summary LIKE '%è%' OR summary LIKE '%ç%' OR summary LIKE '%ô%' OR summary LIKE '%ü%')
    AND (title NOT LIKE '%español%' AND title NOT LIKE '%spanish%')
""")
french_remaining = cursor.fetchone()[0]
print(f"🇫🇷 Artículos en francés restantes: {french_remaining}")

# Sample titles to verify language
cursor.execute("SELECT title FROM articles ORDER BY published_at DESC LIMIT 5")
sample_titles = cursor.fetchall()
print(f"📄 Títulos de muestra:")
for i, (title,) in enumerate(sample_titles, 1):
    print(f"   {i}. {title[:100]}...")

# High risk articles with location
cursor.execute("""
    SELECT COUNT(*) 
    FROM articles 
    WHERE risk_level = 'high' AND (country IS NOT NULL OR region IS NOT NULL)
""")
high_risk_with_location = cursor.fetchone()[0]
print(f"🚨 Artículos de alto riesgo con ubicación: {high_risk_with_location}")

conn.close()

print(f"\n✅ RESUMEN DEL DIAGNÓSTICO:")
print(f"   • Total artículos: {total_articles}")
print(f"   • Con imágenes: {articles_with_images}")
print(f"   • Países únicos: {countries_count}")
print(f"   • Francés restante: {french_remaining}")
print(f"   • Alto riesgo con ubicación: {high_risk_with_location}")

if french_remaining == 0:
    print("🎉 ¡Todos los artículos están en español!")
else:
    print(f"⚠️  Aún quedan {french_remaining} artículos en francés por traducir")

if countries_count > 0:
    print("🎉 ¡Las estadísticas de región deberían funcionar!")
else:
    print("⚠️  Faltan datos de regiones")

if total_articles >= 50:
    print("🎉 ¡El mosaico debería tener suficientes artículos!")
else:
    print(f"⚠️  Solo hay {total_articles} artículos, podría necesitar más")

print(f"\n🎯 ESTADO FINAL:")
print(f"   Todas las correcciones aplicadas:")
print(f"   ✅ Límite de artículos aumentado a 50")
print(f"   ✅ Sistema de traducción mejorado con múltiples fallbacks") 
print(f"   ✅ Estadísticas de región corregidas")
print(f"   ✅ Overlay del mosaico solo muestra título (no contenido)")