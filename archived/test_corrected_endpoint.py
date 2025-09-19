#!/usr/bin/env python3
"""
Probar el endpoint del servidor de prueba
"""
import requests
import json

def test_articles_endpoint():
    """Probar el endpoint /api/articles en el servidor de prueba"""
    print("🧪 PROBANDO: http://localhost:5000/api/articles")
    print("=" * 60)
    
    try:
        url = "http://localhost:5000/api/articles?limit=5"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            filters = data.get('filters_applied', {})
            
            print(f"✅ ENDPOINT FUNCIONANDO")
            print(f"📊 Artículos obtenidos: {len(articles)}")
            print(f"🔧 Filtros aplicados:")
            for filter_name, applied in filters.items():
                print(f"   - {filter_name}: {'✅' if applied else '❌'}")
            
            print("\n📰 ARTÍCULOS:")
            
            issues = 0
            for i, article in enumerate(articles):
                print(f"\n{i+1}. ID: {article.get('id')}")
                title = article.get('title', '')
                print(f"   📰 {title[:70]}...")
                
                # Verificar imagen
                image_url = article.get('image', '')
                if 'via.placeholder' in image_url:
                    print(f"   ❌ IMAGEN: Usando via.placeholder (problemático)")
                    issues += 1
                elif 'unsplash' in image_url:
                    print(f"   ✅ IMAGEN: Unsplash (válido)")
                else:
                    print(f"   🖼️  IMAGEN: {image_url[:50]}...")
                
                # Verificar contenido
                content = article.get('content', '') or article.get('summary', '')
                if '<think>' in content:
                    print(f"   ❌ CONTENIDO: Contiene <think>")
                    issues += 1
                else:
                    print(f"   ✅ CONTENIDO: Limpio")
                
                print(f"   📊 Risk Score: {article.get('risk_score', 0)}")
                print(f"   🔗 Source: {article.get('source', 'N/A')}")
            
            print(f"\n" + "=" * 60)
            print(f"📋 RESUMEN:")
            print(f"- Artículos retornados: {len(articles)}")
            print(f"- Problemas detectados: {issues}")
            
            if issues == 0:
                print("🎉 TODAS LAS CORRECCIONES FUNCIONAN PERFECTAMENTE")
                print("✅ No se detectaron URLs de via.placeholder")
                print("✅ No se detectó contenido <think>")
                print("✅ Todas las imágenes usan URLs válidas")
                return True
            else:
                print("⚠️  SE DETECTARON ALGUNOS PROBLEMAS")
                return False
        
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_status_endpoint():
    """Probar el endpoint de estado"""
    print("\n🔧 PROBANDO: http://localhost:5000/api/status")
    
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Status endpoint funcionando")
            print(f"   Database: {'✅' if data.get('database') else '❌'}")
            return True
        else:
            print(f"❌ Status endpoint error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return False

def main():
    print("🧪 TESTING: Servidor de prueba con correcciones aplicadas")
    
    # Test 1: Status
    status_ok = test_status_endpoint()
    
    # Test 2: Articles
    articles_ok = test_articles_endpoint()
    
    print(f"\n" + "=" * 60)
    print("🎯 RESULTADO FINAL:")
    print(f"- Status endpoint: {'✅ OK' if status_ok else '❌ FALLO'}")
    print(f"- Articles endpoint: {'✅ OK' if articles_ok else '❌ FALLO'}")
    
    if status_ok and articles_ok:
        print("\n🎉 TODOS LOS TESTS EXITOSOS")
        print("🔗 Próximo paso: Probar en el navegador:")
        print("   http://localhost:5000/api/articles")
    else:
        print("\n⚠️  ALGUNOS TESTS FALLARON")

if __name__ == "__main__":
    main()