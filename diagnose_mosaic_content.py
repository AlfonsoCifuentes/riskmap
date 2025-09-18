#!/usr/bin/env python3
"""
Script de diagnóstico para verificar que el mosaico solo muestra títulos
"""
import requests
import json
import sys

def check_mosaic_content():
    """Verifica que la API solo devuelva títulos, no contenido adicional"""
    try:
        # Verificar endpoint deduplicado
        response = requests.get('http://localhost:5001/api/articles/deduplicated?hours=24', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('mosaic'):
                print("✅ Verificando artículos deduplicados...")
                for i, article in enumerate(data['mosaic'][:5]):  # Revisar primeros 5
                    title = article.get('title', '')
                    content = article.get('content', '')
                    summary = article.get('summary', '')

                    print(f"Artículo {i+1}:")
                    print(f"  Título: {title[:50]}...")
                    if content:
                        print(f"  ⚠️  CONTENIDO PRESENTE: {content[:50]}...")
                    if summary:
                        print(f"  ⚠️  SUMMARY PRESENTE: {summary[:50]}...")
                    if not content and not summary:
                        print("  ✅ Solo título presente")
                    print()
            else:
                print("❌ No hay datos deduplicados disponibles")
        else:
            print(f"❌ Error en endpoint deduplicado: {response.status_code}")

        # Verificar endpoint estándar
        response = requests.get('http://localhost:5001/api/articles?limit=5', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('articles'):
                print("✅ Verificando artículos estándar...")
                for i, article in enumerate(data['articles'][:3]):  # Revisar primeros 3
                    title = article.get('title', '')
                    content = article.get('content', '')
                    summary = article.get('summary', '')

                    print(f"Artículo {i+1}:")
                    print(f"  Título: {title[:50]}...")
                    if content:
                        print(f"  ❌ CONTENIDO EN API: {content[:30]}...")
                    if summary:
                        print(f"  ❌ SUMMARY EN API: {summary[:30]}...")
                    if not content and not summary:
                        print("  ✅ API correcta - solo título")
                    print()
            else:
                print("❌ No hay datos estándar disponibles")
        else:
            print(f"❌ Error en endpoint estándar: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que el servidor esté ejecutándose en http://localhost:5001")
        return False

    return True

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DEL MOSAICO")
    print("=" * 50)
    success = check_mosaic_content()
    if success:
        print("✅ Diagnóstico completado")
    else:
        print("❌ Error en diagnóstico")
        sys.exit(1)