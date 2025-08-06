#!/usr/bin/env python3
"""
Test directo de la API de GDELT
"""

import requests
import json
from datetime import datetime, timedelta

def test_gdelt_api():
    """Probar directamente la API de GDELT"""
    try:
        print("🧪 Probando API de GDELT directamente...")
        
        # Parámetros de prueba
        base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        
        params = {
            'query': 'conflict',
            'mode': 'ArtList',
            'maxrecords': 10,
            'format': 'json'
        }
        
        print(f"📡 URL: {base_url}")
        print(f"📊 Parámetros: {params}")
        
        # Hacer request
        response = requests.get(base_url, params=params, timeout=30)
        print(f"📱 Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                articles = data.get('articles', [])
                
                print(f"✅ Respuesta JSON válida")
                print(f"📰 Artículos encontrados: {len(articles)}")
                
                if articles:
                    print("\n🔍 PRIMEROS 3 ARTÍCULOS:")
                    for i, article in enumerate(articles[:3]):
                        print(f"\n  📰 Artículo {i+1}:")
                        print(f"     Título: {article.get('title', 'N/A')[:80]}...")
                        print(f"     URL: {article.get('url', 'N/A')}")
                        print(f"     Fecha: {article.get('seendate', 'N/A')}")
                        print(f"     País: {article.get('sourcecountry', 'N/A')}")
                        print(f"     Domain: {article.get('domain', 'N/A')}")
                        
                        # Verificar si tiene coordenadas
                        lat = article.get('lat')
                        lon = article.get('lon')
                        if lat and lon:
                            print(f"     Coords: ({lat}, {lon})")
                        else:
                            print(f"     Coords: No disponibles")
                else:
                    print("❌ No se encontraron artículos")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error decodificando JSON: {e}")
                print(f"📝 Respuesta raw: {response.text[:500]}...")
                
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"📝 Respuesta: {response.text[:200]}...")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def test_alternative_gdelt_apis():
    """Probar APIs alternativas de GDELT"""
    print("\n🔄 Probando APIs alternativas de GDELT...")
    
    # API alternativa 1: GKG (Global Knowledge Graph)
    try:
        print("\n📡 Probando GDELT GKG API...")
        url = "https://api.gdeltproject.org/api/v2/gkg/gkg"
        params = {
            'query': 'conflict',
            'mode': 'artlist',
            'maxrecords': 5,
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=20)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ GKG API funciona: {len(data.get('articles', []))} artículos")
        
    except Exception as e:
        print(f"   ❌ GKG API error: {e}")
    
    # API alternativa 2: TV API
    try:
        print("\n📺 Probando GDELT TV API...")
        url = "https://api.gdeltproject.org/api/v2/tv/tv"
        params = {
            'query': 'ukraine OR gaza',
            'mode': 'clipgallery',
            'maxrecords': 5,
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=20)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            clips = data.get('clips', [])
            print(f"   ✅ TV API funciona: {len(clips)} clips")
            
            if clips:
                for i, clip in enumerate(clips[:2]):
                    print(f"     📺 Clip {i+1}: {clip.get('show', 'N/A')} - {clip.get('date', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ TV API error: {e}")
    
    # Test con diferentes queries
    print("\n🔍 Probando diferentes queries...")
    queries = ['ukraine', 'gaza', 'war', 'crisis', 'protest']
    
    for query in queries:
        try:
            url = "https://api.gdeltproject.org/api/v2/doc/doc"
            params = {
                'query': query,
                'mode': 'ArtList',
                'maxrecords': 3,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                print(f"   📰 '{query}': {len(articles)} artículos")
            else:
                print(f"   ❌ '{query}': Error {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ '{query}': {e}")

if __name__ == "__main__":
    test_gdelt_api()
    test_alternative_gdelt_apis()
