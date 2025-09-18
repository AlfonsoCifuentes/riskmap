#!/usr/bin/env python3
"""
Script de diagnóstico para verificar qué datos se están enviando al mosaico.
Esto nos ayudará a identificar por qué aparecen textos largos en lugar del título.
"""

import requests
import json

def diagnose_mosaic_data():
    """Verifica qué datos están llegando al endpoint del mosaico."""

    print("🔍 DIAGNÓSTICO DE DATOS DEL MOSAICO")
    print("=" * 50)

    try:
        # Verificar endpoint de artículos
        response = requests.get('http://localhost:5001/api/articles', timeout=10)
        if response.status_code == 200:
            articles = response.json()

            print(f"✅ Recibidos {len(articles)} artículos")
            print()

            # Analizar primeros 5 artículos
            for i, article in enumerate(articles[:5]):
                print(f"📄 Artículo {i+1}:")
                print(f"   ID: {article.get('id', 'N/A')}")
                print(f"   Título: {article.get('title', 'N/A')[:80]}{'...' if len(str(article.get('title', ''))) > 80 else ''}")

                # Verificar campos problemáticos
                summary = article.get('summary', '')
                auto_summary = article.get('auto_generated_summary', '')

                if summary and len(summary) > 100:
                    print(f"   ⚠️  SUMMARY LARGO ({len(summary)} chars): {summary[:100]}...")
                else:
                    print(f"   ✅ Summary: {'Presente' if summary else 'Ausente'}")

                if auto_summary and len(auto_summary) > 100:
                    print(f"   ❌ AUTO_SUMMARY LARGO ({len(auto_summary)} chars): {auto_summary[:100]}...")
                else:
                    print(f"   ✅ Auto-summary: {'Presente' if auto_summary else 'Ausente'}")

                print(f"   Risk Level: {article.get('risk_level', 'N/A')}")
                print(f"   Image: {article.get('image', 'N/A')[:50]}{'...' if len(str(article.get('image', ''))) > 50 else ''}")
                print()

        else:
            print(f"❌ Error en endpoint: {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que el servidor esté ejecutándose en http://localhost:5001")

    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def check_backend_logic():
    """Verifica la lógica del backend para asegurar que solo envíe títulos."""

    print("\n🔧 VERIFICACIÓN DE LÓGICA DEL BACKEND")
    print("=" * 50)

    print("✅ El backend debería enviar SOLO:")
    print("   - title: El título de la noticia")
    print("   - image: URL de la imagen")
    print("   - risk_level: Nivel de riesgo")
    print("   - id: ID del artículo")
    print("   - original_url: URL original")
    print()
    print("❌ NO debería enviar:")
    print("   - auto_generated_summary (largos textos de resumen)")
    print("   - summary (si es muy largo)")
    print("   - content (contenido completo)")
    print()
    print("🎯 El frontend debería mostrar SOLO el título en el mosaico")

if __name__ == "__main__":
    diagnose_mosaic_data()
    check_backend_logic()

    print("\n" + "=" * 50)
    print("💡 SI ENCUENTRAS TEXTOS LARGOS:")
    print("1. Verifica que el backend NO esté enviando auto_generated_summary")
    print("2. Verifica que el frontend esté usando article.title, no article.summary")
    print("3. Recarga la página con Ctrl+F5")
    print("=" * 50)