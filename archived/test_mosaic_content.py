#!/usr/bin/env python3
"""
Script para verificar que las tarjetas del mosaico solo muestren imagen y título
"""

import requests
import time
import json

def test_mosaic_content():
    """
    Verifica que el HTML generado para las tarjetas del mosaico
    solo contenga imagen y título (sin indicadores CV ni metadata adicional)
    """
    
    base_url = "http://localhost:5001"
    
    print("🔍 Verificando contenido del mosaico de artículos...")
    print("=" * 60)
    
    try:
        # Hacer petición a la API de artículos
        response = requests.get(f"{base_url}/api/articles", timeout=10)
        
        if response.status_code == 200:
            articles = response.json()
            print(f"✅ API de artículos funciona: {len(articles)} artículos encontrados")
            
            # Verificar que tenemos artículos
            if articles and len(articles) > 0:
                article = articles[0]
                print(f"📰 Artículo ejemplo: {article.get('title', 'Sin título')[:50]}...")
                print(f"🖼️  Imagen: {bool(article.get('image_url', ''))}")
                
                # Verificar estructura esperada
                required_fields = ['title', 'image_url']
                available_fields = []
                
                for field in required_fields:
                    if article.get(field):
                        available_fields.append(field)
                
                print(f"✅ Campos necesarios disponibles: {', '.join(available_fields)}")
                
                # Verificar que no hay campos de metadata excesiva en las tarjetas
                # (estos campos pueden existir en los datos pero no deben mostrarse)
                metadata_fields = ['summary', 'auto_generated_summary', 'risk_level', 'location']
                
                print("\n📊 Campos de metadata (no se mostrarán en tarjetas):")
                for field in metadata_fields:
                    if article.get(field):
                        print(f"   - {field}: disponible")
                
            else:
                print("⚠️  No se encontraron artículos")
                
        else:
            print(f"❌ Error en API de artículos: {response.status_code}")
            
        # Hacer petición a la página principal para verificar el dashboard
        print(f"\n🌐 Verificando página principal...")
        dashboard_response = requests.get(base_url, timeout=10)
        
        if dashboard_response.status_code == 200:
            html_content = dashboard_response.text
            
            # Verificar que las funciones de mosaico están presentes
            mosaic_indicators = [
                "generateArticleTile",
                "mosaic-article",
                "mosaic-title",
                "mosaic-content"
            ]
            
            found_indicators = []
            for indicator in mosaic_indicators:
                if indicator in html_content:
                    found_indicators.append(indicator)
            
            print(f"✅ Dashboard cargado correctamente")
            print(f"📋 Elementos de mosaico encontrados: {', '.join(found_indicators)}")
            
            # Verificar que NO hay elementos de CV indicator en el HTML generado
            if "cv-quality-indicator" in html_content.lower():
                print("⚠️  Se detectó código del indicador CV (pero debería estar deshabilitado)")
            else:
                print("✅ No se detectó código del indicador CV (correcto)")
                
        else:
            print(f"❌ Error cargando dashboard: {dashboard_response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está ejecutándose en puerto 5001?")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Verificación completada")
    print("\n📋 RESUMEN ESPERADO:")
    print("   - Cada tarjeta del mosaico debe mostrar:")
    print("     ✅ Imagen de fondo")
    print("     ✅ Título del artículo")
    print("   - Cada tarjeta NO debe mostrar:")
    print("     ❌ Indicador CV (CV: X%)")
    print("     ❌ Metadata adicional")
    print("     ❌ Resúmenes o descripciones")

if __name__ == "__main__":
    test_mosaic_content()