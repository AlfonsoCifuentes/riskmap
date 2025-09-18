#!/usr/bin/env python3
"""
Script para detectar elementos que puedan estar causando texto superpuesto en el mosaico.
"""

import requests
from bs4 import BeautifulSoup
import re

def analyze_potential_overlays():
    """Analiza elementos que podrían causar superposición de texto."""
    print("🔍 Analizando posibles fuentes de texto superpuesto...")
    
    try:
        response = requests.get('http://localhost:5001', timeout=10)
        if response.status_code != 200:
            print(f"❌ No se puede acceder al sitio: {response.status_code}")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Buscar todos los elementos con posición absoluta o fixed
        positioned_elements = soup.find_all(attrs={"style": re.compile(r"position:\s*(absolute|fixed)")})
        print(f"🎯 Elementos con posición absoluta/fixed: {len(positioned_elements)}")
        
        for elem in positioned_elements[:5]:  # Mostrar los primeros 5
            text_content = elem.get_text(strip=True)[:100]
            if text_content and len(text_content) > 20:
                print(f"   📝 {elem.name}: {text_content}...")
        
        # 2. Buscar elementos con z-index alto
        high_z_elements = soup.find_all(attrs={"style": re.compile(r"z-index:\s*[1-9]\d+")})
        print(f"📊 Elementos con z-index alto: {len(high_z_elements)}")
        
        for elem in high_z_elements[:3]:
            text_content = elem.get_text(strip=True)[:100]
            if text_content:
                print(f"   🔢 {elem.name}: {text_content}...")
        
        # 3. Buscar elementos con clases que contengan "overlay", "modal", "popup"
        overlay_classes = soup.find_all(class_=re.compile(r"(overlay|modal|popup|float|absolute)", re.I))
        print(f"🎭 Elementos con clases de overlay: {len(overlay_classes)}")
        
        for elem in overlay_classes[:3]:
            text_content = elem.get_text(strip=True)[:100]
            if text_content and len(text_content) > 20:
                print(f"   🎪 {elem.name} ({elem.get('class')}): {text_content}...")
        
        # 4. Buscar específicamente elementos que puedan contener contenido de artículos
        article_text_elements = soup.find_all(text=re.compile(r".{50,}", re.DOTALL))
        long_text_elements = [elem for elem in article_text_elements if len(elem.strip()) > 100]
        print(f"📄 Elementos con texto largo (>100 chars): {len(long_text_elements)}")
        
        for i, text in enumerate(long_text_elements[:3]):
            parent = text.parent if text.parent else None
            parent_info = f"{parent.name} ({parent.get('class', ['no-class'])[0] if parent.get('class') else 'no-class'})" if parent else "no-parent"
            print(f"   📃 Texto {i+1} en {parent_info}: {text.strip()[:80]}...")
        
        # 5. Buscar elementos del mosaico específicamente
        mosaic_elements = soup.find_all(class_=re.compile(r"mosaic"))
        print(f"🗂️  Elementos del mosaico encontrados: {len(mosaic_elements)}")
        
        for elem in mosaic_elements[:3]:
            text_content = elem.get_text(strip=True)
            print(f"   🔖 {elem.name} ({elem.get('class', [''])[0]}): {text_content[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante análisis: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("🔍 ANÁLISIS: Detección de elementos superpuestos")
    print("=" * 70)
    
    success = analyze_potential_overlays()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ ANÁLISIS COMPLETADO")
        print("📝 Revise los elementos listados arriba para identificar posibles fuentes")
        print("🔄 Busque elementos con mucho texto que puedan estar mal posicionados")
    else:
        print("❌ ANÁLISIS FALLÓ")
        print("📝 Verifique que el servidor esté funcionando")
    
    print("=" * 70)

if __name__ == "__main__":
    main()