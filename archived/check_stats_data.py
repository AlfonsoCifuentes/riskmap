#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

print("🔍 VERIFICANDO DATOS PARA ESTADÍSTICAS")
print("="*50)

# 1. Alertas críticas
cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_score >= 0.7")
critical_alerts = cursor.fetchone()[0]
print(f"Alertas críticas (risk_score >= 0.7): {critical_alerts}")

# 2. Regiones con conflicto
cursor.execute("SELECT COUNT(DISTINCT country) FROM articles WHERE country IS NOT NULL AND risk_level = 'high'")
regions_in_conflict = cursor.fetchone()[0]
print(f"Regiones con conflicto: {regions_in_conflict}")

# 3. Fuentes monitoreadas
cursor.execute("SELECT COUNT(DISTINCT source) FROM articles WHERE source IS NOT NULL")
monitored_sources = cursor.fetchone()[0]
print(f"Fuentes monitoreadas: {monitored_sources}")

# 4. Fuentes activas (con artículos recientes)
cursor.execute("""
    SELECT COUNT(DISTINCT source) FROM articles 
    WHERE source IS NOT NULL 
    AND created_at >= datetime('now', '-7 days')
""")
active_sources = cursor.fetchone()[0]
print(f"Fuentes activas (últimos 7 días): {active_sources}")

# 5. Detalles de fuentes
cursor.execute("""
    SELECT source, COUNT(*) as articles_count 
    FROM articles 
    WHERE source IS NOT NULL 
    GROUP BY source 
    ORDER BY articles_count DESC 
    LIMIT 10
""")
sources_detail = cursor.fetchall()
print(f"\n📊 Top 10 fuentes:")
for source, count in sources_detail:
    print(f"  {source}: {count} artículos")

conn.close()