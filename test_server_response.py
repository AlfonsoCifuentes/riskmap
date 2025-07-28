#!/usr/bin/env python3
"""
Script para probar las respuestas del servidor
"""

import requests
import json
import time
import threading
from pathlib import Path
import sys

# Agregar el directorio al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_server():
    """Iniciar el servidor en un hilo separado"""
    try:
        from src.dashboard.app_modern import app, socketio
        socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error iniciando servidor: {e}")

def test_apis():
    """Probar las APIs del servidor"""
    base_url = "http://localhost:5000"
    
    # Esperar a que el servidor esté listo
    print("⏳ Esperando a que el servidor esté listo...")
    for i in range(30):  # Esperar hasta 30 segundos
        try:
            response = requests.get(f"{base_url}/api/test", timeout=5)
            if response.status_code == 200:
                print("✅ Servidor listo!")
                break
        except:
            pass
        time.sleep(1)
        print(f"   Intento {i+1}/30...")
    else:
        print("❌ El servidor no respondió en 30 segundos")
        return
    
    # Probar APIs
    apis_to_test = [
        "/api/test",
        "/api/dashboard/stats", 
        "/api/articles",
        "/api/articles/latest?limit=5",
        "/api/articles/high-risk?limit=3",
        "/api/articles/featured",
        "/api/events/heatmap"
    ]
    
    print("\n=== PROBANDO APIS ===")
    
    for api in apis_to_test:
        try:
            print(f"\n🔍 Probando: {api}")
            response = requests.get(f"{base_url}{api}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if api == "/api/articles":
                    print(f"✅ {len(data)} artículos cargados")
                    if len(data) > 0:
                        print(f"   Primer artículo: {data[0].get('title', 'Sin título')[:50]}...")
                        print(f"   País: {data[0].get('country', 'N/A')}")
                        print(f"   Riesgo: {data[0].get('risk_level', 'N/A')}")
                
                elif api == "/api/articles/high-risk?limit=3":
                    print(f"✅ {len(data)} artículos de alto riesgo")
                    for i, article in enumerate(data[:2], 1):
                        print(f"   {i}. {article.get('title', 'Sin título')[:40]}...")
                
                elif api == "/api/articles/featured":
                    if data.get('id', 0) != 0:
                        print(f"✅ Artículo destacado: {data.get('title', 'Sin título')[:50]}...")
                        print(f"   País: {data.get('country', 'N/A')}")
                    else:
                        print("⚠️ No hay artículo destacado disponible")
                
                elif api == "/api/dashboard/stats":
                    stats = data.get('stats', {})
                    print(f"✅ Estadísticas cargadas:")
                    print(f"   Total artículos: {stats.get('total_articles', 0)}")
                    print(f"   Alto riesgo: {stats.get('high_risk_events', 0)}")
                    print(f"   Procesados hoy: {stats.get('processed_today', 0)}")
                
                elif api == "/api/events/heatmap":
                    print(f"✅ {len(data)} puntos en mapa de calor")
                
                else:
                    print(f"�� API respondió correctamente")
                    
            else:
                print(f"❌ Error {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n=== PRUEBAS COMPLETADAS ===")

if __name__ == "__main__":
    print("🚀 Iniciando prueba del servidor...")
    
    # Iniciar servidor en hilo separado
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Esperar un poco y probar APIs
    time.sleep(3)
    test_apis()
    
    print("\n✅ Pruebas completadas. El servidor sigue ejecutándose.")
    print("🌐 Puedes acceder a: http://localhost:5000")
    print("📰 Análisis de noticias: http://localhost:5000/news-analysis")
    print("🔄 Presiona Ctrl+C para detener")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")