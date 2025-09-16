#!/usr/bin/env python3
"""
VERIFICACIÓN FINAL: Confirma que solo se muestran noticias geopolíticas con imágenes reales
"""

import requests
import json

def verify_geopolitical_filter():
    print("🔍 VERIFICACIÓN FINAL DEL FILTRO GEOPOLÍTICO")
    print("=" * 60)
    
    try:
        # Test API endpoint
        url = "http://localhost:5001/api/articles"
        response = requests.get(url, params={"limit": 20}, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}: {response.text[:200]}")
            return False
        
        data = response.json()
        articles = data.get('articles', [])
        
        print(f"✅ Conectado exitosamente al servidor")
        print(f"📊 Encontrados: {len(articles)} artículos")
        print(f"📊 Total en DB: {data.get('total', 'unknown')}")
        
        # Analyze articles
        print("\n" + "="*60)
        print("ANÁLISIS DE ARTÍCULOS DEVUELTOS")
        print("="*60)
        
        geopolitical_count = 0
        with_images = 0
        
        for i, article in enumerate(articles):
            title = article.get('title', 'N/A')
            content = article.get('content', '')
            image_url = article.get('image_url', '')
            
            # Check image
            has_real_image = (
                image_url and 
                not any(placeholder in image_url.lower() for placeholder in [
                    'placeholder', 'default', 'no-image', 'missing'
                ]) and
                not image_url.startswith('/static/images/placeholder')
            )
            
            # Simple geopolitical check (keywords)
            geopolitical_keywords = [
                'conflicto', 'guerra', 'militar', 'política', 'gobierno', 'elecciones',
                'diplomacia', 'internacional', 'seguridad', 'defensa', 'crisis',
                'conflict', 'war', 'military', 'politics', 'government', 'elections',
                'diplomacy', 'international', 'security', 'defense', 'crisis'
            ]
            
            is_geopolitical = any(
                keyword.lower() in (title + ' ' + content).lower() 
                for keyword in geopolitical_keywords
            )
            
            if is_geopolitical:
                geopolitical_count += 1
            if has_real_image:
                with_images += 1
            
            # Print details for first few articles
            if i < 5:
                print(f"\n{i+1}. {title[:70]}{'...' if len(title) > 70 else ''}")
                print(f"   🖼️  Imagen: {'✅ Sí' if has_real_image else '❌ No'} ({image_url[:50] if image_url else 'Sin imagen'})")
                print(f"   🌍 Geopolítico: {'✅ Sí' if is_geopolitical else '❌ No'}")
        
        # Summary
        print("\n" + "="*60)
        print("RESUMEN DE VERIFICACIÓN")
        print("="*60)
        print(f"📰 Total artículos analizados: {len(articles)}")
        print(f"🖼️  Con imágenes reales: {with_images}/{len(articles)} ({100*with_images/len(articles):.1f}%)")
        print(f"🌍 Contenido geopolítico: {geopolitical_count}/{len(articles)} ({100*geopolitical_count/len(articles):.1f}%)")
        
        # Determine success
        success = (with_images == len(articles) and geopolitical_count >= len(articles) * 0.8)
        
        if success:
            print(f"\n🎉 ÉXITO: El filtro funciona correctamente")
            print("✅ Todas las noticias tienen imágenes reales")
            print("✅ La mayoría del contenido es geopolítico")
        else:
            print(f"\n⚠️  ATENCIÓN: Posibles mejoras necesarias")
            if with_images < len(articles):
                print(f"❌ {len(articles) - with_images} artículos sin imágenes reales")
            if geopolitical_count < len(articles) * 0.8:
                print(f"❌ Pocos artículos geopolíticos detectados")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_geopolitical_filter()
    exit(0 if success else 1)