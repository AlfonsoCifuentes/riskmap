#!/usr/bin/env python3
"""
Script de diagnóstico ultra-detallado para verificar exactamente qué se está enviando
"""
import requests
import json
import sys

def check_exact_response():
    """Verifica exactamente qué se está enviando en la respuesta JSON"""
    try:
        print("🔬 DIAGNÓSTICO ULTRA-DETALLADO")
        print("=" * 60)

        # Verificar endpoint deduplicado
        print("\n📡 Analizando respuesta completa del endpoint deduplicado...")
        response = requests.get('http://localhost:5001/api/articles/deduplicated?hours=24', timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta recibida - Status: {response.status_code}")

            if data.get('success'):
                print("✅ Campo 'success': True")

                # Analizar hero
                hero = data.get('hero')
                if hero:
                    print(f"\n🏆 HERO ARTICLE:")
                    print(f"   Tipo: {type(hero)}")
                    print(f"   Campos: {list(hero.keys())}")
                    for key, value in hero.items():
                        if key == 'title':
                            print(f"   {key}: '{value}' (longitud: {len(str(value))})")
                        elif key in ['summary', 'content', 'description']:
                            print(f"   ❌ {key}: '{str(value)[:50]}...' (longitud: {len(str(value))}) - ESTE NO DEBERÍA ESTAR")
                        else:
                            print(f"   {key}: {type(value)} (longitud: {len(str(value))})")
                else:
                    print("ℹ️  No hay hero article")

                # Analizar mosaic
                mosaic = data.get('mosaic', [])
                if mosaic:
                    print(f"\n🎯 MOSAIC ARTICLES: {len(mosaic)}")
                    for i, article in enumerate(mosaic[:3]):  # Solo primeros 3
                        print(f"\n   Artículo {i+1}:")
                        print(f"      Tipo: {type(article)}")
                        print(f"      Campos: {list(article.keys())}")
                        for key, value in article.items():
                            if key == 'title':
                                print(f"      {key}: '{value}' (longitud: {len(str(value))})")
                            elif key in ['summary', 'content', 'description']:
                                print(f"      ❌ {key}: '{str(value)[:50]}...' (longitud: {len(str(value))}) - ESTE NO DEBERÍA ESTAR")
                            else:
                                print(f"      {key}: {type(value)} (longitud: {len(str(value))})")
                else:
                    print("ℹ️  No hay artículos en mosaic")

                # Analizar debug info
                debug = data.get('_debug')
                if debug:
                    print(f"\n🐛 DEBUG INFO:")
                    print(f"   Hero fields: {debug.get('hero_fields', [])}")
                    print(f"   Mosaic sample fields: {debug.get('mosaic_sample_fields', [])}")

            else:
                print("❌ Campo 'success': False")
                print(f"Respuesta completa: {data}")

        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que el servidor esté ejecutándose en http://localhost:5001")
        return False

    print("\n" + "=" * 60)
    print("📋 ANÁLISIS:")
    print("- Si ves campos 'summary', 'content', 'description' en hero o mosaic, ese es el problema")
    print("- El mosaico debe tener SOLO: id, title, image_url, risk_level, original_url")
    print("- Hero debe tener los mismos campos")

    return True

if __name__ == "__main__":
    success = check_exact_response()
    if not success:
        sys.exit(1)