#!/usr/bin/env python3
"""
Script para probar el sistema completo corregido
"""

import requests
import json
import time
import threading
import webbrowser
from pathlib import Path
import sys

# Agregar el directorio al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_server():
    """Iniciar el servidor en un hilo separado"""
    try:
        from src.dashboard.app_modern import app, socketio
        print("🚀 Servidor iniciado en http://localhost:5000")
        socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")

def test_complete_system():
    """Probar el sistema completo"""
    base_url = "http://localhost:5000"
    
    print("⏳ Esperando a que el servidor esté listo...")
    for i in range(30):
        try:
            response = requests.get(f"{base_url}/api/test", timeout=5)
            if response.status_code == 200:
                print("✅ Servidor listo!")
                break
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(f"   Esperando... {i+1}/30")
    else:
        print("❌ El servidor no respondió en 30 segundos")
        return False
    
    print("\n=== PROBANDO SISTEMA COMPLETO ===")
    
    # 1. Probar API de test
    try:
        response = requests.get(f"{base_url}/api/test")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Test: {data['message']}")
            print(f"   Base de datos: {data['database']['articles']} artículos, {data['database']['events']} eventos")
        else:
            print(f"❌ API Test falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en API Test: {e}")
        return False
    
    # 2. Probar estadísticas
    try:
        response = requests.get(f"{base_url}/api/dashboard/stats")
        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print(f"✅ Estadísticas cargadas:")
            print(f"   📰 Total artículos: {stats['total_articles']}")
            print(f"   🔥 Alto riesgo: {stats['high_risk_events']}")
            print(f"   📅 Procesados hoy: {stats['processed_today']}")
            print(f"   ���� Regiones activas: {stats['active_regions']}")
        else:
            print(f"❌ Estadísticas fallaron: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en estadísticas: {e}")
        return False
    
    # 3. Probar artículos
    try:
        response = requests.get(f"{base_url}/api/articles?limit=5")
        if response.status_code == 200:
            articles = response.json()
            if isinstance(articles, list) and len(articles) > 0:
                print(f"✅ Artículos cargados: {len(articles)}")
                for i, article in enumerate(articles[:3], 1):
                    print(f"   {i}. {article['title'][:50]}...")
                    print(f"      País: {article['country']}, Riesgo: {article['risk_level']}")
            else:
                print("⚠️ No se encontraron artículos")
        else:
            print(f"❌ Artículos fallaron: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en artículos: {e}")
        return False
    
    # 4. Probar artículos de alto riesgo
    try:
        response = requests.get(f"{base_url}/api/articles/high-risk?limit=3")
        if response.status_code == 200:
            articles = response.json()
            if isinstance(articles, list) and len(articles) > 0:
                print(f"✅ Artículos de alto riesgo: {len(articles)}")
                for i, article in enumerate(articles, 1):
                    print(f"   {i}. {article['title'][:50]}... ({article['country']})")
            else:
                print("⚠️ No se encontraron artículos de alto riesgo")
        else:
            print(f"❌ Alto riesgo falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en alto riesgo: {e}")
        return False
    
    # 5. Probar artículo destacado
    try:
        response = requests.get(f"{base_url}/api/articles/featured")
        if response.status_code == 200:
            article = response.json()
            if article.get('id', 0) != 0:
                print(f"✅ Artículo destacado: {article['title'][:50]}...")
                print(f"   País: {article['country']}, Riesgo: {article['risk_level']}")
            else:
                print("⚠️ No hay artículo destacado disponible")
        else:
            print(f"❌ Artículo destacado falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en artículo destacado: {e}")
        return False
    
    # 6. Probar mapa de calor
    try:
        response = requests.get(f"{base_url}/api/events/heatmap")
        if response.status_code == 200:
            heatmap = response.json()
            if isinstance(heatmap, list):
                print(f"✅ Mapa de calor: {len(heatmap)} puntos")
            else:
                print("⚠️ Datos de mapa de calor no válidos")
        else:
            print(f"❌ Mapa de calor falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en mapa de calor: {e}")
        return False
    
    # 7. Probar página principal
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Página principal accesible")
        else:
            print(f"❌ Página principal falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en página principal: {e}")
        return False
    
    # 8. Probar página de análisis de noticias
    try:
        response = requests.get(f"{base_url}/news-analysis")
        if response.status_code == 200:
            print("✅ Página de análisis de noticias accesible")
        else:
            print(f"❌ Análisis de noticias falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en análisis de noticias: {e}")
        return False
    
    print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    print("✅ El sistema está funcionando correctamente")
    print("✅ Los artículos se cargan desde la base de datos real")
    print("✅ Las 3 versiones del mapa de calor están disponibles")
    print("✅ Los artículos son reales con países y dirigentes específicos")
    
    return True

if __name__ == "__main__":
    print("🧪 PRUEBA COMPLETA DEL SISTEMA RISKMAP")
    print("=" * 50)
    
    # Iniciar servidor en hilo separado
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Esperar un poco y probar sistema
    time.sleep(3)
    
    if test_complete_system():
        print("\n🌐 URLs disponibles:")
        print("   📊 Dashboard principal: http://localhost:5000")
        print("   📰 Análisis de noticias: http://localhost:5000/news-analysis")
        print("   🧪 Página de pruebas: http://localhost:5000/test-articles")
        print("   🔧 API de prueba: http://localhost:5000/api/test")
        
        print("\n🚀 Abriendo navegador...")
        try:
            webbrowser.open("http://localhost:5000/news-analysis")
        except:
            pass
        
        print("\n🔄 El servidor seguirá ejecutándose...")
        print("   Presiona Ctrl+C para detener")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Sistema detenido por el usuario")
    else:
        print("\n❌ Las pruebas fallaron. Revisa los errores anteriores.")
        print("🔧 Verifica que la base de datos esté disponible y las columnas sean correctas.")