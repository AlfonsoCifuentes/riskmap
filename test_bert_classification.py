"""
Prueba del sistema de clasificación BERT implementado
Verifica el funcionamiento del endpoint /api/analyze-importance
"""

import requests
import json
import time
from datetime import datetime

# Configuración
API_URL = "http://localhost:8050/api/analyze-importance"

# Artículos de prueba con diferentes niveles de importancia/riesgo
test_articles = [
    {
        "title": "Breaking: Nuclear facility attacked in Ukraine, radiation levels rising",
        "content": "A major nuclear facility has been targeted in a missile attack, causing widespread concern about radiation leaks and international security implications.",
        "location": "Ukraine",
        "risk_level": "critical",
        "created_at": datetime.now().isoformat()
    },
    {
        "title": "Local weather update: Sunny skies expected this weekend",
        "content": "The meteorological department forecasts clear skies and moderate temperatures for the upcoming weekend.",
        "location": "New York",
        "risk_level": "low",
        "created_at": datetime.now().isoformat()
    },
    {
        "title": "Military tensions escalate as troops mobilize near Gaza border",
        "content": "Israeli and Palestinian forces are increasing their presence along the Gaza border amid rising tensions and diplomatic failures.",
        "location": "Gaza",
        "risk_level": "high",
        "created_at": datetime.now().isoformat()
    },
    {
        "title": "Economic summit concludes with trade agreements",
        "content": "World leaders have signed several bilateral trade agreements during the economic summit, focusing on post-pandemic recovery.",
        "location": "Geneva",
        "risk_level": "low",
        "created_at": datetime.now().isoformat()
    },
    {
        "title": "Terrorist attack kills dozens in major European capital",
        "content": "A coordinated terrorist attack has struck the heart of a major European city, with casualty numbers still rising and security forces responding.",
        "location": "Paris",
        "risk_level": "critical",
        "created_at": datetime.now().isoformat()
    }
]

def test_bert_analysis():
    """Prueba el sistema de análisis BERT"""
    print("🧠 Iniciando pruebas del sistema de clasificación BERT")
    print("=" * 60)
    
    results = []
    
    for i, article in enumerate(test_articles, 1):
        print(f"\n📰 Prueba {i}: {article['title'][:60]}...")
        print(f"📍 Ubicación: {article['location']}")
        print(f"⚠️  Nivel de riesgo inicial: {article['risk_level']}")
        
        try:
            # Realizar petición al endpoint BERT
            response = requests.post(API_URL, json=article, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Mostrar resultados del análisis
                importance = result.get('importance_factor', 'N/A')
                risk_factor = result.get('risk_factor', 'N/A')
                
                print(f"🎯 Factor de importancia: {importance}%")
                print(f"🔥 Factor de riesgo: {risk_factor}%")
                
                # Información BERT
                bert_analysis = result.get('bert_analysis', {})
                if bert_analysis:
                    negative_sentiment = bert_analysis.get('negative_sentiment', 'N/A')
                    positive_sentiment = bert_analysis.get('positive_sentiment', 'N/A')
                    confidence = bert_analysis.get('confidence', 'N/A')
                    
                    print(f"🧠 Análisis BERT:")
                    print(f"   • Sentimiento negativo: {negative_sentiment}")
                    print(f"   • Sentimiento positivo: {positive_sentiment}")
                    print(f"   • Confianza: {confidence}")
                
                # Información del modelo
                model_info = result.get('model_info', {})
                if model_info:
                    fallback_used = model_info.get('fallback_used', False)
                    print(f"🤖 Modelo usado: {'Fallback local' if fallback_used else 'BERT'}")
                
                results.append({
                    'title': article['title'][:50],
                    'location': article['location'],
                    'initial_risk': article['risk_level'],
                    'importance_factor': importance,
                    'risk_factor': risk_factor,
                    'bert_used': not model_info.get('fallback_used', True),
                    'negative_sentiment': bert_analysis.get('negative_sentiment', 0),
                    'confidence': bert_analysis.get('confidence', 0)
                })
                
                # Verificar que los resultados tengan sentido
                if article['risk_level'] == 'critical' and importance < 70:
                    print("⚠️  ADVERTENCIA: Artículo crítico con importancia baja")
                elif article['risk_level'] == 'low' and importance > 80:
                    print("⚠️  ADVERTENCIA: Artículo de bajo riesgo con importancia alta")
                else:
                    print("✅ Resultado parece coherente")
                    
            else:
                print(f"❌ Error en la petición: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
        
        # Pausa entre peticiones
        time.sleep(1)
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    if results:
        bert_count = sum(1 for r in results if r['bert_used'])
        fallback_count = len(results) - bert_count
        
        print(f"🧠 Análisis BERT exitosos: {bert_count}/{len(results)}")
        print(f"🔄 Fallbacks utilizados: {fallback_count}/{len(results)}")
        
        avg_importance = sum(r['importance_factor'] for r in results if isinstance(r['importance_factor'], (int, float))) / len(results)
        print(f"📈 Importancia promedio: {avg_importance:.1f}%")
        
        # Top 3 artículos por importancia
        sorted_results = sorted(results, key=lambda x: x['importance_factor'] if isinstance(x['importance_factor'], (int, float)) else 0, reverse=True)
        
        print(f"\n🏆 TOP 3 ARTÍCULOS MÁS IMPORTANTES:")
        for i, result in enumerate(sorted_results[:3], 1):
            print(f"   {i}. {result['title']} - {result['importance_factor']}%")
        
        print(f"\n📍 DISTRIBUCIÓN POR UBICACIÓN:")
        location_counts = {}
        for result in results:
            location = result['location']
            if location not in location_counts:
                location_counts[location] = []
            location_counts[location].append(result['importance_factor'])
        
        for location, importances in location_counts.items():
            valid_importances = [i for i in importances if isinstance(i, (int, float))]
            if valid_importances:
                avg_loc_importance = sum(valid_importances) / len(valid_importances)
                print(f"   • {location}: {avg_loc_importance:.1f}% promedio")
    
    print("\n✅ Prueba completada")

if __name__ == "__main__":
    print("🔬 Sistema de Pruebas para Clasificación BERT")
    print("Verificando endpoint: " + API_URL)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://localhost:8050/api/dashboard/stats", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor Flask detectado y funcionando")
            test_bert_analysis()
        else:
            print("❌ Servidor Flask no responde correctamente")
    except requests.exceptions.RequestException:
        print("❌ No se puede conectar al servidor Flask")
        print("   Asegúrate de que esté ejecutándose en http://localhost:8050")
