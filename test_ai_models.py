"""
Script de prueba para verificar el funcionamiento de los modelos de IA.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from ai import MultiModelAIClient, generate_ai_analysis

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_models():
    """Prueba todos los modelos disponibles."""
    print("=== PRUEBA DE MODELOS DE IA ===\n")
    
    # Initialize client
    client = MultiModelAIClient()
    
    print(f"Prioridad de modelos: {client.priority}")
    print(f"Modelos disponibles: {client.available_models}")
    print()
    
    # Test data
    test_articles = [
        {
            'title': 'Tensiones geopolíticas en Europa Oriental',
            'content': 'Las recientes tensiones entre países de Europa Oriental han escalado significativamente en las últimas semanas...',
            'risk_level': 'HIGH',
            'conflict_type': 'Political',
            'country': 'Ukraine',
            'region': 'Eastern Europe',
            'source': 'Reuters',
            'language': 'es'
        },
        {
            'title': 'Crisis económica en región asiática',
            'content': 'Los mercados financieros de Asia muestran signos de volatilidad extrema debido a factores geopolíticos...',
            'risk_level': 'MEDIUM',
            'conflict_type': 'Economic',
            'country': 'China',
            'region': 'Asia',
            'source': 'Bloomberg',
            'language': 'es'
        }
    ]
    
    # Test each model individually
    for model_name in client.priority:
        if client.available_models.get(model_name, False):
            print(f"--- Probando {model_name.upper()} ---")
            try:
                # Temporarily set this model as the only one in priority
                original_priority = client.priority.copy()
                client.priority = [model_name]
                
                result = client.generate_analysis(test_articles)
                
                print(f"✅ {model_name}: Éxito")
                print(f"Fuente: {result['source']}")
                print(f"Artículos analizados: {result['articles_analyzed']}")
                print(f"Texto generado: {len(result['analysis'])} caracteres")
                print(f"Extracto: {result['analysis'][:150]}...")
                print()
                
                # Restore original priority
                client.priority = original_priority
                
            except Exception as e:
                print(f"❌ {model_name}: Error - {e}")
                print()
        else:
            print(f"⚠️ {model_name}: No disponible (falta API key)")
            print()
    
    # Test with normal priority (should use first available)
    print("--- Prueba con prioridad normal ---")
    try:
        result = generate_ai_analysis(test_articles)
        print(f"✅ Análisis generado con: {result['source']}")
        print(f"Artículos analizados: {result['articles_analyzed']}")
        print(f"Tiempo: {result['generated_at']}")
        print(f"Extracto: {result['analysis'][:200]}...")
        print()
    except Exception as e:
        print(f"❌ Error en análisis normal: {e}")

if __name__ == "__main__":
    test_models()
