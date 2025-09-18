#!/usr/bin/env python3
"""
Verificación de truncamiento de títulos largos en el backend
"""
import requests
import json

def verify_title_truncation():
    """Verifica que los títulos largos se truncan correctamente"""
    try:
        # Hacer petición al endpoint de artículos
        response = requests.get('http://localhost:5001/api/articles?limit=50')
        response.raise_for_status()

        data = response.json()

        if not data.get('success', False):
            print("❌ Error en la respuesta del API")
            return

        articles = data.get('articles', [])

        print("🔍 VERIFICACIÓN DE TRUNCAMIENTO DE TÍTULOS:")
        print("=" * 80)

        long_titles_found = 0
        total_articles = len(articles)

        for article in articles:
            title = article.get('title', '')
            title_length = len(title)

            if title_length > 80:
                long_titles_found += 1
                print(f"\n⚠️  TÍTULO LARGO ENCONTRADO:")
                print(f"📏 Longitud: {title_length} caracteres")
                print(f"📝 Título: {title}")

                # Verificar si termina con "..."
                if title.endswith('...'):
                    print("✅ Correctamente truncado con '...'")
                else:
                    print("❌ No termina con '...', posible problema")

            elif "..." in title:
                print(f"\n✅ Título truncado encontrado: {title}")

        print("\n📊 RESULTADOS:")
        print(f"📄 Total artículos verificados: {total_articles}")
        print(f"⚠️  Títulos largos (>80 chars): {long_titles_found}")

        if long_titles_found == 0:
            print("✅ ÉXITO: Todos los títulos están dentro del límite de 80 caracteres")
        else:
            print(f"❌ PROBLEMA: {long_titles_found} títulos aún son demasiado largos")

        # Verificar algunos títulos de ejemplo
        print("\n📝 EJEMPLOS DE TÍTULOS:")
        for i, article in enumerate(articles[:5]):
            print(f"{i+1}. {article.get('title', '')[:100]}{'...' if len(article.get('title', '')) > 100 else ''}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al servidor: {e}")
        print("💡 Asegúrate de que el servidor esté ejecutándose en http://localhost:5001")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    verify_title_truncation()