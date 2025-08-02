#!/usr/bin/env python3
"""
Script para analizar una imagen específica y mostrar los resultados completos
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Importar patch inmediatamente
try:
    import ml_dtypes_patch
    print("🔧 Patch ml_dtypes aplicado correctamente")
except ImportError as e:
    print(f"⚠️ No se pudo cargar patch ml_dtypes: {e}")

from src.vision.image_analysis import analyze_article_image
import json

def test_single_image():
    """Probar análisis de una sola imagen local"""
    
    # Usar una imagen local específica
    image_url = "static/images/articles/article_1798_social_1754095698.jpg"
    title = "Test: Análisis de imagen local"
    
    print(f"🔍 Analizando imagen de prueba: {image_url}")
    print(f"📝 Título: {title}")
    
    # Realizar análisis
    result = analyze_article_image(image_url, title)
    
    if result and 'error' not in result:
        print("\n✅ Análisis completado exitosamente!")
        
        # Mostrar resultado completo en formato JSON legible
        print("\n📊 RESULTADO COMPLETO:")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Extractos clave
        print("\n🎯 EXTRACTOS CLAVE:")
        print("=" * 40)
        
        dimensions = result.get('dimensions', {})
        print(f"📐 Dimensiones: {dimensions.get('width')}x{dimensions.get('height')}")
        
        quality = result.get('quality_score', 0)
        print(f"⭐ Calidad: {quality:.3f}")
        
        interest_areas = result.get('interest_areas', [])
        print(f"👁️ Áreas de interés: {len(interest_areas)}")
        
        positioning = result.get('positioning_recommendation', {})
        print(f"🎪 Posición mosaico: {positioning.get('mosaic_position', 'N/A')}")
        print(f"📍 Punto focal: {positioning.get('focal_point', 'N/A')}")
        print(f"📏 Tamaño recomendado: {positioning.get('size_recommendation', 'N/A')}")
        print(f"🎯 Confianza: {positioning.get('confidence', 'N/A')}")
        print(f"💭 Razón: {positioning.get('reasoning', 'N/A')}")
        
    else:
        print(f"❌ Error en análisis: {result}")

if __name__ == "__main__":
    test_single_image()
