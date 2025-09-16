#!/usr/bin/env python3
"""
Monitor del progreso de extracción masiva de imágenes
"""

import requests
import time
import json
from datetime import datetime

def monitor_image_extraction():
    """Monitorear el progreso de extracción de imágenes"""
    
    print("🖼️  MONITOR DE EXTRACCIÓN MASIVA DE IMÁGENES")
    print("=" * 60)
    print("🎯 Objetivo: Hacer que TODOS los artículos tengan imagen")
    print("=" * 60)
    
    base_url = "http://localhost:8050"
    start_time = datetime.now()
    
    # Estado inicial
    try:
        response = requests.get(f"{base_url}/api/images/status")
        if response.status_code == 200:
            initial_data = response.json()['statistics']
            initial_with_images = initial_data['articles_with_images']
            total_articles = initial_data['total_articles']
            initial_coverage = initial_data['coverage_percentage']
            
            print(f"📊 ESTADO INICIAL:")
            print(f"   📰 Total artículos: {total_articles}")
            print(f"   ✅ Con imágenes: {initial_with_images} ({initial_coverage:.1f}%)")
            print(f"   ❌ Sin imágenes: {initial_data['articles_without_images']}")
        else:
            print("❌ Error obteniendo estado inicial")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n🔄 INICIANDO MONITOREO...")
    print("-" * 60)
    
    iteration = 0
    max_iterations = 30  # Monitorear por 30 iteraciones (5 minutos)
    
    while iteration < max_iterations:
        try:
            # Verificar estado de imágenes
            response = requests.get(f"{base_url}/api/images/status")
            if response.status_code == 200:
                current_data = response.json()['statistics']
                current_with_images = current_data['articles_with_images']
                current_coverage = current_data['coverage_percentage']
                
                # Calcular progreso
                images_added = current_with_images - initial_with_images
                elapsed_time = datetime.now() - start_time
                rate = images_added / elapsed_time.total_seconds() * 60 if elapsed_time.total_seconds() > 0 else 0
                
                print(f"⏰ {elapsed_time.seconds//60:02d}:{elapsed_time.seconds%60:02d} | "
                      f"✅ {current_with_images}/{total_articles} ({current_coverage:.1f}%) | "
                      f"📈 +{images_added} | "
                      f"🚀 {rate:.1f} img/min")
                
                # Verificar si completado
                if current_coverage >= 99.0:
                    print("\n🎉 ¡PROCESO CASI COMPLETADO!")
                    print(f"✅ Cobertura: {current_coverage:.1f}%")
                    break
            
            # Verificar estado de la tarea
            response = requests.get(f"{base_url}/api/background/tasks")
            if response.status_code == 200:
                tasks = response.json()['tasks']
                if 'ensure_all_images' in tasks:
                    task = tasks['ensure_all_images']
                    status = task['status']
                    
                    if status == 'completed':
                        print("\n🎉 ¡TAREA COMPLETADA!")
                        if 'result' in task:
                            result = task['result']
                            print(f"📊 Resultado final:")
                            print(f"   ✅ Procesados: {result.get('processed', 'N/A')}")
                            print(f"   🖼️  Extraídos: {result.get('extracted', 'N/A')}")
                            print(f"   ❌ Errores: {result.get('errors', 'N/A')}")
                        break
                    elif status == 'failed':
                        print("\n❌ TAREA FALLÓ")
                        print(f"Error: {task.get('error', 'Error desconocido')}")
                        break
            
            time.sleep(10)  # Esperar 10 segundos entre verificaciones
            iteration += 1
            
        except Exception as e:
            print(f"❌ Error en iteración {iteration}: {e}")
            time.sleep(5)
            iteration += 1
    
    # Estado final
    print("\n" + "=" * 60)
    print("📊 ESTADO FINAL:")
    
    try:
        response = requests.get(f"{base_url}/api/images/status")
        if response.status_code == 200:
            final_data = response.json()['statistics']
            final_with_images = final_data['articles_with_images']
            final_coverage = final_data['coverage_percentage']
            
            total_added = final_with_images - initial_with_images
            improvement = final_coverage - initial_coverage
            
            print(f"   📰 Total artículos: {total_articles}")
            print(f"   ✅ Con imágenes: {final_with_images} ({final_coverage:.1f}%)")
            print(f"   📈 Imágenes agregadas: {total_added}")
            print(f"   🎯 Mejora de cobertura: +{improvement:.1f}%")
            
            if final_coverage >= 95:
                print("   🏆 ¡EXCELENTE COBERTURA ALCANZADA!")
            elif final_coverage >= 85:
                print("   🎉 ¡BUENA COBERTURA ALCANZADA!")
            elif final_coverage >= 75:
                print("   ✅ Cobertura mejorada significativamente")
            else:
                print("   ⚠️ Aún se puede mejorar la cobertura")
        
    except Exception as e:
        print(f"❌ Error obteniendo estado final: {e}")
    
    elapsed_total = datetime.now() - start_time
    print(f"   ⏱️ Tiempo total: {elapsed_total.seconds//60}:{elapsed_total.seconds%60:02d}")
    print("=" * 60)

if __name__ == "__main__":
    monitor_image_extraction()
