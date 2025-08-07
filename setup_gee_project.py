#!/usr/bin/env python3
"""
Script para configurar Google Earth Engine con un proyecto personalizado
"""

import os
import subprocess
import sys
import json
from datetime import datetime

def print_step(step, description):
    """Imprimir paso de configuración"""
    print(f"\n🔧 PASO {step}: {description}")
    print("=" * 60)

def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"⚡ Ejecutando: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Éxito")
            if result.stdout.strip():
                print(f"📄 Output: {result.stdout.strip()}")
            return True, result.stdout.strip()
        else:
            print(f"❌ {description} - Error")
            if result.stderr.strip():
                print(f"⚠️ Error: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False, str(e)

def setup_gee_project():
    """Configurar proyecto de Google Earth Engine"""
    
    print("🚀 CONFIGURACIÓN DE GOOGLE EARTH ENGINE")
    print("=" * 60)
    print("Este script te ayudará a configurar Google Earth Engine con tu propio proyecto.")
    print()
    
    # Paso 1: Verificar CLI instalado
    print_step(1, "Verificar Google Earth Engine CLI")
    success, output = run_command("earthengine --version", "Verificar CLI")
    if not success:
        print("❌ Google Earth Engine CLI no está instalado.")
        print("💡 Instala con: pip install earthengine-api")
        return False
    
    # Paso 2: Solicitar ID del proyecto
    print_step(2, "Configurar ID del proyecto")
    print("🔗 Crea un nuevo proyecto en: https://console.cloud.google.com/projectcreate")
    print()
    print("Sugerencias para el nombre del proyecto:")
    print("  - riskmap-satellite-analysis")
    print("  - geospatial-intelligence-hub")
    print("  - conflict-monitoring-gee")
    print("  - earth-engine-riskmap")
    print()
    
    project_id = input("📝 Ingresa el ID de tu proyecto de Google Cloud: ").strip()
    
    if not project_id:
        print("❌ ID del proyecto es requerido.")
        return False
    
    # Paso 3: Configurar proyecto en EE
    print_step(3, f"Configurar proyecto: {project_id}")
    success, output = run_command(f'earthengine set_project "{project_id}"', "Configurar proyecto")
    if not success:
        print(f"❌ Error configurando proyecto: {output}")
        return False
    
    # Paso 4: Verificar autenticación
    print_step(4, "Verificar autenticación")
    success, output = run_command("earthengine authenticate --quiet", "Autenticación")
    if not success:
        print("⚠️ Puede que necesites autenticarte manualmente")
        print("💡 Ejecuta: earthengine authenticate")
    
    # Paso 5: Probar conexión
    print_step(5, "Probar conexión con Google Earth Engine")
    
    # Crear script de prueba temporal
    test_script = '''
import ee
try:
    ee.Initialize()
    print("✅ Google Earth Engine inicializado correctamente")
    
    # Probar operación básica
    number = ee.Number(42)
    result = number.getInfo()
    print(f"✅ Operación básica exitosa: {result}")
    
    # Probar acceso a colección
    collection = ee.ImageCollection('COPERNICUS/S2_SR').limit(1)
    size = collection.size().getInfo()
    print(f"✅ Acceso a colección exitoso: {size} imagen(es)")
    
    print("🎉 ¡Configuración completada exitosamente!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if "project" in str(e).lower():
        print("💡 Asegúrate de que el proyecto existe y tienes permisos")
        print("💡 Visita: https://console.cloud.google.com/apis/library/earthengine.googleapis.com")
    elif "authentication" in str(e).lower():
        print("💡 Ejecuta: earthengine authenticate")
'''
    
    # Escribir y ejecutar script de prueba
    with open('test_gee_connection.py', 'w') as f:
        f.write(test_script)
    
    success, output = run_command("python test_gee_connection.py", "Probar conexión GEE")
    
    # Limpiar archivo temporal
    try:
        os.remove('test_gee_connection.py')
    except:
        pass
    
    if success:
        print_step(6, "Configurar variables de entorno")
        print(f"💾 Guardando configuración del proyecto: {project_id}")
        
        # Guardar en archivo .env
        env_line = f"GEE_PROJECT_ID={project_id}\n"
        
        try:
            # Leer .env existente
            env_content = ""
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    env_content = f.read()
            
            # Actualizar o agregar GEE_PROJECT_ID
            lines = env_content.split('\n')
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('GEE_PROJECT_ID='):
                    lines[i] = f"GEE_PROJECT_ID={project_id}"
                    updated = True
                    break
            
            if not updated:
                lines.append(f"GEE_PROJECT_ID={project_id}")
            
            # Escribir .env actualizado
            with open('.env', 'w') as f:
                f.write('\n'.join(line for line in lines if line.strip()))
            
            print("✅ Variable GEE_PROJECT_ID guardada en .env")
            
        except Exception as e:
            print(f"⚠️ Error guardando en .env: {e}")
        
        print()
        print("🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("=" * 60)
        print(f"✅ Proyecto configurado: {project_id}")
        print("✅ Google Earth Engine está listo para usar")
        print("✅ Variables de entorno actualizadas")
        print()
        print("🔗 Enlaces útiles:")
        print(f"   - Console del proyecto: https://console.cloud.google.com/home/dashboard?project={project_id}")
        print(f"   - APIs habilitadas: https://console.cloud.google.com/apis/dashboard?project={project_id}")
        print(f"   - Earth Engine: https://console.cloud.google.com/apis/library/earthengine.googleapis.com?project={project_id}")
        
        return True
    else:
        print()
        print("⚠️ CONFIGURACIÓN INCOMPLETA")
        print("=" * 60)
        print("El proyecto fue configurado pero hay problemas de conexión.")
        print()
        print("🔧 Pasos adicionales necesarios:")
        print("1. Habilita la API de Google Earth Engine:")
        print(f"   https://console.cloud.google.com/apis/library/earthengine.googleapis.com?project={project_id}")
        print("2. Asegúrate de tener permisos en el proyecto")
        print("3. Ejecuta: earthengine authenticate")
        
        return False

if __name__ == "__main__":
    setup_gee_project()
