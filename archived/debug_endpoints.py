#!/usr/bin/env python3
"""
Script de diagnóstico para identificar errores específicos en endpoints
"""

import urllib.request
import urllib.error
import json
import sqlite3
import os

def check_database():
    """Verificar estructura de la base de datos"""
    print("🔍 VERIFICANDO BASE DE DATOS")
    print("=" * 50)
    
    db_path = "./data/geopolitical_intel.db"
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estructura de la tabla articles
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        
        print(f"✅ Base de datos encontrada")
        print(f"📊 Columnas en tabla 'articles': {len(columns)}")
        
        column_names = [col[1] for col in columns]
        critical_columns = ['id', 'title', 'summary', 'description', 'content', 'image_url', 'original_image_url']
        
        print("\n🔍 Verificando columnas críticas:")
        for col in critical_columns:
            if col in column_names:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col} - FALTA")
        
        # Contar artículos
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        print(f"\n📰 Total de artículos: {total}")
        
        # Contar artículos con imagen
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE (image_url IS NOT NULL AND image_url != '') 
               OR (original_image_url IS NOT NULL AND original_image_url != '')
        """)
        with_images = cursor.fetchone()[0]
        print(f"🖼️  Artículos con imagen: {with_images}")
        
        # Intentar consulta problemática
        print("\n🧪 Probando consulta con 'description':")
        try:
            cursor.execute("SELECT id, title, description FROM articles LIMIT 1")
            print("   ✅ Consulta con 'description' funciona")
        except sqlite3.OperationalError as e:
            print(f"   ❌ Error con 'description': {e}")
        
        print("\n🧪 Probando consulta con 'summary':")
        try:
            cursor.execute("SELECT id, title, summary FROM articles LIMIT 1")
            result = cursor.fetchone()
            if result:
                print("   ✅ Consulta con 'summary' funciona")
            else:
                print("   ⚠️  No hay datos en articles")
        except sqlite3.OperationalError as e:
            print(f"   ❌ Error con 'summary': {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")
        return False

def test_endpoint_with_details(url, name):
    """Probar endpoint con detalles de error"""
    print(f"\n🔍 Probando {name}")
    print(f"URL: {url}")
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            print(f"✅ {name}: Status {response.status}")
            content = response.read().decode('utf-8')
            
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    print(f"📊 Respuesta: {len(data)} elementos")
                    if len(data) > 0:
                        first = data[0]
                        print(f"📝 Primer elemento: {list(first.keys())}")
                else:
                    print(f"📊 Respuesta: Objeto con {len(data)} claves")
                    if 'error' in data:
                        print(f"❌ Error en respuesta: {data['error']}")
                
            except json.JSONDecodeError:
                print(f"⚠️  Respuesta no es JSON válido")
                print(f"Contenido: {content[:200]}...")
            
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ {name}: HTTP Error {e.code}")
        try:
            error_content = e.read().decode('utf-8')
            print(f"Detalles del error: {error_content[:500]}")
        except:
            print("No se pudieron leer detalles del error")
        return False
        
    except urllib.error.URLError as e:
        print(f"❌ {name}: URL Error - {e}")
        return False
        
    except Exception as e:
        print(f"❌ {name}: Error inesperado - {e}")
        return False

def main():
    print("🚨 DIAGNÓSTICO DE ERRORES 500")
    print("=" * 60)
    
    # Verificar base de datos primero
    db_ok = check_database()
    
    print("\n" + "=" * 60)
    print("🌐 PROBANDO ENDPOINTS")
    
    base_url = "http://localhost:5001"
    endpoints = [
        (f"{base_url}/api/status", "Status"),
        (f"{base_url}/api/articles", "Articles"),
        (f"{base_url}/api/articles?limit=20", "Articles (limit=20)"),
        (f"{base_url}/api/articles?limit=40", "Articles (limit=40)"),
        (f"{base_url}/api/hero-article", "Hero Article"),
        (f"{base_url}/api/articles/deduplicated", "Deduplicated Articles"),
        (f"{base_url}/api/articles/deduplicated?hours=24", "Deduplicated (24h)"),
    ]
    
    results = []
    for url, name in endpoints:
        success = test_endpoint_with_details(url, name)
        results.append((name, success))
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE DIAGNÓSTICO")
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print(f"\n💾 Base de datos: {'✅ OK' if db_ok else '❌ PROBLEMA'}")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    if successful == 0:
        print(f"\n🚨 TODOS LOS ENDPOINTS FALLAN ({successful}/{total})")
        print("💡 Posibles causas:")
        print("   - Servidor ejecutando versión con bugs")
        print("   - Problemas de columnas SQL")
        print("   - Código de servidor no actualizado")
    else:
        print(f"\n📊 Resultado: {successful}/{total} endpoints funcionando")

if __name__ == "__main__":
    main()