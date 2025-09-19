#!/usr/bin/env python3
"""
Script para verificar exactamente qué datos están llegando del backend
y por qué aparecen textos largos en lugar de títulos.
"""

import requests
import json

def check_backend_data():
    """Verifica qué datos está enviando el backend"""

    print("🔍 VERIFICACIÓN DE DATOS DEL BACKEND")
    print("=" * 60)

    try:
        # Hacer petición al endpoint
        response = requests.get('http://localhost:5001/api/articles?limit=5', timeout=10)

        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])

            print(f"✅ Recibidos {len(articles)} artículos del backend")
            print()

            for i, article in enumerate(articles, 1):
                print(f"📄 Artículo {i}:")
                print(f"   ID: {article.get('id', 'N/A')}")

                title = article.get('title', '')
                print(f"   Título ({len(title)} chars): {title[:100]}{'...' if len(title) > 100 else ''}")

                # Verificar campos problemáticos
                summary = article.get('summary', '')
                content = article.get('content', '')
                auto_summary = article.get('auto_generated_summary', '')

                if summary:
                    print(f"   ⚠️  SUMMARY ({len(summary)} chars): {summary[:80]}...")
                if content:
                    print(f"   ❌ CONTENT ({len(content)} chars): {content[:80]}...")
                if auto_summary:
                    print(f"   ❌ AUTO_SUMMARY ({len(auto_summary)} chars): {auto_summary[:80]}...")

                print(f"   Image: {article.get('image', 'N/A')[:50]}...")
                print(f"   Risk Level: {article.get('risk_level', 'N/A')}")
                print()

                # Verificar si el título contiene el contenido largo
                if title and len(title) > 200:
                    print(f"   🚨 PROBLEMA: El campo 'title' contiene {len(title)} caracteres!")
                    print(f"      Esto sugiere que el backend está enviando contenido en lugar de título")
                    print()

        else:
            print(f"❌ Error en endpoint: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de que el servidor esté ejecutándose")

def check_database_content():
    """Verifica el contenido real de la base de datos"""

    print("\n💾 VERIFICACIÓN DE BASE DE DATOS")
    print("=" * 60)

    try:
        import sqlite3

        db_path = 'data/geopolitical_intel.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Obtener algunos artículos recientes
        cursor.execute('''
            SELECT id, title, summary, auto_generated_summary, content
            FROM articles
            ORDER BY created_at DESC
            LIMIT 3
        ''')

        rows = cursor.fetchall()

        for row in rows:
            article_id, title, summary, auto_summary, content = row
            print(f"📰 Artículo ID {article_id}:")

            if title:
                print(f"   Título ({len(title)} chars): {title[:100]}{'...' if len(title) > 100 else ''}")
            if summary:
                print(f"   Summary ({len(summary)} chars): {summary[:80]}...")
            if auto_summary:
                print(f"   Auto-summary ({len(auto_summary)} chars): {auto_summary[:80]}...")
            if content:
                print(f"   Content ({len(content)} chars): {content[:80]}...")

            print()

        conn.close()

    except Exception as e:
        print(f"❌ Error al acceder a BD: {e}")

if __name__ == "__main__":
    check_backend_data()
    check_database_content()