#!/usr/bin/env python3
"""
Test para verificar si el modal está siendo ocultado correctamente.
"""

import requests
from bs4 import BeautifulSoup
import re

def test_modal_hidden():
    """Test si el modal está correctamente oculto."""
    print("🧪 Test: Verificando que el modal esté oculto correctamente...")
    
    try:
        response = requests.get('http://localhost:5001', timeout=10)
        if response.status_code != 200:
            print(f"❌ No se puede acceder al sitio: {response.status_code}")
            return False
        
        # Verificar que el CSS del modal tiene display: none !important
        if 'display: none !important; /* FORCE HIDE BY DEFAULT */' in response.text:
            print("✅ Modal CSS configurado para ocultarse por defecto")
        else:
            print("⚠️ Modal CSS no está configurado correctamente")
            
        # Verificar que el modal HTML tiene style="display: none;"
        if 'id="article-modal" class="article-modal-overlay" style="display: none;"' in response.text:
            print("✅ Modal HTML configurado como oculto")
        else:
            print("⚠️ Modal HTML no tiene display: none")
            
        # Verificar que el modal solo se muestra con .show class
        if 'display: flex !important; /* ONLY SHOW WHEN .show CLASS */' in response.text:
            print("✅ Modal configurado para mostrarse solo con .show class")
        else:
            print("⚠️ Modal no está configurado para .show class")
            
        # Parse HTML para verificar estado del modal
        soup = BeautifulSoup(response.text, 'html.parser')
        modal = soup.find('div', id='article-modal')
        
        if modal:
            classes = modal.get('class', [])
            style = modal.get('style', '')
            
            print(f"📄 Modal encontrado:")
            print(f"   🎨 Classes: {classes}")
            print(f"   🎨 Style: {style}")
            
            # Verificar que no tiene la clase 'show'
            if 'show' not in classes:
                print("✅ Modal no tiene clase 'show' - debería estar oculto")
                return True
            else:
                print("❌ Modal tiene clase 'show' - está visible")
                return False
        else:
            print("❌ Modal no encontrado en HTML")
            return False
            
    except Exception as e:
        print(f"❌ Error durante test: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🔧 TEST: Modal Hidden Verification")
    print("=" * 60)
    
    success = test_modal_hidden()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RESULTADO: Modal configurado correctamente")
        print("📝 ACCIÓN: Verifique visualmente si el texto superpuesto desapareció")
    else:
        print("❌ RESULTADO: Modal no está configurado correctamente")
        print("📝 ACCIÓN: Revisar configuración CSS y JavaScript del modal")
    
    print("=" * 60)

if __name__ == "__main__":
    main()