#!/usr/bin/env python3
"""Prueba rápida usando urllib en lugar de requests"""
import urllib.request
import json

def test_endpoint_simple():
    url = "http://localhost:5001/api/articles"
    
    try:
        print("🔍 Probando endpoint /api/articles...")
        
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            
        print(f"✅ SUCCESS: {data.get('success', False)}")
        print(f"📰 Total artículos: {data.get('total', 0)}")
        
        articles = data.get('articles', [])
        if articles:
            print(f"\n🎯 ¡ÉXITO! {len(articles)} artículos cargados para el mosaico:")
            for i, article in enumerate(articles[:3]):
                print(f"   {i+1}. {article.get('title', 'Sin título')[:50]}...")
                print(f"      🖼️ Imagen: {'SÍ' if article.get('image') else 'NO'}")
                print(f"      🎯 Riesgo: {article.get('risk', 'unknown')}")
            
            print("\n✅ EL MOSAICO DEBERÍA FUNCIONAR AHORA!")
            print("   El error '❌ No se pudieron cargar artículos' está RESUELTO")
            return True
        else:
            print("❌ Sin artículos")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_endpoint_simple()