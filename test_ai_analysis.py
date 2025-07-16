#!/usr/bin/env python3
"""
Script para probar el análisis de IA mejorado con datos NLP
"""

import requests
import json

def test_enhanced_ai_analysis():
    """Probar el análisis de IA mejorado con NLP"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("=== Probando Análisis de IA Mejorado con NLP ===\n")
    
    try:
        print("Solicitando análisis de IA con datos NLP...")
        response = requests.get(f"{base_url}/api/ai_analysis", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Análisis generado exitosamente:")
            print(f"   NLP Enhanced: {data.get('nlp_enhanced', False)}")
            print(f"   Risk Level: {data.get('risk_level', 'N/A')}")
            
            analysis = data.get('analysis', 'Sin análisis')
            print(f"\n📊 Análisis:")
            print(f"   {analysis[:200]}...")
            
            key_insights = data.get('key_insights', [])
            print(f"\n🔍 Key Insights ({len(key_insights)}):")
            for i, insight in enumerate(key_insights[:3], 1):
                print(f"   {i}. {insight}")
            
            recommendations = data.get('recommendations', [])
            print(f"\n💡 Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. {rec}")
            
            nlp_metrics = data.get('nlp_metrics', {})
            if nlp_metrics:
                print(f"\n🧠 NLP Metrics:")
                print(f"   Risk Levels: {len(nlp_metrics.get('risk_levels', []))} articles")
                print(f"   Sentiment Distribution: {nlp_metrics.get('sentiment_distribution', {})}")
                print(f"   Countries Involved: {len(nlp_metrics.get('countries_involved', set()))}")
                print(f"   Key Entities: {len(nlp_metrics.get('key_entities', []))}")
        else:
            print(f"   Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   Error: {e}")
        
    print("\n=== Prueba completada ===")

if __name__ == "__main__":
    test_enhanced_ai_analysis()
