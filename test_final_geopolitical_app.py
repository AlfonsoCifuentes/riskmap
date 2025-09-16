#!/usr/bin/env python3
"""
Test final: Verificar que la aplicación Flask use el filtro geopolítico
"""
import requests
import time
import json

def test_flask_geopolitical_filter():
    """Test el filtro geopolítico en la aplicación Flask real"""
    
    print("🧪 TEST FINAL: Filtro geopolítico en Flask")
    print("=" * 55)
    
    # URL del endpoint de artículos
    url = "http://localhost:5001/api/articles"
    
    try:
        print("🌐 Conectando a Flask...")
        response = requests.get(url, params={'limit': 20}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                articles = data.get('articles', [])
                print(f"✅ Conexión exitosa")
                print(f"📊 Artículos obtenidos: {len(articles)}")
                
                print(f"\n📰 ARTÍCULOS SERVIDOS POR FLASK:")
                
                geopolitical_count = 0
                sports_entertainment_count = 0
                
                for i, article in enumerate(articles, 1):
                    title = article.get('title', 'Sin título')
                    risk = article.get('risk_score', 0)
                    source = article.get('source', 'Sin fuente')
                    
                    print(f"   {i:2}. [Riesgo: {risk:.2f}] '{title[:50]}...' ({source})")
                    
                    # Clasificar artículo
                    title_lower = title.lower()
                    if any(word in title_lower for word in [
                        'sport', 'game', 'match', 'team', 'player', 'goal', 
                        'football', 'soccer', 'basketball', 'emmy', 'oscar', 
                        'actor', 'movie', 'celebrity'
                    ]):
                        sports_entertainment_count += 1
                        print(f"       ⚠️  DEPORTES/ENTRETENIMIENTO detectado")
                    elif any(word in title_lower for word in [
                        'war', 'conflict', 'military', 'politics', 'government',
                        'israel', 'russia', 'china', 'nato', 'crisis', 'security'
                    ]):
                        geopolitical_count += 1
                        print(f"       ✅ GEOPOLÍTICO confirmado")
                
                print(f"\n📊 ANÁLISIS DE CONTENIDO:")
                print(f"   ✅ Artículos geopolíticos: {geopolitical_count}")
                print(f"   ❌ Deportes/entretenimiento: {sports_entertainment_count}")
                print(f"   🔄 Otros: {len(articles) - geopolitical_count - sports_entertainment_count}")
                
                success_rate = (geopolitical_count / len(articles) * 100) if articles else 0
                print(f"   📈 Tasa de éxito geopolítico: {success_rate:.1f}%")
                
                # Evaluación final
                print(f"\n🎯 EVALUACIÓN DEL FILTRO:")
                if sports_entertainment_count == 0:
                    print(f"   🎉 FILTRO PERFECTO: No se detectaron deportes/entretenimiento")
                elif sports_entertainment_count <= 2:
                    print(f"   ✅ FILTRO BUENO: Solo {sports_entertainment_count} artículos no geopolíticos")
                else:
                    print(f"   ⚠️  FILTRO MEJORABLE: {sports_entertainment_count} artículos no geopolíticos")
                
                return {
                    'total': len(articles),
                    'geopolitical': geopolitical_count,
                    'sports_entertainment': sports_entertainment_count,
                    'success_rate': success_rate
                }
                
            else:
                print(f"❌ Error en respuesta: {data}")
                return None
                
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar a Flask en localhost:5001")
        print(f"💡 Para probar:")
        print(f"   1. Ejecutar: python app_BUENA.py")
        print(f"   2. Esperar que Flask arranque")
        print(f"   3. Ejecutar este test nuevamente")
        return None
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def main():
    """Función principal"""
    print("🔧 VERIFICACIÓN FINAL DEL SISTEMA")
    print("=" * 55)
    
    # Test del filtro geopolítico
    result = test_flask_geopolitical_filter()
    
    if result:
        print(f"\n📋 RESUMEN FINAL:")
        print(f"   🎯 Objetivo: Solo mostrar noticias geopolíticas")
        print(f"   ✅ Implementado: Filtro SQL con palabras clave")
        print(f"   📊 Resultado: {result['geopolitical']}/{result['total']} artículos geopolíticos")
        
        if result['sports_entertainment'] == 0:
            print(f"   🏆 ÉXITO TOTAL: Cero deportes/entretenimiento")
        else:
            print(f"   📈 Mejora: {result['sports_entertainment']} artículos requieren ajuste")
        
        print(f"\n🚀 SISTEMA LISTO PARA USAR")
        
    else:
        print(f"\n⚠️  PARA COMPLETAR LA VERIFICACIÓN:")
        print(f"   1. Asegúrese de que Flask esté corriendo")
        print(f"   2. Verifique que el filtro esté aplicado en app_BUENA.py")

if __name__ == "__main__":
    main()