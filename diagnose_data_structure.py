#!/usr/bin/env python3
"""
Diagnostic script to check what data is actually being returned from the database
and identify where tuples might be coming from.
"""

import sqlite3
import os
import json

def get_database_path():
    """Get database path."""
    return "data/geopolitical_intel.db"

def check_raw_data():
    """Check what raw data looks like from the database."""
    try:
        db_path = get_database_path()
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get a few articles to inspect their structure
        query = """
            SELECT id, title, summary, content, image_url, original_image_url
            FROM articles 
            WHERE geopolitical_relevance = 1
            AND title IS NOT NULL AND title != ''
            LIMIT 3
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        print("🔍 RAW DATABASE DATA:")
        print("=" * 50)
        
        for i, row in enumerate(rows):
            print(f"\nArticle {i+1}:")
            print(f"  ID: {row[0]}")
            print(f"  Title: {repr(row[1])}")
            print(f"  Summary: {repr(row[2])}")
            print(f"  Content: {repr(row[3][:100] if row[3] else None)}...")
            print(f"  Image URL: {repr(row[4])}")
            print(f"  Original Image URL: {repr(row[5])}")
            
            # Check for any tuple-like structures
            for j, field in enumerate(row):
                if isinstance(field, (list, tuple)):
                    print(f"  ⚠️  Field {j} is a {type(field)}: {field}")
        
        return rows
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return None

def test_translation_system():
    """Test the translation system directly."""
    print("\n🔍 TESTING TRANSLATION SYSTEM:")
    print("=" * 50)
    
    try:
        from robust_translation_v3 import UltraRobustTranslationService
        
        # Initialize translation system
        translator = UltraRobustTranslationService()
        
        # Test translation
        test_text = "This is a test message"
        result = translator.translate_text(test_text, target_language='es')
        
        print(f"Input: {test_text}")
        print(f"Result type: {type(result)}")
        print(f"Result value: {result}")
        
        if isinstance(result, tuple):
            print(f"✅ Translation system returns tuple: ({result[0]}, {result[1]})")
            return result[0]  # Return just the translated text
        else:
            print(f"⚠️  Translation system returns: {type(result)}")
            return result
        
    except Exception as e:
        print(f"❌ Error testing translation system: {e}")
        return None

def check_article_processing():
    """Check how articles are processed in the application."""
    print("\n🔍 TESTING ARTICLE PROCESSING:")
    print("=" * 50)
    
    # Simulate the same processing as in app_BUENA.py
    try:
        from robust_translation_v3 import UltraRobustTranslationService
        translator = UltraRobustTranslationService()
        
        # Test article data
        test_article = {
            'id': 1,
            'title': 'Test Article Title',
            'summary': 'Test article summary',
            'content': 'Test article content'
        }
        
        print(f"Original article: {test_article}")
        
        # Test translation like in the app
        try:
            translated_title, _ = translator.translate_text(
                test_article['title'], target_language='es'
            )
            test_article['title'] = translated_title
            
            if test_article.get('summary'):
                translated_summary, _ = translator.translate_text(
                    test_article['summary'], target_language='es'  
                )
                test_article['summary'] = translated_summary
                
            print(f"Processed article: {test_article}")
            
            # Check for tuple structures
            for key, value in test_article.items():
                if isinstance(value, (list, tuple)):
                    print(f"⚠️  {key} is a {type(value)}: {value}")
                elif not isinstance(value, str) and key in ['title', 'summary', 'content']:
                    print(f"⚠️  {key} is not a string: {type(value)} - {value}")
            
        except Exception as translation_error:
            print(f"❌ Translation error: {translation_error}")
        
    except Exception as e:
        print(f"❌ Error in article processing test: {e}")

def main():
    """Run comprehensive diagnostic."""
    print("🚀 COMPREHENSIVE DATA DIAGNOSTIC")
    print("=" * 70)
    
    # Check raw database data
    raw_data = check_raw_data()
    
    # Test translation system
    translation_result = test_translation_system()
    
    # Test article processing
    check_article_processing()
    
    print("\n📊 DIAGNOSTIC COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()