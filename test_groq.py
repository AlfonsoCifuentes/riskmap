"""Test específico para Groq"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from ai import MultiModelAIClient
from dotenv import load_dotenv
load_dotenv()

def test_groq_specifically():
    """Prueba Groq específicamente."""
    client = MultiModelAIClient()
    
    # Test data
    test_articles = [
        {
            'title': 'Conflicto en región estratégica',
            'content': 'Las tensiones han escalado significativamente...',
            'risk_level': 'HIGH',
            'conflict_type': 'Military',
            'country': 'Ukraine',
            'region': 'Eastern Europe',
            'source': 'Reuters',
            'language': 'es'
        }
    ]
    
    print("=== PRUEBA ESPECÍFICA DE GROQ ===")
    print(f"API Key configurada: {bool(os.getenv('GROQ_API_KEY'))}")
    print(f"Groq disponible: {client.available_models.get('groq', False)}")
    print()
    
    # Force Groq only
    original_priority = client.priority.copy()
    client.priority = ['groq']
    
    try:
        result = client.generate_analysis(test_articles)
        print(f"✅ Groq Result:")
        print(f"Source: {result['source']}")
        print(f"Length: {len(result['analysis'])} characters")
        print(f"Text sample: {result['analysis'][:200]}...")
        
    except Exception as e:
        print(f"❌ Groq Error: {e}")
    
    # Restore priority
    client.priority = original_priority

if __name__ == "__main__":
    test_groq_specifically()
