#!/usr/bin/env python3
"""
Test Translation Service
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from utils.translation import TranslationService

def test_translation():
    """Test the translation service."""
    print("🌐 Testing Translation Service")
    print("=" * 40)
    
    # Create translator
    translator = TranslationService()
    
    # Test cases
    test_cases = [
        {
            'text': 'The government announced new security measures amid rising tensions',
            'source': 'en',
            'target': 'es',
            'expected_keywords': ['gobierno', 'seguridad', 'tensiones']
        },
        {
            'text': 'Military conflict escalates in Eastern Europe',
            'source': 'en',
            'target': 'es',
            'expected_keywords': ['militar', 'conflicto', 'Europa']
        },
        {
            'text': 'Climate change summit addresses global warming',
            'source': 'en',
            'target': 'es',
            'expected_keywords': ['clima', 'cumbre', 'calentamiento']
        },
        {
            'text': 'Economic sanctions imposed on energy sector',
            'source': 'en',
            'target': 'es',
            'expected_keywords': ['económicas', 'sanciones', 'energía']
        }
    ]
    
    print("🔄 Testing translations...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['text'][:50]}...")
        
        try:
            result = translator.translate(
                test_case['text'],
                test_case['source'],
                test_case['target']
            )
            
            print(f"   Original ({test_case['source']}): {test_case['text']}")
            print(f"   Translated ({test_case['target']}): {result}")
            
            # Check if translation contains expected keywords
            found_keywords = []
            for keyword in test_case['expected_keywords']:
                if keyword.lower() in result.lower():
                    found_keywords.append(keyword)
            
            if found_keywords:
                print(f"   ✓ Found keywords: {', '.join(found_keywords)}")
            else:
                print(f"   ⚠ Expected keywords not found: {', '.join(test_case['expected_keywords'])}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n✅ Translation test completed!")

def test_language_pairs():
    """Test different language pairs."""
    print("\n🌍 Testing Language Pairs")
    print("=" * 30)
    
    translator = TranslationService()
    
    test_text = "International crisis requires immediate attention"
    
    language_pairs = [
        ('en', 'es'),  # English to Spanish
        ('en', 'fr'),  # English to French
        ('en', 'de'),  # English to German
        ('en', 'pt'),  # English to Portuguese
    ]
    
    for source, target in language_pairs:
        try:
            result = translator.translate(test_text, source, target)
            print(f"{source} -> {target}: {result}")
        except Exception as e:
            print(f"{source} -> {target}: ❌ Error: {e}")

if __name__ == "__main__":
    test_translation()
    test_language_pairs()