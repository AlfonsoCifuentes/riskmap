#!/usr/bin/env python3
"""
Script para diagnosticar problemas con las APIs del dashboard
"""

import sqlite3
import json
from pathlib import Path

# Configurar rutas
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')

print("=== DIAGNÓSTICO DE APIS ===")
print(f"Base de datos: {DB_PATH}")

try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n1. VERIFICANDO ESTRUCTURA DE TABLAS:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tablas encontradas: {tables}")
    
    print("\n2. VERIFICANDO ARTÍCULOS:")
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    print(f"Total artículos: {total_articles}")
    
    if total_articles > 0:
        print("\n3. MUESTRA DE ARTÍCULOS:")
        cursor.execute("""
            SELECT title, content, country, risk_level, created_at, source_url, source, language
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        articles = []
        for row in cursor.fetchall():
            article = {
                'title': row['title'],
                'content': row['content'][:200] + '...' if row['content'] else 'Sin descripción disponible',
                'summary': row['content'][:150] + '...' if row['content'] else 'Sin resumen disponible',
                'created_at': row['created_at'],
                'country': row['country'] or 'Global',
                'location': row['country'] or 'Global',
                'risk_level': row['risk_level'] or 'medium',
                'source_url': row['source_url'],
                'url': row['source_url'],
                'source': row['source'] or 'Fuente desconocida',
                'language': row['language'] or 'es'
            }
            articles.append(article)
            print(f"- {article['title'][:60]}...")
            print(f"  País: {article['country']}, Riesgo: {article['risk_level']}")
        
        print(f"\n4. SIMULANDO RESPUESTA API /api/articles:")
        print(json.dumps(articles, indent=2, ensure_ascii=False))
        
        print(f"\n5. ARTÍCULOS DE ALTO RIESGO:")
        cursor.execute("""
            SELECT title, country, risk_level, created_at
            FROM articles 
            WHERE risk_level = 'high'
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        high_risk = []
        for row in cursor.fetchall():
            high_risk.append({
                'title': row['title'],
                'country': row['country'] or 'Global',
                'risk_level': row['risk_level'],
                'created_at': row['created_at']
            })
        
        print(f"Artículos de alto riesgo encontrados: {len(high_risk)}")
        for article in high_risk:
            print(f"- {article['title'][:60]}... ({article['country']})")
    
    print("\n6. VERIFICANDO EVENTOS:")
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    print(f"Total eventos: {total_events}")
    
    if total_events > 0:
        cursor.execute("""
            SELECT title, location, type, magnitude, published_at
            FROM events 
            WHERE location IS NOT NULL 
            ORDER BY published_at DESC 
            LIMIT 3
        """)
        
        events = []
        for row in cursor.fetchall():
            try:
                location = json.loads(row['location']) if row['location'] else None
                if location and len(location) == 2:
                    events.append({
                        'title': row['title'],
                        'lat': float(location[0]),
                        'lng': float(location[1]),
                        'type': row['type'] or 'general',
                        'magnitude': row['magnitude'] or 1,
                        'time': row['published_at']
                    })
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        
        print(f"Eventos con ubicación válida: {len(events)}")
    
    conn.close()
    
    print("\n=== DIAGNÓSTICO COMPLETADO ===")
    print("✅ Base de datos accesible")
    print(f"✅ {total_articles} artículos disponibles")
    print(f"✅ {total_events} eventos disponibles")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()