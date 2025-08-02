"""
Script para probar el sistema de extracción de imágenes
"""

import requests
import json
import time

def test_image_extraction():
    """Probar la extracción de imágenes"""
    base_url = "http://127.0.0.1:5001"  # Puerto del servidor simple
    
    print("🖼️  PROBANDO SISTEMA DE EXTRACCIÓN DE IMÁGENES")
    print("=" * 60)
    
    # 1. Verificar estado actual de imágenes
    print("📊 Verificando estado actual de imágenes...")
    try:
        response = requests.get(f"{base_url}/api/images/status")
        if response.status_code == 200:
            data = response.json()
            stats = data['statistics']
            print(f"   📰 Total de artículos: {stats['total_articles']}")
            print(f"   🖼️  Con imágenes: {stats['articles_with_images']}")
            print(f"   ❌ Sin imágenes: {stats['articles_without_images']}")
            print(f"   📈 Cobertura: {stats['coverage_percentage']:.1f}%")
        else:
            print(f"   ❌ Error obteniendo estado: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 2. Iniciar extracción de imágenes
    print("🚀 Iniciando extracción de imágenes...")
    try:
        response = requests.post(f"{base_url}/api/images/extract", 
                               json={"limit": 10})
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"   ✅ {data['message']}")
                print(f"   📝 Artículos a procesar: {data['articles_to_process']}")
            else:
                print(f"   ❌ Error: {data.get('error', 'Error desconocido')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 3. Verificar estado de tareas en background
    print("⏳ Monitoreando progreso...")
    for i in range(5):
        try:
            response = requests.get(f"{base_url}/api/background/tasks")
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('tasks', {})
                
                if 'extract_images' in tasks:
                    task = tasks['extract_images']
                    status = task.get('status', 'unknown')
                    progress = task.get('progress', 0)
                    
                    print(f"   📊 Estado: {status} - Progreso: {progress}%")
                    
                    if status == 'completed':
                        result = task.get('result', {})
                        print(f"   ✅ Completado: {result.get('processed', 0)} procesados, {result.get('errors', 0)} errores")
                        break
                    elif status == 'failed':
                        error = task.get('error', 'Error desconocido')
                        print(f"   ❌ Falló: {error}")
                        break
                else:
                    print(f"   📝 Tarea no encontrada (intento {i+1}/5)")
            
            time.sleep(5)
            
        except Exception as e:
            print(f"   ❌ Error monitoreando: {e}")
    
    print()
    
    # 4. Verificar estado final
    print("📊 Verificando estado final...")
    try:
        response = requests.get(f"{base_url}/api/images/status")
        if response.status_code == 200:
            data = response.json()
            stats = data['statistics']
            print(f"   📰 Total de artículos: {stats['total_articles']}")
            print(f"   🖼️  Con imágenes: {stats['articles_with_images']}")
            print(f"   ❌ Sin imágenes: {stats['articles_without_images']}")
            print(f"   📈 Cobertura: {stats['coverage_percentage']:.1f}%")
        else:
            print(f"   ❌ Error obteniendo estado final: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("✅ Prueba completada")

if __name__ == "__main__":
    test_image_extraction()
