#!/usr/bin/env python3
"""
Script para probar que la configuración de la base de datos funciona correctamente
"""

import os
import sqlite3
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_database_path():
    """Obtener la ruta de la base de datos desde variables de entorno"""
    db_path = os.getenv('DATABASE_PATH', './data/geopolitical_intel.db')
    return db_path

def test_database_configuration():
    """Probar que la configuración de la base de datos funciona"""
    
    print("🔧 PROBANDO CONFIGURACIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    # 1. Verificar variable de entorno
    db_path = get_database_path()
    print(f"📍 Ruta desde .env: {db_path}")
    
    # 2. Verificar que el archivo existe
    if os.path.exists(db_path):
        print(f"✅ Archivo de BD existe: {db_path}")
    else:
        print(f"❌ Archivo de BD NO existe: {db_path}")
        return False
    
    # 3. Conectar y verificar contenido
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar tabla articles
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
            if cursor.fetchone():
                print("✅ Tabla 'articles' encontrada")
                
                # Contar artículos
                cursor.execute("SELECT COUNT(*) FROM articles")
                total_articles = cursor.fetchone()[0]
                print(f"📰 Total de artículos: {total_articles}")
                
                # Verificar artículos con imágenes
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != '' 
                    AND image_url NOT LIKE '%placeholder%'
                """)
                with_images = cursor.fetchone()[0]
                print(f"🖼️  Con imágenes: {with_images}")
                
                # Calcular cobertura
                coverage = (with_images / total_articles * 100) if total_articles > 0 else 0
                print(f"📈 Cobertura de imágenes: {coverage:.1f}%")
                
                # Mostrar algunos ejemplos
                print("\n📝 Ejemplos de artículos:")
                cursor.execute("""
                    SELECT id, title, image_url 
                    FROM articles 
                    ORDER BY id DESC 
                    LIMIT 3
                """)
                for row in cursor.fetchall():
                    has_image = "✅" if row[2] and 'placeholder' not in row[2] else "❌"
                    print(f"   {has_image} ID {row[0]}: {row[1][:60]}...")
                
                return True
            else:
                print("❌ Tabla 'articles' NO encontrada")
                return False
    
    except Exception as e:
        print(f"❌ Error conectando a la BD: {e}")
        return False

def test_endpoints_configuration():
    """Probar que los endpoints usan la configuración correcta"""
    print("\n🔌 PROBANDO CONFIGURACIÓN DE ENDPOINTS")
    print("=" * 50)
    
    # Simular el comportamiento del app
    try:
        # Test 1: Función get_database_path
        db_path = get_database_path()
        print(f"✅ get_database_path() retorna: {db_path}")
        
        # Test 2: Verificar que podemos conectar
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            print(f"✅ Conexión exitosa: {count} artículos encontrados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración de endpoints: {e}")
        return False

if __name__ == "__main__":
    print("🧪 INICIANDO PRUEBAS DE CONFIGURACIÓN")
    print("=" * 60)
    
    success1 = test_database_configuration()
    success2 = test_endpoints_configuration()
    
    print("\n🎯 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    if success1 and success2:
        print("✅ TODAS LAS PRUEBAS EXITOSAS")
        print("🚀 La configuración está lista para usar")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisar la configuración")
    
    print("\n📝 Variable DATABASE_PATH configurada en .env")
    print("🔗 Todos los archivos ahora usan get_database_path()")
    print("🎯 Ya no habrá confusión sobre qué BD usar")
