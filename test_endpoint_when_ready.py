#!/usr/bin/env python3
"""
Test directo del endpoint usando requests cuando la app esté funcionando
"""
import requests
import json
import time
import sys

def wait_for_server(url="http://localhost:5001/api/articles", max_attempts=30):
    """Esperar a que el servidor esté disponible"""
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except:
            pass
        
        print(f"Intento {attempt + 1}/{max_attempts} - Servidor no disponible, esperando...")
        time.sleep(2)
    
    return False

def test_endpoint():
    """Probar el endpoint /api/articles"""
    print("🌐 Probando endpoint /api/articles...")
    
    try:
        url = "http://localhost:5001/api/articles?limit=5"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"✅ Endpoint funcionando: {len(articles)} artículos retornados")
            
            # Verificar que no hay placeholders problemáticos ni <think>
            issues = 0
            
            for i, article in enumerate(articles):
                print(f"\n📰 Artículo {i+1}:")
                print(f"  ID: {article.get('id')}")
                print(f"  Título: {article.get('title', '')[:60]}...")
                
                # Verificar imagen
                image_url = article.get('image', '') or article.get('image_url', '')
                print(f"  Imagen: {image_url}")
                
                if 'via.placeholder' in image_url:
                    print(f"  ❌ CONTIENE VIA.PLACEHOLDER")
                    issues += 1
                elif 'unsplash' in image_url:
                    print(f"  ✅ Usando Unsplash")
                
                # Verificar summary
                summary = article.get('summary', '') or article.get('content', '')
                if '<think>' in summary:
                    print(f"  ❌ CONTIENE <THINK>")
                    issues += 1
                else:
                    print(f"  ✅ Summary limpio")
                
                print(f"  Summary: {summary[:80]}...")
                print(f"  Risk: {article.get('risk_score', 0)}")
            
            print(f"\n📊 Resumen:")
            print(f"- Total artículos: {len(articles)}")
            print(f"- Problemas encontrados: {issues}")
            
            if issues == 0:
                print("🎉 ENDPOINT FUNCIONANDO PERFECTAMENTE")
            else:
                print("⚠️  ALGUNOS PROBLEMAS DETECTADOS")
            
            return issues == 0
            
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 TEST: Endpoint después de correcciones")
    print("=" * 50)
    
    # Verificar si el servidor está disponible
    if wait_for_server():
        print("✅ Servidor disponible")
        success = test_endpoint()
        
        if success:
            print("\n✅ TODAS LAS CORRECCIONES FUNCIONAN CORRECTAMENTE")
            print("💡 Ahora puedes abrir http://localhost:5001 en el navegador")
        else:
            print("\n❌ REVISAR PROBLEMAS EN EL ENDPOINT")
    else:
        print("❌ Servidor no disponible")
        print("💡 Ejecuta: python app_BUENA.py")

if __name__ == "__main__":
    main()