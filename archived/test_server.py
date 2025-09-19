#!/usr/bin/env python3
"""
Script para probar si el servidor Flask está funcionando
"""

import requests
import time

def test_server():
    """Probar conectividad con el servidor Flask"""
    base_url = "http://127.0.0.1:8050"
    
    endpoints_to_test = [
        "/",
        "/api/hero-article", 
        "/api/articles",
        "/api/statistics"
    ]
    
    print(f"Probando servidor en {base_url}...")
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        try:
            print(f"\nProbando: {url}")
            response = requests.get(url, timeout=5)
            print(f"Status: {response.status_code}")
            
            if endpoint == "/api/hero-article" and response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success'):
                        article = data.get('article', {})
                        print(f"Artículo héroe: {article.get('title', 'Sin título')}")
                        print(f"Ubicación: {article.get('location', 'N/A')}")
                        print(f"Riesgo: {article.get('risk', 'N/A')}")
                except:
                    pass
                    
            elif endpoint == "/api/articles" and response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success'):
                        articles = data.get('articles', [])
                        print(f"Artículos encontrados: {len(articles)}")
                        if articles:
                            print(f"Primer artículo: {articles[0].get('title', 'Sin título')}")
                except:
                    pass
                    
        except requests.exceptions.ConnectionError:
            print(f"Error: No se pudo conectar a {url}")
        except requests.exceptions.Timeout:
            print(f"Error: Timeout al conectar a {url}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_server()
