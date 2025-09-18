#!/usr/bin/env python3
"""
Script de diagnóstico simple para probar el endpoint simplificado
"""
import requests
import json
import time

def test_endpoint():
    """Probar el endpoint simplificado"""
    try:
        print("🔍 Probando endpoint /api/articles/deduplicated...")

        # Hacer la petición
        response = requests.get('http://localhost:5001/api/articles/deduplicated', timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint responde correctamente")
            print(f"📊 Estado: {data.get('success', 'N/A')}")
            print(f"🎯 Artículos en mosaico: {len(data.get('mosaic', []))}")

            # Verificar que no hay campos no deseados
            if 'mosaic' in data:
                for i, article in enumerate(data['mosaic']):
                    print(f"\n📄 Artículo {i+1}:")
                    print(f"   ID: {article.get('id', 'N/A')}")
                    print(f"   Título: {article.get('title', 'N/A')[:50]}...")
                    print(f"   Imagen: {article.get('image_url', 'N/A')}")
                    print(f"   Riesgo: {article.get('risk_level', 'N/A')}")

                    # Verificar campos no deseados
                    unwanted_fields = ['summary', 'content', 'description']
                    found_unwanted = [field for field in unwanted_fields if field in article]
                    if found_unwanted:
                        print(f"   ⚠️  CAMPOS NO DESEADOS ENCONTRADOS: {found_unwanted}")
                    else:
                        print("   ✅ Solo campos permitidos")

            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico del endpoint simplificado...")
    success = test_endpoint()
    if success:
        print("\n🎉 Diagnóstico completado exitosamente")
    else:
        print("\n💥 Diagnóstico falló")