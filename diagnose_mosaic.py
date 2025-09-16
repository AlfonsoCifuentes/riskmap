#!/usr/bin/env python3
"""
Diagnosticar exactamente qué noticias se están mostrando en el mosaico
"""

import requests
import json

def check_current_articles():
    """Verificar artículos actuales en el mosaico"""
    try:
        response = requests.get("http://localhost:5001/api/articles", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"📰 ARTÍCULOS EN EL MOSAICO ACTUAL: {len(articles)}")
            print("=" * 80)
            
            geopolitical_count = 0
            with_real_images = 0
            non_geopolitical = []
            without_images = []
            
            for i, article in enumerate(articles, 1):
                title = article.get('title', 'Sin título')
                source = article.get('source', 'Sin fuente')
                image_url = article.get('image_url', '')
                
                # Verificar si es geopolítico
                title_lower = title.lower()
                is_geopolitical = any(keyword in title_lower for keyword in [
                    'war', 'conflict', 'military', 'politics', 'government', 'security',
                    'nato', 'russia', 'china', 'israel', 'gaza', 'iran', 'trump', 'biden',
                    'guerra', 'militar', 'política', 'gobierno', 'seguridad'
                ])
                
                # Verificar si tiene imagen real
                has_real_image = image_url and 'placeholder' not in image_url and image_url != ''
                
                # Verificar si es no geopolítico
                is_non_geo = any(keyword in title_lower for keyword in [
                    'sport', 'game', 'football', 'basketball', 'emmy', 'oscar', 'movie',
                    'actor', 'hollywood', 'music', 'celebrity', 'iphone', 'apple', 'anime'
                ])
                
                print(f"\n{i:2}. [{source}] {title[:60]}...")
                
                # Indicadores
                geo_status = "✅ GEO" if is_geopolitical else ("❌ NO-GEO" if is_non_geo else "❓ UNCLEAR")
                img_status = "✅ IMG" if has_real_image else "❌ NO-IMG"
                
                print(f"    {geo_status} | {img_status}")
                
                if has_real_image:
                    print(f"    🖼️  {image_url[:70]}...")
                else:
                    print(f"    🚫 Sin imagen real: {image_url[:70] if image_url else 'Sin URL'}...")
                
                # Contadores
                if is_geopolitical:
                    geopolitical_count += 1
                if has_real_image:
                    with_real_images += 1
                if is_non_geo:
                    non_geopolitical.append(f"{i}. [{source}] {title[:50]}")
                if not has_real_image:
                    without_images.append(f"{i}. [{source}] {title[:50]}")
            
            # Resumen
            print("\n" + "=" * 80)
            print("📊 RESUMEN DEL ANÁLISIS:")
            print(f"   📰 Total artículos: {len(articles)}")
            print(f"   🌐 Geopolíticos: {geopolitical_count}")
            print(f"   🖼️  Con imagen real: {with_real_images}")
            print(f"   ❌ No geopolíticos: {len(non_geopolitical)}")
            print(f"   🚫 Sin imagen: {len(without_images)}")
            
            if non_geopolitical:
                print(f"\n🚨 ARTÍCULOS NO GEOPOLÍTICOS QUE NO DEBERÍAN ESTAR:")
                for item in non_geopolitical:
                    print(f"   {item}")
                    
            if without_images:
                print(f"\n🚨 ARTÍCULOS SIN IMAGEN REAL:")
                for item in without_images:
                    print(f"   {item}")
            
            target_articles = geopolitical_count if geopolitical_count == with_real_images else min(geopolitical_count, with_real_images)
            
            print(f"\n🎯 OBJETIVO: Solo {target_articles} artículos geopolíticos con imagen real")
            print(f"📈 ACTUAL: {len(articles)} artículos (algunos no cumplen criterios)")
            
            if len(non_geopolitical) > 0 or len(without_images) > 0:
                print(f"\n❌ PROBLEMA CONFIRMADO: Filtros no funcionan correctamente")
                return False
            else:
                print(f"\n✅ PERFECTO: Todos los artículos cumplen criterios")
                return True
                
        else:
            print(f"❌ Error API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_current_articles()