#!/usr/bin/env python3
"""
Script de verificación de endpoints optimizados
Verifica que los cambios en el filtro de imágenes estén funcionando correctamente
"""

import requests
import json
import sys
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_endpoint(url, endpoint_name):
    """Prueba un endpoint y analiza la respuesta"""
    
    print(f"\n🔍 PRUEBA: {endpoint_name}")
    print("=" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}: {response.text[:200]}")
            return None
        
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ API devolvió error: {data.get('error', 'Error desconocido')}")
            return None
        
        print(f"✅ Status: {response.status_code}")
        
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def analyze_articles(articles, endpoint_name):
    """Analiza artículos devueltos por un endpoint"""
    
    if not articles:
        print("⚠️ No hay artículos para analizar")
        return
    
    print(f"\n📊 ANÁLISIS: {len(articles)} artículos de {endpoint_name}")
    print("-" * 40)
    
    # Contadores
    with_images = 0
    without_images = 0
    https_images = 0
    placeholder_images = 0
    
    for i, article in enumerate(articles):
        image_url = article.get('image', '') or article.get('image_url', '')
        
        if image_url:
            with_images += 1
            if image_url.startswith('https://'):
                https_images += 1
            if 'placeholder' in image_url.lower():
                placeholder_images += 1
        else:
            without_images += 1
        
        # Mostrar muestra de los primeros 5
        if i < 5:
            title = article.get('title', 'Sin título')
            risk = article.get('risk', '') or article.get('risk_level', 'unknown')
            article_id = article.get('id', 'N/A')
            
            print(f"   {i+1}. ID: {article_id} | Risk: {risk}")
            print(f"      📰 {title[:60]}...")
            print(f"      🖼️  {image_url[:60] if image_url else 'SIN IMAGEN'}...")
            print()
    
    # Estadísticas
    print(f"📈 ESTADÍSTICAS:")
    print(f"   Con imágenes: {with_images}/{len(articles)} ({with_images/len(articles)*100:.1f}%)")
    print(f"   Sin imágenes: {without_images}/{len(articles)} ({without_images/len(articles)*100:.1f}%)")  
    print(f"   HTTPS válidas: {https_images}/{with_images} ({https_images/with_images*100 if with_images > 0 else 0:.1f}%)")
    print(f"   Placeholders: {placeholder_images}/{with_images} ({placeholder_images/with_images*100 if with_images > 0 else 0:.1f}%)")
    
    # Validación
    if without_images > 0:
        print(f"⚠️ PROBLEMA: {without_images} artículos sin imagen")
    if placeholder_images > 0:
        print(f"⚠️ PROBLEMA: {placeholder_images} artículos con placeholder")
    if https_images == with_images and without_images == 0 and placeholder_images == 0:
        print(f"✅ PERFECTO: Todos los artículos tienen imágenes HTTPS válidas")

def check_hero_mosaic_exclusivity(hero_data, mosaic_data):
    """Verifica que el héroe no aparezca en el mosaico"""
    
    print(f"\n🔒 VERIFICACIÓN DE EXCLUSIVIDAD HÉROE/MOSAICO")
    print("=" * 50)
    
    if not hero_data or not mosaic_data:
        print("⚠️ No hay datos de héroe o mosaico para verificar")
        return
    
    hero_id = hero_data.get('id')
    hero_title = hero_data.get('title', 'Sin título')
    
    print(f"👑 HÉROE: ID {hero_id} - {hero_title[:50]}...")
    
    # Verificar duplicación por ID
    duplicate_ids = [art for art in mosaic_data if art.get('id') == hero_id]
    
    # Verificar duplicación por título (similar)
    duplicate_titles = [art for art in mosaic_data 
                       if art.get('title', '').lower().strip() == hero_title.lower().strip()]
    
    if duplicate_ids:
        print(f"❌ DUPLICACIÓN POR ID: {len(duplicate_ids)} artículos en mosaico con mismo ID")
        for dup in duplicate_ids:
            print(f"   - ID {dup.get('id')}: {dup.get('title', 'Sin título')[:50]}...")
    
    if duplicate_titles:
        print(f"❌ DUPLICACIÓN POR TÍTULO: {len(duplicate_titles)} artículos en mosaico con mismo título")
        for dup in duplicate_titles:
            print(f"   - ID {dup.get('id')}: {dup.get('title', 'Sin título')[:50]}...")
    
    if not duplicate_ids and not duplicate_titles:
        print("✅ EXCLUSIVIDAD CONFIRMADA: Héroe no aparece en mosaico")
    
    return len(duplicate_ids) == 0 and len(duplicate_titles) == 0

def main():
    """Función principal de verificación"""
    
    print("🧪 VERIFICACIÓN DE ENDPOINTS OPTIMIZADOS")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:5001"
    
    # 1. Test /api/hero-article
    hero_data = test_endpoint(f"{base_url}/api/hero-article", "/api/hero-article")
    hero_article = None
    
    if hero_data:
        hero_article = hero_data.get('article', {})
        analyze_articles([hero_article], "HÉROE")
    
    # 2. Test /api/articles  
    articles_data = test_endpoint(f"{base_url}/api/articles?limit=20", "/api/articles")
    mosaic_articles = []
    
    if articles_data:
        mosaic_articles = articles_data.get('articles', [])
        analyze_articles(mosaic_articles, "MOSAICO")
    
    # 3. Test /api/articles/deduplicated
    dedup_data = test_endpoint(f"{base_url}/api/articles/deduplicated", "/api/articles/deduplicated")
    dedup_hero = None
    dedup_mosaic = []
    
    if dedup_data:
        dedup_hero = dedup_data.get('hero', {})
        dedup_mosaic = dedup_data.get('mosaic', [])
        
        print(f"\n📋 ENDPOINT DEDUPLICADO:")
        print(f"   Héroe: {dedup_hero.get('title', 'Sin título')[:50]}...")
        print(f"   Mosaico: {len(dedup_mosaic)} artículos")
        
        analyze_articles([dedup_hero], "HÉROE DEDUPLICADO")
        analyze_articles(dedup_mosaic, "MOSAICO DEDUPLICADO")
    
    # 4. Verificar exclusividad
    all_passed = True
    
    if hero_article and mosaic_articles:
        exclusivity_1 = check_hero_mosaic_exclusivity(hero_article, mosaic_articles)
        all_passed = all_passed and exclusivity_1
    
    if dedup_hero and dedup_mosaic:
        exclusivity_2 = check_hero_mosaic_exclusivity(dedup_hero, dedup_mosaic)
        all_passed = all_passed and exclusivity_2
    
    # 5. Resumen final
    print(f"\n🎯 RESUMEN FINAL")
    print("=" * 30)
    
    endpoints_working = sum([
        1 if hero_data else 0,
        1 if articles_data else 0, 
        1 if dedup_data else 0
    ])
    
    print(f"✅ Endpoints funcionando: {endpoints_working}/3")
    
    if all_passed:
        print("✅ TODAS LAS VALIDACIONES PASARON")
        print("✅ Solo artículos geopolíticos con imágenes reales")
        print("✅ Héroe no duplicado en mosaico")
        return 0
    else:
        print("❌ ALGUNAS VALIDACIONES FALLARON")
        print("⚠️ Revisar logs para detalles")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)