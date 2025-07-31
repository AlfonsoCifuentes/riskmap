import requests
import json

def test_endpoint():
    url = "http://127.0.0.1:5003/api/generate-ai-analysis"
    
    payload = {
        "articles": [
            {
                "title": "Test geopolitical analysis",
                "content": "This is a test article for geopolitical analysis",
                "location": "Global",
                "risk_level": "medium",
                "importance": 75
            }
        ],
        "analysis_type": "geopolitical_journalistic",
        "language": "spanish"
    }
    
    try:
        print("🧪 Probando endpoint de análisis geopolítico...")
        print(f"📡 URL: {url}")
        
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ ¡Análisis generado exitosamente!")
            print(f"📰 Título: {data.get('title', 'N/A')}")
            print(f"📝 Subtítulo: {data.get('subtitle', 'N/A')}")
            print(f"📊 Fuentes: {data.get('sources_count', 'N/A')}")
            
            content = data.get('content', '')
            if content:
                print(f"📄 Contenido generado: {len(content)} caracteres")
                print(f"🔍 Preview: {content[:200]}...")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📝 Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_endpoint()
