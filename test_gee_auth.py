#!/usr/bin/env python3
"""
Script para probar la autenticación de Google Earth Engine
"""

import os
import sys

def test_gee_authentication():
    """Probar la autenticación de Google Earth Engine"""
    
    print("🔍 Probando autenticación de Google Earth Engine...")
    
    try:
        # Importar Earth Engine
        import ee
        print("✅ Módulo 'ee' importado correctamente")
        
        # Intentar inicializar
        try:
            ee.Initialize()
            print("✅ Google Earth Engine inicializado correctamente")
            
            # Probar una operación básica
            try:
                # Obtener información de un dataset simple
                collection = ee.ImageCollection('COPERNICUS/S2_SR')
                count = collection.limit(1).size()
                print(f"✅ Operación de prueba exitosa: {count.getInfo()} imagen encontrada")
                
                # Obtener proyecto actual
                try:
                    project = ee.data.get_current_project()
                    print(f"📋 Proyecto actual: {project}")
                except Exception as e:
                    print(f"⚠️ No se pudo obtener el proyecto actual: {e}")
                
                return True
                
            except Exception as e:
                print(f"❌ Error en operación de prueba: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error al inicializar Google Earth Engine: {e}")
            print("💡 Asegúrate de haber ejecutado 'earthengine authenticate'")
            return False
            
    except ImportError as e:
        print(f"❌ Error al importar Google Earth Engine: {e}")
        print("💡 Instala con: pip install earthengine-api")
        return False

def check_credentials():
    """Verificar las credenciales almacenadas"""
    
    print("\n🔐 Verificando credenciales...")
    
    # Ruta típica de credenciales en Windows
    credentials_path = os.path.expanduser("~/.config/earthengine/credentials")
    
    if os.path.exists(credentials_path):
        print(f"✅ Archivo de credenciales encontrado: {credentials_path}")
        try:
            with open(credentials_path, 'r') as f:
                content = f.read()
                if 'refresh_token' in content:
                    print("✅ Credenciales parecen válidas (contienen refresh_token)")
                else:
                    print("⚠️ Credenciales pueden estar incompletas")
        except Exception as e:
            print(f"❌ Error leyendo credenciales: {e}")
    else:
        print(f"❌ Archivo de credenciales no encontrado: {credentials_path}")
        print("💡 Ejecuta 'earthengine authenticate' para configurar")

def test_gee_from_client():
    """Probar usando nuestro cliente personalizado"""
    
    print("\n🧪 Probando con cliente personalizado...")
    
    try:
        # Intentar importar nuestro cliente
        sys.path.append('.')
        from google_earth_engine_client import GoogleEarthEngineClient
        
        client = GoogleEarthEngineClient()
        
        if client.is_initialized:
            print("✅ Cliente GEE personalizado inicializado correctamente")
            return True
        else:
            print("❌ Cliente GEE personalizado no está inicializado")
            return False
            
    except ImportError as e:
        print(f"❌ Error importando cliente personalizado: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en cliente personalizado: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de Google Earth Engine\n")
    
    # Verificar credenciales
    check_credentials()
    
    # Probar autenticación básica
    basic_test = test_gee_authentication()
    
    # Probar cliente personalizado
    client_test = test_gee_from_client()
    
    print(f"\n📊 Resumen de pruebas:")
    print(f"  - Autenticación básica: {'✅ OK' if basic_test else '❌ FALLO'}")
    print(f"  - Cliente personalizado: {'✅ OK' if client_test else '❌ FALLO'}")
    
    if basic_test and client_test:
        print("\n🎉 ¡Google Earth Engine está configurado correctamente!")
    else:
        print("\n⚠️ Hay problemas con la configuración de Google Earth Engine")
        print("💡 Verifica que hayas ejecutado 'earthengine authenticate'")
