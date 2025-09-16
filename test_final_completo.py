#!/usr/bin/env python3
"""
TEST FINAL COMPLETO DEL SISTEMA RISKMAP
Verifica que tanto el filtro geopolítico como el sistema de imágenes funcionen correctamente
"""

import os
import sys
import sqlite3
import requests
from datetime import datetime

# Agregar el directorio raíz al path para importar el módulo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test 1: Verificar conexión a la base de datos"""
    print("🧪 TEST 1: Conexión a la base de datos")
    
    db_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            print(f"   ✅ Base de datos conectada: {total:,} artículos")
            return True
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def test_geopolitical_filter():
    """Test 2: Verificar filtro geopolítico"""
    print("\n🧪 TEST 2: Filtro geopolítico")
    
    db_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # SQL con filtro geopolítico (igual que en app_BUENA.py)
            query = """
            SELECT id, title, source, image_url 
            FROM articles 
            WHERE (
                -- Incluir contenido geopolítico
                (LOWER(title || ' ' || COALESCE(content, '')) LIKE '%war%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%conflict%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%military%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%politics%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%government%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%security%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%nato%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%russia%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%china%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%israel%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%gaza%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%iran%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%guerra%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%militar%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%política%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%gobierno%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%seguridad%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%otan%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%rusia%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%irán%')
            ) AND (
                -- Excluir contenido no geopolítico
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%sport%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%game%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%match%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%team%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%player%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%goal%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%football%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%soccer%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%basketball%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%emmy%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%oscar%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%movie%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%actor%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%hollywood%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%music%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%celebrity%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%iphone%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%apple%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%anime%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tv show%'
            )
            ORDER BY created_at DESC 
            LIMIT 20
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            print(f"   ✅ Artículos geopolíticos encontrados: {len(results)}")
            
            if results:
                print("   📰 Ejemplos de artículos filtrados:")
                for i, (article_id, title, source, image_url) in enumerate(results[:5], 1):
                    title_short = title[:50] + "..." if len(title) > 50 else title
                    print(f"      {i}. [{source}] {title_short}")
                    
            return len(results) > 0
            
    except Exception as e:
        print(f"   ❌ Error en filtro: {e}")
        return False

def test_image_system():
    """Test 3: Verificar sistema de imágenes"""
    print("\n🧪 TEST 3: Sistema de imágenes")
    
    images_dir = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\static\images\news"
    db_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
    
    try:
        # Verificar directorio
        if not os.path.exists(images_dir):
            print(f"   ❌ Directorio no existe: {images_dir}")
            return False
            
        # Contar imágenes en el directorio
        image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        print(f"   📊 Imágenes en directorio: {len(image_files)}")
        
        # Verificar BD
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Artículos con imagen original
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE original_image_url IS NOT NULL AND original_image_url != ''
            """)
            with_original = cursor.fetchone()[0]
            
            # Artículos con placeholder
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE image_url LIKE '%placeholder%'
            """)
            with_placeholder = cursor.fetchone()[0]
            
            # Total artículos
            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            
            coverage = (with_original / total * 100) if total > 0 else 0
            
            print(f"   📊 Artículos con imagen original: {with_original:,}")
            print(f"   📊 Artículos con placeholder: {with_placeholder:,}")
            print(f"   📈 Cobertura de imágenes: {coverage:.1f}%")
            
            return coverage > 70  # Esperamos al menos 70% de cobertura
            
    except Exception as e:
        print(f"   ❌ Error en sistema de imágenes: {e}")
        return False

def test_flask_api():
    """Test 4: Verificar API Flask (si está ejecutándose)"""
    print("\n🧪 TEST 4: API Flask")
    
    try:
        response = requests.get("http://localhost:5001/api/articles", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                print(f"   ✅ API respondiendo: {len(data)} artículos")
                
                # Verificar que los artículos tengan imágenes
                with_images = sum(1 for article in data if article.get('image_url') and not 'placeholder' in article['image_url'])
                print(f"   📊 Artículos con imagen real: {with_images}/{len(data)}")
                
                # Mostrar algunos ejemplos
                print("   📰 Ejemplos de artículos desde API:")
                for i, article in enumerate(data[:3], 1):
                    title = article.get('title', 'Sin título')[:50] + "..."
                    source = article.get('source', 'Sin fuente')
                    has_real_image = 'placeholder' not in article.get('image_url', '')
                    image_status = "✅" if has_real_image else "❌"
                    print(f"      {i}. [{source}] {title} {image_status}")
                
                return True
            else:
                print(f"   ⚠️  API responde pero sin datos válidos")
                return False
                
        else:
            print(f"   ❌ API error HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Flask no está ejecutándose en localhost:5001")
        return False
    except Exception as e:
        print(f"   ❌ Error al conectar API: {e}")
        return False

def test_image_serving():
    """Test 5: Verificar que Flask sirva imágenes correctamente"""
    print("\n🧪 TEST 5: Servicio de imágenes")
    
    images_dir = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\static\images\news"
    
    try:
        # Buscar una imagen existente
        if os.path.exists(images_dir):
            image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            
            if image_files:
                test_image = image_files[0]
                image_url = f"http://localhost:5001/static/images/news/{test_image}"
                
                response = requests.head(image_url, timeout=10)
                
                if response.status_code == 200:
                    print(f"   ✅ Imagen servida correctamente: {test_image}")
                    return True
                else:
                    print(f"   ❌ Error sirviendo imagen: HTTP {response.status_code}")
                    return False
            else:
                print(f"   ⚠️  No hay imágenes para probar")
                return False
        else:
            print(f"   ❌ Directorio de imágenes no existe")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Flask no está ejecutándose")
        return False
    except Exception as e:
        print(f"   ❌ Error sirviendo imagen: {e}")
        return False

def main():
    """Función principal - ejecutar todos los tests"""
    print("🧪 TEST FINAL COMPLETO DEL SISTEMA RISKMAP")
    print("=" * 60)
    print(f"⏰ Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Conexión BD", test_database_connection),
        ("Filtro Geopolítico", test_geopolitical_filter),
        ("Sistema de Imágenes", test_image_system),
        ("API Flask", test_flask_api),
        ("Servicio de Imágenes", test_image_serving)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE TESTS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 RESULTADO FINAL: {passed}/{total} tests exitosos ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 TODOS LOS TESTS PASARON - SISTEMA COMPLETAMENTE FUNCIONAL")
    elif passed >= 3:
        print("⚠️  SISTEMA MAYORMENTE FUNCIONAL - Algunos servicios no disponibles")
    else:
        print("❌ SISTEMA CON PROBLEMAS CRÍTICOS")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)