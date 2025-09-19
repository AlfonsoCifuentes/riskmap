#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test directo de las correcciones aplicadas
"""

from corrected_app import get_corrected_articles_from_db

def test_content_fixes():
    """Test las correcciones directamente"""
    print("🔍 Testing correcciones aplicadas...")
    
    # Obtener artículos con las correcciones
    articles = get_corrected_articles_from_db(limit=5)
    
    if not articles:
        print("❌ No se obtuvieron artículos")
        return False
    
    print(f"✅ Obtenidos {len(articles)} artículos")
    print("\n📊 Verificando correcciones:")
    
    issues_found = 0
    
    for i, article in enumerate(articles):
        print(f"\n📰 Artículo {i+1} (ID: {article['id']}):")
        
        # Verificar título
        title = article.get('title', '')
        if '<think>' in title:
            print(f"  ❌ Título contiene <think>: {title[:60]}...")
            issues_found += 1
        else:
            print(f"  ✅ Título limpio: {title[:60]}...")
        
        # Verificar summary
        summary = article.get('summary', '')
        if '<think>' in summary:
            print(f"  ❌ Summary contiene <think>: {summary[:80]}...")
            issues_found += 1
        else:
            print(f"  ✅ Summary limpio: {summary[:80]}...")
        
        # Verificar imagen
        image_url = article.get('image_url', '')
        if 'text=Artículo+de+Noticias' in image_url:
            print(f"  ❌ Placeholder sin arreglar")
            issues_found += 1
        elif 'placeholder.com' in image_url:
            print(f"  ✅ Placeholder corregido: {image_url}")
        else:
            print(f"  ✅ URL de imagen real: {image_url[:50]}...")
    
    print(f"\n📋 Resumen:")
    print(f"  Total artículos: {len(articles)}")
    print(f"  Problemas encontrados: {issues_found}")
    
    if issues_found == 0:
        print(f"\n🎉 ¡TODAS LAS CORRECCIONES APLICADAS EXITOSAMENTE!")
        print(f"✅ No hay contenido <think> visible")
        print(f"✅ Placeholders de imagen corregidos")
        print(f"✅ Frontend debería mostrar contenido limpio")
        return True
    else:
        print(f"\n⚠️ Algunos problemas aún presentes")
        return False

if __name__ == "__main__":
    test_content_fixes()