#!/usr/bin/env python3
"""
Script para probar los endpoints del dashboard
"""

import requests
import json

def test_endpoints():
    """Probar los endpoints principales del dashboard"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("=== Probando endpoints del dashboard ===\n")
    
    # 1. Endpoint de artículos de alto riesgo
    try:
        print("1. Artículos de alto riesgo:")
        response = requests.get(f"{base_url}/api/high_risk_articles")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"   Count: {len(articles)} artículos")
            
            for i, article in enumerate(articles[:5], 1):
                title = article.get('title', 'Sin título')[:50]
                risk = article.get('risk_score', 0)
                sentiment = article.get('sentiment_label', 'N/A')
                location = article.get('location', 'N/A')
                print(f"   {i}. [{risk}] {title}... - {sentiment} - {location}")
        else:
            print(f"   Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # 2. Endpoint de datos del dashboard (usando summary)
    try:
        print("2. Datos del dashboard:")
        response = requests.get(f"{base_url}/api/summary")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Estadísticas básicas
            total_articles = data.get('total_articles', 0)
            high_risk = data.get('high_risk_articles', 0)
            avg_risk = data.get('avg_risk_score', 0)
            
            print(f"   Total artículos: {total_articles}")
            print(f"   Alto riesgo: {high_risk}")
            print(f"   Score promedio: {avg_risk}")
            
            # Distribución por idioma
            lang_dist = data.get('language_distribution', {})
            print(f"   Idiomas: {dict(lang_dist)}")
            
        else:
            print(f"   Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # 3. Endpoint de análisis AI
    try:
        print("3. Análisis AI:")
        response = requests.get(f"{base_url}/api/ai_analysis")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            analysis = data.get('analysis', 'Sin análisis')[:200]
            print(f"   Análisis: {analysis}...")
        else:
            print(f"   Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   Error: {e}")
        
    print("\n=== Pruebas completadas ===")

if __name__ == "__main__":
    test_endpoints()
