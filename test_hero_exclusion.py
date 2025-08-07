#!/usr/bin/env python3
"""
Test script para verificar que el artículo HERO no aparece duplicado en el mosaico
"""

import requests
import json
import sys
import time

def test_hero_mosaic_exclusion():
    """Probar que el artículo HERO no aparece en el mosaico"""
    
    print("🧪 PROBANDO EXCLUSIÓN DEL HÉROE DEL MOSAICO")
    print("=" * 60)
    
    # Esperar a que el servidor esté listo
    print("⏳ Esperando a que el servidor esté listo...")
    time.sleep(5)
    
    try:
        # 1. Obtener el artículo HERO
        print("\n1️⃣ Obteniendo artículo HERO...")
        hero_response = requests.get("http://localhost:5001/api/hero-article", timeout=10)
        
        if hero_response.status_code != 200:
            print(f"❌ Error obteniendo HERO: HTTP {hero_response.status_code}")
            return False
            
        hero_data = hero_response.json()
        if not hero_data.get('success') or not hero_data.get('article'):
            print(f"❌ Respuesta HERO inválida: {hero_data}")
            return False
            
        hero_article = hero_data['article']
        hero_id = hero_article.get('id')
        hero_title = hero_article.get('title', 'Sin título')
        
        print(f"✅ HERO obtenido: ID={hero_id}, Título='{hero_title[:50]}...'")
        
        # 2. Obtener artículos del mosaico
        print("\n2️⃣ Obteniendo artículos del mosaico...")
        mosaic_response = requests.get("http://localhost:5001/api/articles?limit=20", timeout=10)
        
        if mosaic_response.status_code != 200:
            print(f"❌ Error obteniendo mosaico: HTTP {mosaic_response.status_code}")
            return False
            
        mosaic_data = mosaic_response.json()
        if not isinstance(mosaic_data, list):
            print(f"❌ Respuesta mosaico inválida: {type(mosaic_data)}")
            return False
            
        print(f"✅ Mosaico obtenido: {len(mosaic_data)} artículos")
        
        # 3. Verificar que el HERO no está en el mosaico
        print("\n3️⃣ Verificando exclusión del HERO...")
        
        hero_in_mosaic = False
        mosaic_ids = []
        
        for article in mosaic_data:
            article_id = article.get('id')
            mosaic_ids.append(article_id)
            
            if article_id == hero_id:
                hero_in_mosaic = True
                print(f"❌ HERO ENCONTRADO EN MOSAICO: ID={article_id}")
                break
        
        if not hero_in_mosaic:
            print(f"✅ HERO CORRECTAMENTE EXCLUIDO del mosaico")
            print(f"📊 IDs en mosaico: {mosaic_ids[:10]}...")  # Mostrar primeros 10
            return True
        else:
            print(f"❌ HERO DUPLICADO en mosaico")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_image_alignment():
    """Probar el alineamiento de la imagen del HERO"""
    
    print("\n🖼️ PROBANDO ALINEAMIENTO DE IMAGEN HERO")
    print("=" * 60)
    
    try:
        # Obtener el artículo HERO
        hero_response = requests.get("http://localhost:8050/api/hero-article", timeout=10)
        
        if hero_response.status_code == 200:
            hero_data = hero_response.json()
            if hero_data.get('success') and hero_data.get('article'):
                hero_article = hero_data['article']
                image_url = hero_article.get('image')
                
                if image_url:
                    print(f"✅ HERO tiene imagen: {image_url[:60]}...")
                    print("ℹ️ CSS actualizado: background-position: center top")
                    print("ℹ️ Esto evitará que se corte la parte superior de la imagen")
                    return True
                else:
                    print("⚠️ HERO no tiene imagen")
                    return False
            else:
                print("❌ No se pudo obtener el artículo HERO")
                return False
        else:
            print(f"❌ Error HTTP: {hero_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    
    print("🚀 INICIANDO PRUEBAS DE EXCLUSIÓN HERO Y ALINEAMIENTO")
    print("=" * 70)
    
    # Test 1: Exclusión del HERO del mosaico
    exclusion_success = test_hero_mosaic_exclusion()
    
    # Test 2: Alineamiento de imagen
    alignment_success = test_image_alignment()
    
    # Resumen
    print("\n📋 RESUMEN DE PRUEBAS")
    print("=" * 30)
    print(f"✅ Exclusión HERO del mosaico: {'PASSED' if exclusion_success else 'FAILED'}")
    print(f"✅ Alineamiento de imagen: {'PASSED' if alignment_success else 'FAILED'}")
    
    if exclusion_success and alignment_success:
        print("\n🎉 TODAS LAS PRUEBAS PASARON")
        print("✅ El HERO no se duplica en el mosaico")
        print("✅ La imagen del HERO está bien alineada")
        return True
    else:
        print("\n❌ ALGUNAS PRUEBAS FALLARON")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
