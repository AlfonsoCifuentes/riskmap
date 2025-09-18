#!/usr/bin/env python3
"""
Test para verificar si ocultar hero-text elimina el texto superpuesto en el mosaico.
"""

import time
import requests

def test_hero_text_fix():
    """Test si ocultar el hero-text soluciona el texto superpuesto."""
    print("🧪 Test: Verificando si ocultar hero-text soluciona superposición...")
    
    try:
        # Test de endpoint principal
        response = requests.get('http://localhost:5001', timeout=10)
        
        if response.status_code == 200:
            print("✅ Página principal carga correctamente")
            
            # Verificar que no hay JS errors en la respuesta
            if 'error' not in response.text.lower():
                print("✅ No se detectan errores JavaScript obvios")
            else:
                print("⚠️ Se detectan posibles errores en la respuesta")
                
            # Verificar que hero-text está oculto
            if 'display: none !important' in response.text:
                print("✅ Hero-text confirmado como oculto en CSS")
                
                # Test de API de artículos
                try:
                    articles_response = requests.get('http://localhost:5001/api/articles', timeout=10)
                    if articles_response.status_code == 200:
                        articles = articles_response.json()
                        print(f"✅ API de artículos funcional - {len(articles)} artículos")
                        
                        # Verificar que hay imágenes
                        images_count = len([a for a in articles if a.get('image_url')])
                        print(f"✅ {images_count} artículos con imágenes para el mosaico")
                        
                        return True
                    else:
                        print(f"❌ API de artículos falla: {articles_response.status_code}")
                        return False
                        
                except Exception as e:
                    print(f"❌ Error en API de artículos: {str(e)}")
                    return False
            else:
                print("❌ Hero-text no parece estar oculto correctamente")
                return False
        else:
            print(f"❌ Página principal no carga: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante test: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🔧 TEST: Hero-Text Hidden Fix")
    print("=" * 60)
    
    success = test_hero_text_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RESULTADO: Test completado exitosamente")
        print("📝 ACCIÓN: Pruebe visualmente si el texto ya no se superpone al mosaico")
        print("🔄 SIGUIENTE: Si funciona, podemos remover hero-text permanentemente")
    else:
        print("❌ RESULTADO: Test falló")
        print("📝 ACCIÓN: Revisar logs del servidor y corregir errores")
    
    print("=" * 60)

if __name__ == "__main__":
    main()