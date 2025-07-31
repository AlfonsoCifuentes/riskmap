"""
Test BERT Real Analysis - Validación de modelo real
Script para garantizar que solo se usa BERT, NO fallback
"""

import requests
import json
import time
from datetime import datetime

def test_bert_endpoint():
    """Test completo del endpoint BERT real"""
    
    base_url = "http://localhost:5002"
    
    print("🧪 TEST: VALIDACIÓN DE BERT REAL")
    print("=" * 50)
    
    # 1. Test de status del modelo BERT
    print("\n1️⃣ Testing BERT model status...")
    try:
        response = requests.get(f"{base_url}/api/test-bert", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ BERT Status: {data['status']}")
            print(f"🧠 BERT Loaded: {data['bert_loaded']}")
            if 'test_analysis' in data:
                print(f"📊 Test Analysis: {data['test_analysis']['importance']:.2f}")
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return False
    
    # 2. Test de análisis real con artículos políticos
    test_articles = [
        {
            "title": "Military conflict escalates with nuclear threats in Eastern Europe",
            "content": "Military forces have been mobilized amid growing nuclear threats. International observers express extreme concern about potential escalation.",
            "location": "Ukraine",
            "risk_level": "critical"
        },
        {
            "title": "Peaceful diplomatic summit reaches breakthrough agreements",
            "content": "World leaders successfully negotiate trade agreements and cooperation treaties, promoting international stability and economic growth.",
            "location": "Geneva",
            "risk_level": "low"
        },
        {
            "title": "Terrorist attack threatens security in major European capital",
            "content": "A coordinated terrorist attack has struck the heart of a major European city, causing multiple casualties and security alerts.",
            "location": "Paris",
            "risk_level": "critical"
        }
    ]
    
    print(f"\n2️⃣ Testing BERT analysis with {len(test_articles)} articles...")
    
    results = []
    
    for i, article in enumerate(test_articles, 1):
        print(f"\n📰 Article {i}: {article['title'][:50]}...")
        
        try:
            response = requests.post(
                f"{base_url}/api/analyze-importance",
                json=article,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validar que es análisis BERT real
                model_info = data.get('model_info', {})
                bert_analysis = data.get('bert_analysis', {})
                
                print(f"   ✅ Importance: {data['importance_factor']:.2f}")
                print(f"   🧠 Model: {model_info.get('primary_model', 'Unknown')}")
                print(f"   🤖 AI Powered: {model_info.get('ai_powered', False)}")
                print(f"   🚫 Fallback Used: {model_info.get('fallback_used', True)}")
                
                if bert_analysis:
                    print(f"   📊 Negative Sentiment: {bert_analysis.get('negative_sentiment', 0):.4f}")
                    print(f"   📊 Positive Sentiment: {bert_analysis.get('positive_sentiment', 0):.4f}")
                    print(f"   📊 Confidence: {bert_analysis.get('confidence', 0):.4f}")
                
                # VALIDACIÓN CRÍTICA
                if not model_info.get('ai_powered', False):
                    print(f"   ❌ ERROR: No es análisis de IA!")
                    return False
                
                if model_info.get('fallback_used', True):
                    print(f"   ❌ ERROR: Se usó fallback!")
                    return False
                
                if not bert_analysis:
                    print(f"   ❌ ERROR: No hay análisis BERT!")
                    return False
                
                results.append({
                    'article': article['title'][:30],
                    'importance': data['importance_factor'],
                    'bert_confidence': bert_analysis.get('confidence', 0),
                    'model': model_info.get('primary_model', 'Unknown')
                })
                
            else:
                print(f"   ❌ Error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    # 3. Resumen de resultados
    print(f"\n3️⃣ RESUMEN DE ANÁLISIS BERT")
    print("=" * 40)
    
    for result in results:
        print(f"📰 {result['article']}")
        print(f"   Importancia: {result['importance']:.2f}")
        print(f"   Confianza BERT: {result['bert_confidence']:.4f}")
        print(f"   Modelo: {result['model']}")
        print()
    
    # 4. Validación final
    all_ai_powered = all(r['bert_confidence'] > 0 for r in results)
    all_use_bert_model = all('bert' in r['model'].lower() for r in results)
    
    print("4️⃣ VALIDACIÓN FINAL")
    print("=" * 30)
    print(f"✅ Todos usan IA: {all_ai_powered}")
    print(f"✅ Todos usan BERT: {all_use_bert_model}")
    
    if all_ai_powered and all_use_bert_model:
        print("\n🎉 SUCCESS: BERT REAL funcionando correctamente")
        print("🧠 Todos los análisis usan el modelo de IA")
        print("🚫 NO se detectó uso de fallback")
        return True
    else:
        print("\n❌ FAIL: Problemas con análisis BERT")
        return False

if __name__ == "__main__":
    print(f"⏰ Iniciando test: {datetime.now()}")
    
    # Dar tiempo al servidor para iniciar
    print("⏳ Esperando que el servidor BERT esté listo...")
    time.sleep(2)
    
    if test_bert_endpoint():
        print("\n🎯 RESULTADO: BERT REAL VALIDADO ✅")
    else:
        print("\n🚨 RESULTADO: FALLO EN VALIDACIÓN ❌")
    
    print(f"\n⏰ Test completado: {datetime.now()}")
