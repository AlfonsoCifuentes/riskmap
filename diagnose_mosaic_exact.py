#!/usr/bin/env python3
"""
Script de diagnóstico para verificar exactamente qué se muestra en el mosaico
"""
import requests
import json
import sys

def check_mosaic_exact_content():
    """Verifica exactamente qué contenido se está enviando al frontend"""
    try:
        print("🔍 DIAGNÓSTICO DETALLADO DEL MOSAICO")
        print("=" * 60)

        # Verificar endpoint deduplicado
        print("\n📡 Probando endpoint deduplicado...")
        response = requests.get('http://localhost:5001/api/articles/deduplicated?hours=24', timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('mosaic'):
                print(f"✅ Recibidos {len(data['mosaic'])} artículos deduplicados")

                for i, article in enumerate(data['mosaic'][:3]):  # Revisar primeros 3
                    print(f"\n📰 ARTÍCULO {i+1}:")
                    print(f"   ID: {article.get('id', 'N/A')}")
                    print(f"   Título: '{article.get('title', '')}'")
                    print(f"   Longitud título: {len(article.get('title', ''))}")

                    # Verificar campos que NO deberían estar
                    summary = article.get('summary', '')
                    content = article.get('content', '')
                    description = article.get('description', '')

                    if summary:
                        print(f"   ❌ SUMMARY PRESENTE: '{summary[:50]}...' (LONGITUD: {len(summary)})")
                    else:
                        print("   ✅ Sin summary")

                    if content:
                        print(f"   ❌ CONTENT PRESENTE: '{content[:50]}...' (LONGITUD: {len(content)})")
                    else:
                        print("   ✅ Sin content")

                    if description:
                        print(f"   ❌ DESCRIPTION PRESENTE: '{description[:50]}...' (LONGITUD: {len(description)})")
                    else:
                        print("   ✅ Sin description")

                    # Verificar imagen
                    image = article.get('image_url') or article.get('image', '')
                    if image:
                        print(f"   🖼️  Imagen: {image[:50]}...")
                    else:
                        print("   ❌ Sin imagen")

            else:
                print("❌ Respuesta sin datos válidos")
                print(f"Respuesta completa: {data}")
        else:
            print(f"❌ Error en endpoint deduplicado: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")

        # Verificar endpoint estándar
        print("\n📡 Probando endpoint estándar...")
        response = requests.get('http://localhost:5001/api/articles?limit=3', timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('articles'):
                print(f"✅ Recibidos {len(data['articles'])} artículos estándar")

                for i, article in enumerate(data['articles'][:2]):  # Revisar primeros 2
                    print(f"\n📄 ARTÍCULO ESTÁNDAR {i+1}:")
                    print(f"   Título: '{article.get('title', '')}'")

                    summary = article.get('summary', '')
                    content = article.get('content', '')

                    if summary:
                        print(f"   ❌ SUMMARY: '{summary[:30]}...'")
                    if content:
                        print(f"   ❌ CONTENT: '{content[:30]}...'")

                    if not summary and not content:
                        print("   ✅ Solo título (correcto)")
            else:
                print("❌ Respuesta sin datos válidos")
        else:
            print(f"❌ Error en endpoint estándar: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que el servidor esté ejecutándose en http://localhost:5001")
        return False

    print("\n" + "=" * 60)
    print("📋 RESUMEN:")
    print("- Si ves SUMMARY o CONTENT en la salida, ese es el problema")
    print("- El mosaico debería recibir SOLO título e imagen")
    print("- Cualquier campo adicional se está mostrando como texto superpuesto")

    return True

if __name__ == "__main__":
    success = check_mosaic_exact_content()
    if not success:
        sys.exit(1)