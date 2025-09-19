#!/usr/bin/env python3
"""
Verificar qué datos está enviando el backend al frontend
"""
import requests
import json

def check_backend_data():
    """Verifica qué datos está enviando el backend"""
    try:
        # Hacer petición al endpoint de artículos
        response = requests.get('http://localhost:5001/api/articles?limit=10')
        response.raise_for_status()

        data = response.json()

        if not data.get('success', False):
            print("❌ Error en la respuesta del API")
            return

        articles = data.get('articles', [])

        print("🔍 VERIFICACIÓN DE DATOS DEL BACKEND:")
        print("=" * 80)

        problematic_articles = []

        for i, article in enumerate(articles, 1):
            print(f"\n📄 Artículo {i}:")
            print(f"🆔 ID: {article.get('id', 'N/A')}")
            print(f"📝 Título: {article.get('title', '')[:100]}{'...' if len(article.get('title', '')) > 100 else ''}")

            # Verificar si hay campos problemáticos
            has_summary = 'summary' in article and article.get('summary')
            has_content = 'content' in article and article.get('content')

            if has_summary:
                summary_len = len(article.get('summary', ''))
                print(f"📋 Summary: {summary_len} caracteres")
                if summary_len > 50:
                    print(f"⚠️  Summary largo: {article.get('summary', '')[:100]}...")
                    problematic_articles.append({
                        'id': article.get('id'),
                        'type': 'summary',
                        'content': article.get('summary', '')[:200]
                    })

            if has_content:
                content_len = len(article.get('content', ''))
                print(f"📄 Content: {content_len} caracteres")
                if content_len > 50:
                    print(f"⚠️  Content largo: {article.get('content', '')[:100]}...")
                    problematic_articles.append({
                        'id': article.get('id'),
                        'type': 'content',
                        'content': article.get('content', '')[:200]
                    })

            # Verificar si el título parece ser contenido
            title = article.get('title', '')
            if len(title) > 150:
                print(f"🚨 TÍTULO SOSPECHOSAMENTE LARGO: {len(title)} caracteres")
                problematic_articles.append({
                    'id': article.get('id'),
                    'type': 'long_title',
                    'content': title[:200]
                })

        print("\n📊 RESUMEN:")
        print(f"📄 Total artículos verificados: {len(articles)}")
        print(f"⚠️  Artículos problemáticos: {len(problematic_articles)}")

        if problematic_articles:
            print("\n🚨 ARTÍCULOS PROBLEMÁTICOS DETECTADOS:")
            for prob in problematic_articles[:5]:  # Mostrar solo los primeros 5
                print(f"🆔 ID {prob['id']} - Tipo: {prob['type']}")
                print(f"📝 Contenido: {prob['content'][:150]}...")
                print("---")

        # Verificar estructura de respuesta
        print("\n🔧 ESTRUCTURA DE RESPUESTA:")
        if articles:
            sample = articles[0]
            print("Campos enviados por el backend:")
            for key in sorted(sample.keys()):
                value = sample[key]
                if isinstance(value, str) and len(value) > 50:
                    print(f"  {key}: {type(value).__name__} ({len(value)} chars)")
                else:
                    print(f"  {key}: {type(value).__name__}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al servidor: {e}")
        print("💡 Asegúrate de que el servidor esté ejecutándose en http://localhost:5001")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    check_backend_data()