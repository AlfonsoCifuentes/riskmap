import requests
import json

def check_api_response():
    """Verificar qué datos está enviando la API"""
    try:
        # Hacer petición a la API
        response = requests.get('http://localhost:5001/api/articles', timeout=10)
        data = response.json()

        print("🔍 VERIFICACIÓN DE DATOS DE LA API:")
        print("=" * 50)

        if 'articles' in data:
            print(f"Total de artículos: {len(data['articles'])}")

            for i, article in enumerate(data['articles'][:5]):  # Revisar primeros 5
                print(f"\n📄 Artículo {i+1}:")
                print(f"  ID: {article.get('id', 'N/A')}")
                print(f"  Título: {article.get('title', 'N/A')[:100]}...")

                # Verificar si hay campos adicionales que no deberían estar
                for key, value in article.items():
                    if key not in ['id', 'title', 'image', 'location', 'country', 'region', 'risk', 'risk_level', 'risk_score', 'source', 'published_at', 'url']:
                        print(f"  ⚠️ Campo adicional: {key} = {str(value)[:100]}...")

                # Buscar textos problemáticos específicos
                all_text = json.dumps(article, ensure_ascii=False).lower()
                problematic_texts = [
                    'aplicación gratuita',
                    'ue advirtió',
                    'akistán',
                    'gratuita'
                ]

                for text in problematic_texts:
                    if text.lower() in all_text:
                        print(f"  ❌ ENCONTRADO TEXTO PROBLEMÁTICO: '{text}'")

        else:
            print("❌ No se encontraron artículos en la respuesta")

    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está ejecutándose app_BUENA.py?")
    except Exception as e:
        print(f"❌ Error al verificar API: {e}")

if __name__ == "__main__":
    check_api_response()