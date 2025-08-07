#!/usr/bin/env python3
"""
Prueba simple de autenticación de Google Earth Engine
"""

import os
import sys

def test_simple_gee():
    """Prueba simple de Google Earth Engine"""
    print("🔍 Probando inicialización simple de Google Earth Engine...")
    
    try:
        import ee
        print("✅ Módulo 'ee' importado correctamente")
        
        # Intentar inicialización sin proyecto específico
        try:
            # Intentar con autenticación por defecto, sin proyecto
            ee.Initialize(opt_url='https://earthengine.googleapis.com')
            print("✅ Google Earth Engine inicializado correctamente")
            
            # Probar una operación muy básica
            try:
                # Simplemente crear un número y obtenerlo
                number = ee.Number(42)
                result = number.getInfo()
                print(f"✅ Operación básica exitosa: {result}")
                
                # Intentar acceder a una colección pública
                try:
                    collection = ee.ImageCollection('COPERNICUS/S2_SR').limit(1)
                    size = collection.size()
                    size_result = size.getInfo()
                    print(f"✅ Acceso a colección exitoso: {size_result} imagen(es) encontrada(s)")
                    return True
                    
                except Exception as e:
                    print(f"⚠️ Error accediendo a colección (puede ser por permisos): {e}")
                    print("✅ Pero la autenticación básica funciona")
                    return True
                    
            except Exception as e:
                print(f"❌ Error en operación básica: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error al inicializar Google Earth Engine: {e}")
            
            # Intentar con inicialización aún más simple
            try:
                print("🔄 Intentando inicialización alternativa...")
                ee.Initialize()
                print("✅ Google Earth Engine inicializado con método alternativo")
                return True
            except Exception as e2:
                print(f"❌ También falló la inicialización alternativa: {e2}")
                return False
            
    except ImportError as e:
        print(f"❌ Error al importar Google Earth Engine: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_gee()
    
    if success:
        print("\n🎉 ¡Google Earth Engine está funcionando!")
    else:
        print("\n⚠️ Hay problemas con Google Earth Engine")
        print("💡 Asegúrate de haber ejecutado 'earthengine authenticate'")
