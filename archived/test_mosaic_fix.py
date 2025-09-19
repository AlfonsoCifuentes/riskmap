#!/usr/bin/env python3
"""
Script para verificar que el mosaico funciona correctamente
"""
import requests
import json
import time

def test_mosaic():
    """Prueba que el mosaico muestre solo títulos"""
    try:
        print("🔍 Probando mosaico...")

        # Esperar a que el servidor esté listo
        time.sleep(2)

        # Probar endpoint deduplicado
        response = requests.get('http://localhost:5001/api/articles/deduplicated?hours=24', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('mosaic'):
                articles = data['mosaic'][:3]  # Primeros 3 artículos
                print("✅ Artículos obtenidos:")
                for i, article in enumerate(articles):
                    title = article.get('title', '')
                    print(f"  {i+1}. Título: {title[:60]}{'...' if len(title) > 60 else ''}")
                    if article.get('content'):
                        print(f"     ⚠️  TIENE CONTENIDO: {article['content'][:30]}...")
                    if article.get('summary'):
                        print(f"     ⚠️  TIENE SUMMARY: {article['summary'][:30]}...")
                    if not article.get('content') and not article.get('summary'):
                        print("     ✅ Solo título")
                return True
            else:
                print("❌ No hay artículos en el mosaico")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 PRUEBA DEL MOSAICO")
    print("=" * 40)
    if test_mosaic():
        print("\n✅ Prueba completada - revisa el navegador")
        print("💡 Si no ves títulos, recarga la página (Ctrl+F5)")
    else:
        print("\n❌ Error en la prueba")