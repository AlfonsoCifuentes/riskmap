#!/usr/bin/env python3
"""
Test Complete Integration - BERT + Groq Dashboard
Prueba completa de la integración del dashboard con BERT y Groq
"""

import requests
import json
import time
from datetime import datetime

def test_server_health():
    """Test if the server is running"""
    try:
        response = requests.get('http://127.0.0.1:5003', timeout=5)
        if response.status_code == 200:
            print("✅ Servidor principal funcionando correctamente")
            return True
        else:
            print(f"❌ Servidor respondió con código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        return False

def test_bert_endpoint():
    """Test BERT analysis endpoint"""
    try:
        print("\n🧠 Probando endpoint BERT...")
        
        test_article = {
            "title": "Crisis militar se intensifica en región estratégica",
            "content": "Las tensiones han escalado significativamente en la zona, con movilización de tropas y declaraciones oficiales que indican posible conflicto armado.",
            "location": "Europa Oriental",
            "risk_level": "high",
            "risk_score": 0.8
        }
        
        response = requests.post(
            'http://127.0.0.1:5003/api/analyze-importance',
            json=test_article,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ BERT análisis exitoso")
            print(f"📊 Factor de importancia: {result.get('importance_factor', 'N/A')}")
            print(f"🧠 Modelo usado: {result.get('bert_analysis', {}).get('model_used', 'N/A')}")
            return True
        else:
            print(f"❌ BERT endpoint falló: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en BERT test: {e}")
        return False

def test_groq_endpoint():
    """Test Groq AI analysis endpoint"""
    try:
        print("\n🤖 Probando endpoint Groq...")
        
        test_articles = [
            {
                "title": "Escalada militar en conflicto internacional",
                "content": "Las tensiones militares han aumentado significativamente en la región",
                "location": "Europa Oriental",
                "risk_score": 0.8
            },
            {
                "title": "Crisis diplomática entre potencias",
                "content": "Las relaciones bilaterales se han deteriorado tras declaraciones oficiales",
                "location": "Asia-Pacífico", 
                "risk_score": 0.7
            }
        ]
        
        response = requests.post(
            'http://127.0.0.1:5003/api/generate-ai-analysis',
            json={
                "articles": test_articles,
                "analysis_type": "geopolitical_journalistic",
                "language": "spanish"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Groq análisis exitoso")
            print(f"📰 Título: {result.get('analysis', {}).get('title', 'N/A')[:60]}...")
            print(f"📊 Artículos analizados: {result.get('analysis', {}).get('sources_count', 'N/A')}")
            print(f"🤖 Modelo: {result.get('analysis', {}).get('ai_model', 'N/A')}")
            return True
        else:
            print(f"❌ Groq endpoint falló: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error en Groq test: {e}")
        return False

def test_dashboard_stats():
    """Test dashboard statistics endpoint"""
    try:
        print("\n📊 Probando estadísticas del dashboard...")
        
        response = requests.get('http://127.0.0.1:5003/api/dashboard/stats', timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Estadísticas obtenidas correctamente")
            print(f"📄 Total artículos: {stats.get('total_articles', 'N/A')}")
            print(f"⚠️  Artículos alto riesgo: {stats.get('high_risk_alerts', 'N/A')}")
            return True
        else:
            print(f"❌ Estadísticas endpoint falló: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en estadísticas test: {e}")
        return False

def main():
    """Run complete integration test"""
    print("🧪 PRUEBA COMPLETA DE INTEGRACIÓN - BERT + GROQ DASHBOARD")
    print("=" * 60)
    print(f"🕐 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Salud del Servidor", test_server_health),
        ("Endpoint BERT", test_bert_endpoint), 
        ("Endpoint Groq", test_groq_endpoint),
        ("Estadísticas Dashboard", test_dashboard_stats)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Ejecutando: {test_name}")
        print("-" * 40)
        
        start_time = time.time()
        success = test_func()
        end_time = time.time()
        
        results.append({
            'test': test_name,
            'success': success,
            'duration': end_time - start_time
        })
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status = "✅ PASÓ" if result['success'] else "❌ FALLÓ"
        duration = f"{result['duration']:.2f}s"
        print(f"{result['test']:.<30} {status} ({duration})")
    
    print(f"\n🎯 Resultado General: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡INTEGRACIÓN COMPLETA EXITOSA!")
        print("🚀 El dashboard está listo para producción")
        print("\n📱 URLs disponibles:")
        print("   🌐 Dashboard: http://127.0.0.1:5003")
        print("   🧠 BERT API: http://127.0.0.1:5003/api/analyze-importance")
        print("   🤖 Groq API: http://127.0.0.1:5003/api/generate-ai-analysis")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar configuración.")
    
    print(f"\n🕐 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
