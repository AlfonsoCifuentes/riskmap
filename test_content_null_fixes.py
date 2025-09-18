#!/usr/bin/env python3
"""
Test script to verify that articles with NULL content don't cause NoneType errors
"""
import sqlite3
import json
from datetime import datetime

def test_articles_with_null_content():
    """Test the specific articles that were failing with NoneType errors"""
    
    db_path = "./data/geopolitical_intel.db"
    
    # Articles that were failing in the logs
    failing_article_ids = [1117, 1116, 1115, 1114, 1113, 1112, 1111, 1110, 1109, 1108]
    
    print("🔍 VERIFICANDO ARTÍCULOS CON PROBLEMAS DE CONTENIDO NULL")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for article_id in failing_article_ids:
            # Get article data
            cursor.execute("""
                SELECT id, title, content, url, country, language
                FROM articles 
                WHERE id = ?
            """, (article_id,))
            
            article = cursor.fetchone()
            
            if article:
                article_id, title, content, url, country, language = article
                
                print(f"\n📄 ARTÍCULO {article_id}:")
                print(f"   🔗 URL: {url[:50]}..." if url else "   🔗 URL: None")
                print(f"   📰 Título: {title[:50] if title else 'None'}...")
                print(f"   📝 Contenido: {'NULL' if content is None else f'{len(content)} caracteres'}")
                print(f"   🌍 País: {country or 'None'}")
                print(f"   🗣️ Idioma: {language or 'None'}")
                
                # Test the content length check that was failing
                try:
                    # OLD WAY (would fail):
                    # result = content[:300] + '...' if len(content) > 300 else content
                    
                    # NEW WAY (should work):
                    safe_content = (content[:300] + '...' if len(content or '') > 300 else content) or ''
                    print(f"   ✅ Contenido seguro generado: {len(safe_content)} caracteres")
                    
                    # Test article data preparation
                    article_data = {
                        'title': title or '',
                        'content': content or '',
                        'description': ''
                    }
                    print(f"   ✅ Datos del artículo preparados correctamente")
                    
                except Exception as e:
                    print(f"   ❌ ERROR: {e}")
                    
            else:
                print(f"\n📄 ARTÍCULO {article_id}: NO ENCONTRADO")
        
        # Check if these articles have content that could be the issue
        print("\n\n🔍 ANÁLISIS DETALLADO DE CONTENIDOS NULL:")
        print("=" * 60)
        
        cursor.execute("""
            SELECT id, title, 
                   CASE 
                       WHEN content IS NULL THEN 'NULL'
                       WHEN content = '' THEN 'EMPTY'
                       ELSE 'HAS_CONTENT'
                   END as content_status,
                   length(content) as content_length
            FROM articles 
            WHERE id IN ({})
            ORDER BY id DESC
        """.format(','.join(map(str, failing_article_ids))))
        
        results = cursor.fetchall()
        
        null_count = 0
        empty_count = 0
        has_content_count = 0
        
        for article_id, title, content_status, content_length in results:
            print(f"ID {article_id}: {content_status} ({content_length or 0} chars) - {title[:40] if title else 'No title'}...")
            
            if content_status == 'NULL':
                null_count += 1
            elif content_status == 'EMPTY':
                empty_count += 1
            else:
                has_content_count += 1
        
        print(f"\n📊 RESUMEN:")
        print(f"   • Artículos con contenido NULL: {null_count}")
        print(f"   • Artículos con contenido vacío: {empty_count}")
        print(f"   • Artículos con contenido: {has_content_count}")
        
        # Test our fix by simulating the processing
        print(f"\n🧪 PROBANDO NUESTRAS CORRECCIONES:")
        print("=" * 60)
        
        test_cases = [
            None,  # NULL content
            '',    # Empty content  
            'Short content',  # Normal short content
            'This is a long piece of content that should be truncated because it exceeds 300 characters. ' * 10  # Long content
        ]
        
        for i, test_content in enumerate(test_cases):
            try:
                # Our fixed version
                safe_summary = (test_content[:300] + '...' if len(test_content or '') > 300 else test_content) or ''
                print(f"   ✅ Test {i+1} ({'NULL' if test_content is None else 'EMPTY' if test_content == '' else f'{len(test_content)} chars'}): OK - Generated {len(safe_summary)} chars")
            except Exception as e:
                print(f"   ❌ Test {i+1}: FAILED - {e}")
        
        conn.close()
        
        print(f"\n🎉 PRUEBAS COMPLETADAS!")
        print(f"Las correcciones deberían resolver el error 'object of type 'NoneType' has no len()'")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

if __name__ == "__main__":
    test_articles_with_null_content()