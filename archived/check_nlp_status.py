#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

print("📊 ANÁLISIS DEL SISTEMA NLP ACTUAL")
print("=" * 50)

# Check current table structure
cursor.execute("PRAGMA table_info(articles)")
columns = cursor.fetchall()
print("🔍 Columnas en la tabla 'articles':")
for col in columns:
    print(f"   - {col[1]} ({col[2]})")

print("\n" + "=" * 50)

# Check if there's already NLP processing tracking
print("📈 Estado actual del procesamiento NLP:")

# Check how many articles have been processed
cursor.execute("SELECT COUNT(*) FROM articles WHERE processed = 1")
processed_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM articles")
total_count = cursor.fetchone()[0]

print(f"📰 Total artículos: {total_count}")
print(f"✅ Procesados NLP: {processed_count}")
print(f"⏳ Pendientes NLP: {total_count - processed_count}")

# Check if advanced_nlp column exists
try:
    cursor.execute("SELECT COUNT(*) FROM articles WHERE advanced_nlp IS NOT NULL")
    advanced_nlp_count = cursor.fetchone()[0]
    print(f"🧠 Con análisis NLP avanzado: {advanced_nlp_count}")
except:
    print("⚠️ Columna 'advanced_nlp' no existe")

# Check if there's a processed_data table
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='processed_data'")
    processed_table = cursor.fetchone()
    if processed_table:
        cursor.execute("SELECT COUNT(*) FROM processed_data")
        processed_data_count = cursor.fetchone()[0]
        print(f"📊 Registros en 'processed_data': {processed_data_count}")
    else:
        print("⚠️ Tabla 'processed_data' no existe")
except Exception as e:
    print(f"⚠️ Error verificando 'processed_data': {e}")

print(f"\n🔧 RECOMENDACIONES:")
print(f"1. Optimizar para solo procesar artículos nuevos")
print(f"2. Guardar resultados NLP en base de datos")
print(f"3. Usar flags de procesamiento para evitar re-procesamiento")
print(f"4. Implementar sistema incremental")

conn.close()