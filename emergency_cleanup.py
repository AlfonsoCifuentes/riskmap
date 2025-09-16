#!/usr/bin/env python3
"""
Script de emergencia para forzar filtros geopolíticos ultra-estrictos
SIN reiniciar servidor - mediante modificación directa de base de datos
"""
import sqlite3
import os
from datetime import datetime

def clean_database_articles():
    """Elimina artículos no geopolíticos directamente de la base de datos"""
    
    print("🔧 LIMPIEZA ULTRA-AGRESIVA DE BASE DE DATOS")
    print("=" * 60)
    
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar artículos antes
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_before = cursor.fetchone()[0]
        print(f"📊 Artículos antes de limpieza: {total_before}")
        
        # ELIMINACIÓN DIRECTA: Remover todo contenido NO geopolítico
        delete_conditions = [
            # Entretenimiento
            "LOWER(title) LIKE '%emmy%'",
            "LOWER(title) LIKE '%emmys%'", 
            "LOWER(title) LIKE '%oscar%'",
            "LOWER(title) LIKE '%film%'",
            "LOWER(title) LIKE '%movie%'",
            "LOWER(title) LIKE '%festival%'",
            "LOWER(title) LIKE '%hamnet%'",
            "LOWER(title) LIKE '%toronto%'",
            "LOWER(title) LIKE '%audience award%'",
            "LOWER(title) LIKE '%choice award%'",
            "LOWER(title) LIKE '%actor%'",
            "LOWER(title) LIKE '%actress%'",
            "LOWER(title) LIKE '%hollywood%'",
            "LOWER(title) LIKE '%variety%'",
            "LOWER(title) LIKE '%deadline%'",
            
            # Tecnología consumer
            "LOWER(title) LIKE '%iphone%'",
            "LOWER(title) LIKE '%apple%'", 
            "LOWER(title) LIKE '%9to5mac%'",
            "LOWER(title) LIKE '%sales off%'",
            "LOWER(title) LIKE '%air launch%'",
            "LOWER(title) LIKE '%smartphone%'",
            "LOWER(title) LIKE '%nintendo%'",
            "LOWER(title) LIKE '%google%'",
            "LOWER(title) LIKE '%meta%'",
            "LOWER(title) LIKE '%facebook%'",
            "LOWER(title) LIKE '%tesla%'",
            
            # Deportes
            "LOWER(title) LIKE '%sport%'",
            "LOWER(title) LIKE '%game%'",
            "LOWER(title) LIKE '%nfl%'",
            "LOWER(title) LIKE '%nba%'",
            "LOWER(title) LIKE '%team%'",
            "LOWER(title) LIKE '%player%'",
            "LOWER(title) LIKE '%match%'",
            
            # Fuentes no geopolíticas
            "source LIKE '%Variety%'",
            "source LIKE '%9to5Mac%'",
            "source LIKE '%Entertainment%'",
            "source LIKE '%ESPN%'",
            "source LIKE '%Sports%'",
            "source LIKE '%TMZ%'",
            "source LIKE '%People%'",
            "source LIKE '%Deadline%'"
        ]
        
        deleted_total = 0
        
        for condition in delete_conditions:
            cursor.execute(f"SELECT COUNT(*) FROM articles WHERE {condition}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"🗑️  Eliminando {count} artículos: {condition}")
                cursor.execute(f"DELETE FROM articles WHERE {condition}")
                deleted_total += count
        
        # Eliminar artículos sin imagen o con imagen placeholder
        print("🖼️  Eliminando artículos sin imagen real...")
        cursor.execute("""
            DELETE FROM articles WHERE 
                (image_url IS NULL OR image_url = '' OR
                 image_url LIKE '%placeholder%' OR
                 image_url LIKE '%default%' OR
                 image_url LIKE '%generic%') AND
                (original_image_url IS NULL OR original_image_url = '')
        """)
        no_image_deleted = cursor.rowcount
        deleted_total += no_image_deleted
        print(f"🗑️  Eliminados {no_image_deleted} artículos sin imagen")
        
        conn.commit()
        
        # Contar después
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_after = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 RESULTADOS DE LIMPIEZA:")
        print(f"   Antes: {total_before} artículos")
        print(f"   Eliminados: {deleted_total} artículos")
        print(f"   Después: {total_after} artículos")
        print(f"   Reducción: {((deleted_total/total_before)*100):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")
        return False

def verify_remaining_articles():
    """Verifica qué artículos quedan después de la limpieza"""
    
    print("\n🔍 VERIFICANDO ARTÍCULOS RESTANTES")
    print("-" * 40)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, source, image_url, original_image_url, risk_level
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        articles = cursor.fetchall()
        conn.close()
        
        if not articles:
            print("❌ No hay artículos restantes")
            return
            
        print(f"📰 {len(articles)} artículos más recientes:")
        
        for i, (title, source, img_url, orig_img, risk) in enumerate(articles, 1):
            # Verificar si es geopolítico
            title_lower = title.lower()
            is_geo = any(x in title_lower for x in [
                'ukraine', 'russia', 'china', 'israel', 'palestine', 'gaza',
                'nato', 'war', 'military', 'conflict', 'security', 'political',
                'government', 'minister', 'president', 'diplomacy', 'sanctions'
            ])
            
            # Verificar imagen
            has_image = bool(img_url or orig_img)
            
            geo_icon = "✅" if is_geo else "❌"
            img_icon = "🖼️" if has_image else "❌"
            
            print(f"   {i:2d}. {geo_icon} {img_icon} {title[:50]}... - {source}")
            
    except Exception as e:
        print(f"❌ Error verificando artículos: {e}")

def fix_image_paths():
    """Corrige rutas de imágenes para evitar errores 404"""
    
    print("\n🔧 CORRIGIENDO RUTAS DE IMÁGENES")
    print("-" * 40)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar qué imágenes tienen rutas problemáticas
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE image_url LIKE '/static/images/news/%'
            AND original_image_url IS NOT NULL
        """)
        
        problematic_count = cursor.fetchone()[0]
        
        if problematic_count > 0:
            print(f"🔧 Corrigiendo {problematic_count} rutas de imágenes problemáticas...")
            
            # Limpiar rutas de imágenes que causan 404
            cursor.execute("""
                UPDATE articles 
                SET image_url = CASE 
                    WHEN original_image_url IS NOT NULL AND original_image_url != '' 
                    THEN original_image_url
                    ELSE NULL
                END
                WHERE image_url LIKE '/static/images/news/%'
            """)
            
            conn.commit()
            print(f"✅ Rutas corregidas")
        else:
            print("✅ No hay rutas problemáticas")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error corrigiendo imágenes: {e}")

def main():
    """Función principal de limpieza de emergencia"""
    
    print("🚨 LIMPIEZA DE EMERGENCIA - FILTROS GEOPOLÍTICOS")
    print("=" * 60)
    print(f"🕒 Iniciado: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Paso 1: Limpiar base de datos
    success = clean_database_articles()
    
    if not success:
        print("❌ Falló la limpieza de base de datos")
        return
    
    # Paso 2: Corregir rutas de imágenes
    fix_image_paths()
    
    # Paso 3: Verificar resultado
    verify_remaining_articles()
    
    print("\n" + "=" * 60)
    print("🎯 LIMPIEZA COMPLETADA")
    print("💡 PRÓXIMOS PASOS:")
    print("   1. Recarga la página web (F5)")
    print("   2. Deberías ver SOLO artículos geopolíticos")
    print("   3. Todas las imágenes deberían cargar correctamente")
    print("   4. Si persisten problemas, reinicia servidor")
    
    print(f"\n🕒 Finalizado: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()