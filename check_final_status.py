#!/usr/bin/env python3
"""Verificar el estado final de la base de datos después del procesamiento masivo."""

import sqlite3
import json

def main():
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    print("📊 VERIFICACIÓN FINAL DE LA BASE DE DATOS")
    print("=" * 50)
    
    # Contar artículos con datos NLP
    cursor.execute('SELECT COUNT(*) FROM unified_articles WHERE countries_involved IS NOT NULL AND countries_involved != ""')
    nlp_count = cursor.fetchone()[0]
    print(f"✅ Artículos con análisis NLP: {nlp_count}")
    
    # Contar artículos con países
    cursor.execute('SELECT COUNT(*) FROM unified_articles WHERE countries_involved IS NOT NULL AND countries_involved != "[]"')
    countries_count = cursor.fetchone()[0]
    print(f"🌍 Artículos con países: {countries_count}")
    
    # Contar artículos con políticos
    cursor.execute('SELECT COUNT(*) FROM unified_articles WHERE politicians_involved IS NOT NULL AND politicians_involved != "[]"')
    politicians_count = cursor.fetchone()[0]
    print(f"👥 Artículos con políticos: {politicians_count}")
    
    # Contar artículos con armamento
    cursor.execute('SELECT COUNT(*) FROM unified_articles WHERE weapons_mentioned IS NOT NULL AND weapons_mentioned != "[]"')
    weapons_count = cursor.fetchone()[0]
    print(f"⚔️ Artículos con armamento: {weapons_count}")
    
    # Verificar ejemplos de armamento
    cursor.execute('SELECT title, weapons_mentioned FROM unified_articles WHERE weapons_mentioned IS NOT NULL AND weapons_mentioned != "[]" LIMIT 3')
    weapons_examples = cursor.fetchall()
    if weapons_examples:
        print("\n🔍 Ejemplos de detección de armamento:")
        for title, weapons in weapons_examples:
            weapons_list = json.loads(weapons) if weapons else []
            print(f"   • {title[:60]}... → {weapons_list}")
    
    # Verificar ejemplos de países
    cursor.execute('SELECT title, countries_involved FROM unified_articles WHERE countries_involved IS NOT NULL AND countries_involved != "[]" LIMIT 3')
    countries_examples = cursor.fetchall()
    if countries_examples:
        print("\n🌍 Ejemplos de detección de países:")
        for title, countries in countries_examples:
            countries_list = json.loads(countries) if countries else []
            print(f"   • {title[:60]}... → {countries_list}")
    
    # Verificar distribución de riesgo
    cursor.execute('SELECT risk_level, COUNT(*) FROM unified_articles WHERE risk_level IS NOT NULL GROUP BY risk_level')
    risk_distribution = cursor.fetchall()
    if risk_distribution:
        print("\n⚠️ Distribución de nivel de riesgo:")
        for level, count in risk_distribution:
            print(f"   • {level}: {count} artículos")
    
    # Total de artículos
    cursor.execute('SELECT COUNT(*) FROM unified_articles')
    total = cursor.fetchone()[0]
    print(f"\n📈 Total de artículos en la tabla unificada: {total}")
    
    # Verificar integridad de datos críticos
    cursor.execute('SELECT COUNT(*) FROM unified_articles WHERE title IS NOT NULL AND image_url IS NOT NULL AND summary IS NOT NULL')
    complete_articles = cursor.fetchone()[0]
    print(f"✅ Artículos con datos completos (título, imagen, resumen): {complete_articles}")
    
    print("\n" + "=" * 50)
    print("✅ VERIFICACIÓN COMPLETADA")
    
    conn.close()

if __name__ == "__main__":
    main()