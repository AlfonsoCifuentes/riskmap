#!/usr/bin/env python3
"""
Script para verificar los cambios en el código del mosaico
"""

import re
import os

def verify_mosaic_code():
    """
    Verifica que el código del mosaico solo genere imagen y título
    """
    
    dashboard_file = "src/web/templates/dashboard_BUENO.html"
    
    print("🔍 Verificando código del mosaico...")
    print("=" * 60)
    
    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar las funciones que generan las tarjetas del mosaico
        print("📋 Verificando funciones generadoras de mosaico:")
        print()
        
        # Buscar la primera función (generateMosaicTile)
        pattern1 = r'return `[^`]*mosaic-article[^`]*`'
        matches1 = re.findall(pattern1, content, re.DOTALL)
        
        for i, match in enumerate(matches1):
            print(f"🎯 Función {i+1} - HTML generado:")
            print("-" * 40)
            
            # Verificar que NO contiene indicador CV
            if "${cvIndicator}" in match:
                print("❌ ENCONTRADO: Indicador CV aún presente")
            else:
                print("✅ SIN indicador CV")
            
            # Verificar que SÍ contiene título
            if "mosaic-title" in match:
                print("✅ SÍ contiene título")
            else:
                print("❌ NO contiene título")
            
            # Verificar que NO contiene metadata extra
            metadata_elements = ["mosaic-meta", "mosaic-location", "mosaic-risk-badge", "cv-quality-indicator"]
            found_metadata = []
            
            for element in metadata_elements:
                if element in match:
                    found_metadata.append(element)
            
            if found_metadata:
                print(f"⚠️  Metadata encontrada: {', '.join(found_metadata)}")
            else:
                print("✅ SIN metadata adicional")
            
            print(f"\n📄 Contenido HTML:")
            print(match.strip())
            print()
        
        print("=" * 60)
        
        # Verificar también que las definiciones CSS de CV indicator están pero no se usan
        if "cv-quality-indicator" in content:
            print("💡 CSS del indicador CV presente (pero no se usa en HTML)")
        
        # Contar elementos de mosaico
        mosaic_articles = content.count('class="mosaic-article"')
        print(f"📊 Definiciones de mosaic-article encontradas: {mosaic_articles}")
        
        print("\n✅ Verificación de código completada")
        print("\n📋 ESTADO ESPERADO:")
        print("   ✅ HTML generado sin ${cvIndicator}")
        print("   ✅ HTML con solo mosaic-content y mosaic-title")
        print("   ✅ Sin elementos de metadata en HTML generado")
        
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {dashboard_file}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    verify_mosaic_code()