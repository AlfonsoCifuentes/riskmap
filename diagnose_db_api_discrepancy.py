#!/usr/bin/env python3
"""
Verificador directo de base de datos y API
"""
import sqlite3
import requests
from datetime import datetime

def check_database_images():
    """Verifica directamente en la base de datos"""
    
    print("🔍 VERIFICACIÓN DIRECTA DE BASE DE DATOS")
    print("=" * 50)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar artículos recientes con sus imágenes
        cursor.execute("""
            SELECT id, title, image_url, original_image_url
            FROM articles 
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        articles = cursor.fetchall()
        
        print(f"📰 Últimos 10 artículos en BASE DE DATOS:")
        
        with_image_db = 0
        
        for id, title, img_url, orig_url in articles:
            title_short = title[:40] if title else "Sin título"
            
            if img_url and img_url.startswith('https://'):
                status = "✅"
                with_image_db += 1
                img_display = img_url[:50] + "..."
            else:
                status = "❌"
                img_display = img_url if img_url else "NULL"
            
            print(f"   {id}: {status} {title_short}")
            print(f"       IMG: {img_display}")
        
        conn.close()
        
        print(f"\n📊 ESTADO BASE DE DATOS:")
        print(f"   ✅ Con imagen: {with_image_db}/10")
        print(f"   📊 Porcentaje: {(with_image_db/10*100):.1f}%")
        
        return with_image_db
        
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")
        return 0

def check_api_response():
    """Verifica qué devuelve la API"""
    
    print(f"\n🌐 VERIFICACIÓN API")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:5001/api/articles?limit=10", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"📊 Artículos devueltos por API: {len(articles)}")
            
            with_image_api = 0
            
            for i, article in enumerate(articles, 1):
                title = article.get('title', '')[:35]
                img_url = article.get('image_url', '')
                art_id = article.get('id', 'N/A')
                
                if img_url and img_url.startswith('https://'):
                    status = "✅"
                    with_image_api += 1
                    img_display = img_url[:45] + "..."
                else:
                    status = "❌"
                    img_display = img_url if img_url else "NULL"
                
                print(f"   {i}. ID:{art_id} {status} {title}")
                print(f"      IMG: {img_display}")
            
            print(f"\n📊 ESTADO API:")
            print(f"   ✅ Con imagen: {with_image_api}/{len(articles)}")
            print(f"   📊 Porcentaje: {(with_image_api/len(articles)*100):.1f}%" if articles else "0%")
            
            return with_image_api, len(articles)
            
        else:
            print(f"❌ Error API: {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}")
            return 0, 0
            
    except Exception as e:
        print(f"❌ Error API: {e}")
        return 0, 0

def force_api_refresh():
    """Intenta forzar actualización del cache/API"""
    
    print(f"\n🔄 FORZANDO ACTUALIZACIÓN")
    print("-" * 30)
    
    try:
        # Probar endpoint de status para ver si el servidor responde
        response = requests.get("http://localhost:5001/api/status", timeout=5)
        print(f"Status endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Sistema: {data.get('status', 'unknown')}")
            print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
        
        # Probar múltiples calls para limpiar cache
        for i in range(3):
            response = requests.get(f"http://localhost:5001/api/articles?limit=5&_bust={i}", timeout=5)
            print(f"   Cache bust {i+1}: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error refrescando: {e}")

def diagnose_discrepancy():
    """Diagnostica por qué hay discrepancia entre BD y API"""
    
    print(f"\n🔬 DIAGNÓSTICO DE DISCREPANCIA")
    print("-" * 40)
    
    # 1. Verificar BD
    db_images = check_database_images()
    
    # 2. Verificar API
    api_images, api_total = check_api_response()
    
    # 3. Analizar discrepancia
    print(f"\n🧮 ANÁLISIS:")
    print(f"   Base de datos: {db_images}/10 con imagen")
    print(f"   API respuesta: {api_images}/{api_total} con imagen")
    
    if db_images > 0 and api_images == 0:
        print(f"\n⚠️ PROBLEMA DETECTADO:")
        print(f"   - Las imágenes SÍ están en la base de datos")
        print(f"   - Pero la API NO las está devolviendo")
        print(f"   - Posible cache o problema en la consulta SQL del backend")
        
        # Intentar refrescar
        force_api_refresh()
        
        # Verificar de nuevo
        print(f"\n🔄 VERIFICACIÓN POST-REFRESH:")
        api_images2, api_total2 = check_api_response()
        
        if api_images2 > api_images:
            print(f"✅ MEJORÓ: Ahora {api_images2}/{api_total2} con imagen")
        else:
            print(f"❌ SIN CAMBIOS: Aún {api_images2}/{api_total2} con imagen")
            
    elif db_images == 0:
        print(f"\n❌ PROBLEMA: Las imágenes no se guardaron en la BD")
        
    elif api_images == db_images:
        print(f"\n✅ CONSISTENTE: BD y API coinciden")

def main():
    """Función principal de diagnóstico"""
    
    print("🛠️ DIAGNÓSTICO COMPLETO BD vs API")
    print("=" * 50)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    diagnose_discrepancy()
    
    print(f"\n" + "=" * 50)
    print(f"💡 CONCLUSIÓN:")
    print(f"   Si las imágenes están en BD pero no en API:")
    print(f"   1. Revisar consulta SQL en app_CORREGIDO.py")
    print(f"   2. Reiniciar el servidor si es necesario")
    print(f"   3. Verificar filtros de la API")

if __name__ == "__main__":
    main()