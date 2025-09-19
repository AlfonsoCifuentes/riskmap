#!/usr/bin/env python3
"""
Test script to verify clean_article_for_mosaic function
"""

def clean_article_for_mosaic(article):
    """Función auxiliar para limpiar artículos y dejar SOLO campos necesarios para el mosaico"""
    if not article:
        return None

    # SOLO incluir campos explícitamente permitidos para el mosaico
    # EXCLUIR summary, content, description y cualquier otro campo NO LISTADO
    allowed_fields = {'id', 'title', 'image_url', 'risk_level', 'original_url', 'url'}

    cleaned = {}
    for key, value in article.items():
        if key in allowed_fields:
            cleaned[key] = value

    # Asegurar campos mínimos
    cleaned['id'] = article.get('id')
    cleaned['title'] = article.get('title', '')
    cleaned['image_url'] = article.get('image_url') or article.get('image')
    cleaned['risk_level'] = article.get('risk_level') or article.get('risk', 'medium')
    cleaned['original_url'] = article.get('original_url') or article.get('url')

    # FORZAR eliminación de campos no deseados
    forbidden_fields = ['summary', 'content', 'description', 'text', 'auto_generated_summary',
                      'ai_importance', 'conflict_type', 'country', 'location', 'published_at',
                      'region', 'risk_score', 'sentiment_score', 'source']
    for field in forbidden_fields:
        if field in cleaned:
            del cleaned[field]

    return cleaned

# Test article with forbidden fields
test_article = {
    'id': 1,
    'title': 'Test Title',
    'summary': 'This should be removed',
    'content': 'This should also be removed',
    'image_url': 'http://example.com/image.jpg',
    'risk_level': 'high',
    'url': 'http://example.com',
    'ai_importance': 0.8,
    'country': 'Test Country'
}

print("Original article:")
print(f"Keys: {list(test_article.keys())}")
print(f"Summary present: {'summary' in test_article}")
print(f"Content present: {'content' in test_article}")

cleaned = clean_article_for_mosaic(test_article)

print("\nCleaned article:")
print(f"Keys: {list(cleaned.keys())}")
print(f"Summary present: {'summary' in cleaned}")
print(f"Content present: {'content' in cleaned}")
print(f"Title: {cleaned.get('title')}")
print(f"Image URL: {cleaned.get('image_url')}")
print(f"Risk Level: {cleaned.get('risk_level')}")