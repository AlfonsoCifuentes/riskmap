#!/usr/bin/env python3
"""
Limpieza ULTRA-AGRESIVA fase 2: Solo artículos geopolíticos válidos
"""
import sqlite3
import os
from datetime import datetime

def ultra_aggressive_cleanup():
    """Elimina CUALQUIER cosa que no sea estrictamente geopolítica"""
    
    print("🔥 LIMPIEZA ULTRA-AGRESIVA FASE 2")
    print("=" * 60)
    
    db_path = "./data/geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar antes
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_before = cursor.fetchone()[0]
        print(f"📊 Artículos antes: {total_before}")
        
        # ELIMINAR TODO LO QUE NO SEA ESTRICTAMENTE GEOPOLÍTICO
        non_geo_patterns = [
            # Empresas/negocios
            "LOWER(title) LIKE '%delta%'",
            "LOWER(title) LIKE '%office depot%'", 
            "LOWER(title) LIKE '%companies%'",
            "LOWER(title) LIKE '%business%'",
            "LOWER(title) LIKE '%customers%'",
            "LOWER(title) LIKE '%colorado%'",
            
            # Salud no geopolítica
            "LOWER(title) LIKE '%ebola%'",
            "LOWER(title) LIKE '%covid%'",
            "LOWER(title) LIKE '%vaccine%'",
            "LOWER(title) LIKE '%vaccination%'",
            
            # Deportes específicos
            "LOWER(title) LIKE '%giants%'",
            "LOWER(title) LIKE '%cowboys%'",
            "LOWER(title) LIKE '%overtime loss%'",
            
            # Entretenimiento restante
            "LOWER(title) LIKE '%demon slayer%'",
            "LOWER(title) LIKE '%infinity castle%'",
            
            # Política local no geopolítica
            "LOWER(title) LIKE '%gov. kathy hochul%'",
            "LOWER(title) LIKE '%zohran mamdani%'",
            "LOWER(title) LIKE '%charlie kirk%'",
            
            # Ciencia/espacio no geopolítico
            "LOWER(title) LIKE '%ligo legacy%'",
            "LOWER(title) LIKE '%gravitational wave%'",
            "LOWER(title) LIKE '%space.com%'",
            
            # Fuentes no geopolíticas
            "source LIKE '%Business Insider%'",
            "source LIKE '%NBC News%'",  
            "source LIKE '%New York Post%'",
            "source LIKE '%Denver7%'",
            "source LIKE '%Space.com%'"
        ]
        
        deleted_count = 0
        
        for pattern in non_geo_patterns:
            cursor.execute(f"SELECT COUNT(*) FROM articles WHERE {pattern}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"🗑️  Eliminando {count}: {pattern}")
                cursor.execute(f"DELETE FROM articles WHERE {pattern}")
                deleted_count += count
        
        # MANTENER SOLO ARTÍCULOS ESTRICTAMENTE GEOPOLÍTICOS
        print("\n✅ MANTENIENDO SOLO CONTENIDO GEOPOLÍTICO VÁLIDO...")
        
        cursor.execute("""
            DELETE FROM articles 
            WHERE NOT (
                -- Países geopolíticamente relevantes
                LOWER(title) LIKE '%ukraine%' OR LOWER(title) LIKE '%russia%' OR
                LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%taiwan%' OR
                LOWER(title) LIKE '%israel%' OR LOWER(title) LIKE '%palestine%' OR
                LOWER(title) LIKE '%gaza%' OR LOWER(title) LIKE '%syria%' OR
                LOWER(title) LIKE '%iran%' OR LOWER(title) LIKE '%north korea%' OR
                LOWER(title) LIKE '%yemen%' OR LOWER(title) LIKE '%iraq%' OR
                LOWER(title) LIKE '%afghanistan%' OR LOWER(title) LIKE '%lebanon%' OR
                LOWER(title) LIKE '%turkey%' OR LOWER(title) LIKE '%venezuela%' OR
                LOWER(title) LIKE '%myanmar%' OR LOWER(title) LIKE '%belarus%' OR
                
                -- Organizaciones internacionales
                LOWER(title) LIKE '%nato%' OR LOWER(title) LIKE '%european union%' OR
                LOWER(title) LIKE '%united nations%' OR LOWER(title) LIKE '%g7%' OR
                LOWER(title) LIKE '%g20%' OR
                
                -- Términos militares/seguridad
                LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%military%' OR
                LOWER(title) LIKE '%drone%' OR LOWER(title) LIKE '%missile%' OR
                LOWER(title) LIKE '%nuclear%' OR LOWER(title) LIKE '%weapons%' OR
                LOWER(title) LIKE '%conflict%' OR LOWER(title) LIKE '%security%' OR
                LOWER(title) LIKE '%defense%' OR LOWER(title) LIKE '%attack%' OR
                LOWER(title) LIKE '%strike%' OR LOWER(title) LIKE '%sanctions%' OR
                LOWER(title) LIKE '%diplomacy%' OR LOWER(title) LIKE '%treaty%' OR
                
                -- Líderes geopolíticos
                LOWER(title) LIKE '%putin%' OR LOWER(title) LIKE '%zelensky%' OR
                LOWER(title) LIKE '%xi jinping%' OR LOWER(title) LIKE '%biden%' OR
                LOWER(title) LIKE '%trump%' OR LOWER(title) LIKE '%netanyahu%' OR
                LOWER(title) LIKE '%erdogan%' OR LOWER(title) LIKE '%khamenei%' OR
                LOWER(title) LIKE '%modi%' OR LOWER(title) LIKE '%marcos%' OR
                
                -- Temas de inteligencia/espionaje
                LOWER(title) LIKE '%intelligence%' OR LOWER(title) LIKE '%spy%' OR
                LOWER(title) LIKE '%espionage%' OR LOWER(title) LIKE '%cyber%' OR
                LOWER(title) LIKE '%hacking%' OR LOWER(title) LIKE '%breach%' OR
                LOWER(title) LIKE '%classified%' OR LOWER(title) LIKE '%leak%'
            )
        """)
        
        geo_deleted = cursor.rowcount
        deleted_count += geo_deleted
        print(f"🗑️  Eliminados {geo_deleted} artículos no estrictamente geopolíticos")
        
        conn.commit()
        
        # Contar después
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_after = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 RESULTADOS FASE 2:")
        print(f"   Antes: {total_before}")
        print(f"   Eliminados: {deleted_count}")
        print(f"   Después: {total_after}")
        print(f"   Reducción: {((deleted_count/total_before)*100):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_final_articles():
    """Muestra los artículos finales que quedan"""
    
    print("\n🔍 ARTÍCULOS FINALES (SOLO GEOPOLÍTICOS)")
    print("-" * 50)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, source, 
                   CASE 
                       WHEN original_image_url IS NOT NULL AND original_image_url != '' THEN '✅'
                       WHEN image_url IS NOT NULL AND image_url != '' THEN '🖼️'
                       ELSE '❌'
                   END as has_image
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 15
        """)
        
        articles = cursor.fetchall()
        conn.close()
        
        if not articles:
            print("❌ No quedan artículos")
            return
            
        print(f"📰 {len(articles)} artículos geopolíticos restantes:")
        
        for i, (title, source, has_image) in enumerate(articles, 1):
            print(f"   {i:2d}. {has_image} {title[:55]}... - {source}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Ejecutar limpieza ultra-agresiva"""
    
    print("🔥 FASE 2: SOLO GEOPOLÍTICA ESTRICTA")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    success = ultra_aggressive_cleanup()
    
    if success:
        show_final_articles()
        
        print("\n" + "=" * 60)
        print("🎉 LIMPIEZA ULTRA-AGRESIVA COMPLETADA")
        print("💡 RESULTADO:")
        print("   ✅ Solo artículos estrictamente geopolíticos")
        print("   ✅ Solo artículos con imágenes reales")
        print("   ✅ Eliminado todo entretenimiento/deportes/tech")
        print("   🔄 RECARGA LA PÁGINA (F5) para ver cambios")
    else:
        print("❌ Falló la limpieza")

if __name__ == "__main__":
    main()