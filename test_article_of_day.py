"""
Script para probar el flujo completo del artículo del día
"""

import requests
import json

def test_article_of_day():
    """Prueba el endpoint del artículo del día y verifica la respuesta"""
    
    print("🧪 PROBANDO ARTÍCULO DEL DÍA")
    print("=" * 50)
    
    try:
        # Hacer request al endpoint
        print("📡 Realizando request a /api/article-of-day...")
        response = requests.get('http://localhost:5000/api/article-of-day')
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ RESPUESTA EXITOSA")
            print("-" * 30)
            print(f"🏷️  Título: {data.get('title', 'NO TITLE')}")
            print(f"⚠️  Riesgo: {data.get('risk_level', 'NO RISK')}")
            print(f"🌍 País: {data.get('country', 'NO COUNTRY')}")
            print(f"🏛️  Fuente: {data.get('source', 'NO SOURCE')}")
            print(f"🌐 Idioma: {data.get('language', 'NO LANGUAGE')}")
            print(f"📅 Fecha: {data.get('created_at', 'NO DATE')}")
            print(f"🔗 URL: {data.get('url', 'NO URL')}")
            print(f"🖼️  Imagen: {data.get('image_url', 'NO IMAGE')}")
            print(f"📝 Contenido: {data.get('content', 'NO CONTENT')[:100]}...")
            
            print("\n🔍 VERIFICANDO CAMPOS REQUERIDOS")
            print("-" * 40)
            
            required_fields = ['title', 'risk_level', 'source', 'language', 'created_at', 'image_url']
            missing_fields = []
            
            for field in required_fields:
                if field not in data or not data[field]:
                    missing_fields.append(field)
                    print(f"❌ {field}: FALTA")
                else:
                    print(f"✅ {field}: OK")
            
            if missing_fields:
                print(f"\n⚠️  CAMPOS FALTANTES: {missing_fields}")
            else:
                print(f"\n🎉 TODOS LOS CAMPOS PRESENTES")
            
            print(f"\n📋 RESPUESTA COMPLETA:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error text: {response.text}")
    
    except Exception as e:
        print(f"💥 EXCEPCIÓN: {e}")

if __name__ == "__main__":
    test_article_of_day()
