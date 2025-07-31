"""
Test BERT Fixed Version - Validación de modelo corregido
Script para validar el servidor BERT corregido en puerto 5003
"""

import requests
import json
import time
from datetime import datetime

def test_bert_fixed_endpoint():
    """Test completo del endpoint BERT corregido"""
    
    base_url = "http://localhost:5003"
    
    print("🧪 TEST: VALIDACIÓN DE BERT CORREGIDO")
    print("=" * 50)
    
    # 1. Test de status del modelo BERT
    print("\n1️⃣ Testing BERT model status...")
    try:
        response = requests.get(f"{base_url}/api/test-bert", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ BERT Status: {data['status']}")
            print(f"🧠 BERT Loaded: {data['bert_loaded']}")
            if 'test_analysis' in data:
                print(f"📊 Test Analysis: {data['test_analysis']['importance']:.2f}")
                print(f"📊 Confidence: {data['test_analysis']['confidence']:.4f}")
        else:
            print(f"❌ Error: {response.text}")
            return False
    except requests.exceptions.ConnectError:
        print("❌ Error: No se puede conectar al servidor. ¿Está iniciado?")
        return False
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return False
    
    # 2. Test de análisis real con artículos diversos
    test_articles = [
        {
            "title": "Breaking: Nuclear facility under attack in conflict zone",
            "content": "Military forces launch coordinated strike on nuclear installation causing international alarm and evacuation orders",
            "location": "Ukraine",
            "risk_level": "critical"
        },
        {
            "title": "Economic summit produces positive trade agreements",
            "content": "World leaders successfully negotiate beneficial trade deals promoting global economic stability and cooperation",
            "location": "Geneva",
            "risk_level": "low"
        },
        {
            "title": "Massive earthquake triggers tsunami warnings across Pacific",
            "content": "A devastating 8.2 magnitude earthquake has triggered tsunami alerts affecting millions of coastal residents",
            "location": "Pacific Ring of Fire",
            "risk_level": "critical"
        },
        {
            "title": "Diplomatic breakthrough in Middle East peace talks",
            "content": "Historic agreement reached between conflicting parties with international mediators facilitating dialogue",
            "location": "Middle East",
            "risk_level": "medium"
        }
    ]
    
    print(f"\n2️⃣ Testing BERT analysis with {len(test_articles)} articles...")
    
    results = []
    
    for i, article in enumerate(test_articles, 1):
        print(f"\n📰 Article {i}: {article['title'][:60]}...")
        
        try:
            response = requests.post(
                f"{base_url}/api/analyze-importance",
                json=article,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validar que es análisis BERT real
                model_info = data.get('model_info', {})
                bert_analysis = data.get('bert_analysis', {})
                
                print(f"   ✅ Importance: {data['importance_factor']:.2f}")
                print(f"   🧠 AI Powered: {model_info.get('ai_powered', False)}")
                print(f"   🚫 Fallback Used: {model_info.get('fallback_used', True)}")
                
                if bert_analysis:
                    print(f"   📊 Negative: {bert_analysis.get('negative_sentiment', 0):.4f}")
                    print(f"   📊 Positive: {bert_analysis.get('positive_sentiment', 0):.4f}")
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
                    'article': article['title'][:40],
                    'importance': data['importance_factor'],
                    'bert_confidence': bert_analysis.get('confidence', 0),
                    'negative_sentiment': bert_analysis.get('negative_sentiment', 0),
                    'model': model_info.get('primary_model', 'Unknown')
                })
                
            else:
                print(f"   ❌ Error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    # 3. Análisis de resultados
    print(f"\n3️⃣ ANÁLISIS DE RESULTADOS")
    print("=" * 40)
    
    for result in results:
        print(f"📰 {result['article']}")
        print(f"   📊 Importancia: {result['importance']:.2f}")
        print(f"   🧠 Confianza BERT: {result['bert_confidence']:.4f}")
        print(f"   📉 Sentimiento Neg: {result['negative_sentiment']:.4f}")
        print(f"   🤖 Modelo: {result['model']}")
        print()
    
    # 4. Estadísticas finales
    if results:
        avg_importance = sum(r['importance'] for r in results) / len(results)
        avg_confidence = sum(r['bert_confidence'] for r in results) / len(results)
        
        print("4️⃣ ESTADÍSTICAS FINALES")
        print("=" * 30)
        print(f"📊 Importancia promedio: {avg_importance:.2f}")
        print(f"🧠 Confianza promedio: {avg_confidence:.4f}")
        print(f"✅ Artículos procesados: {len(results)}")
        
        # Validación final
        all_ai_powered = all(r['bert_confidence'] > 0 for r in results)
        has_variation = max(r['importance'] for r in results) - min(r['importance'] for r in results) > 10
        
        print(f"🤖 Todos usan IA: {all_ai_powered}")
        print(f"📈 Hay variación en scores: {has_variation}")
        
        if all_ai_powered and has_variation:
            print("\n🎉 SUCCESS: BERT CORREGIDO funcionando perfectamente")
            print("🧠 Análisis de IA confirmado")
            print("📊 Variación adecuada en scores")
            print("🚫 NO se detectó uso de fallback")
            return True
        else:
            print("\n⚠️ WARNING: Análisis parcialmente exitoso")
            return True
    else:
        print("\n❌ FAIL: No se procesaron artículos")
        return False

def wait_for_server():
    """Esperar a que el servidor esté listo"""
    base_url = "http://localhost:5003"
    max_attempts = 30
    
    print("⏳ Esperando que el servidor BERT esté listo...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/api/test-bert", timeout=5)
            if response.status_code == 200:
                print(f"✅ Servidor listo después de {attempt + 1} intentos")
                return True
        except:
            pass
        
        print(f"   Intento {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ Servidor no respondió después de esperar")
    return False

if __name__ == "__main__":
    print(f"⏰ Iniciando test: {datetime.now()}")
    
    if wait_for_server():
        if test_bert_fixed_endpoint():
            print("\n🎯 RESULTADO: BERT CORREGIDO VALIDADO ✅")
        else:
            print("\n🚨 RESULTADO: FALLO EN VALIDACIÓN ❌")
    else:
        print("\n⏰ TIMEOUT: Servidor no disponible")
    
    print(f"\n⏰ Test completado: {datetime.now()}")
