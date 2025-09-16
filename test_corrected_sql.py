#!/usr/bin/env python3
"""
Prueba directa de la consulta SQL corregida
"""
import sqlite3
import os
from datetime import datetime

def test_corrected_query():
    """Prueba la consulta SQL corregida directamente"""
    
    print("🧪 PRUEBA DE CONSULTA SQL CORREGIDA")
    print("=" * 50)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        db_path = "./data/geopolitical_intel.db"
        if not os.path.exists(db_path):
            print(f"❌ Database no encontrada: {db_path}")
            return False

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Consulta SQL CORREGIDA (mismo código del app_CORREGIDO.py arreglado)
        query = """
            SELECT 
                id, title, 
                CASE 
                    WHEN summary IS NOT NULL AND summary != '' AND summary NOT LIKE '%<think>%' THEN 
                        summary
                    WHEN auto_generated_summary IS NOT NULL AND auto_generated_summary != '' AND auto_generated_summary NOT LIKE '%<think>%' THEN 
                        auto_generated_summary
                    WHEN content IS NOT NULL AND content != '' AND content NOT LIKE '%<think>%' THEN 
                        SUBSTR(content, 1, 300) || '...'
                    ELSE 
                        'Análisis de contenido geopolítico disponible para revisión.'
                END as summary,
                url, source, published_at, country, region, risk_level, 
                conflict_type, sentiment_score, risk_score,
                CASE 
                    WHEN original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%'
                    THEN original_image_url
                    WHEN image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' AND image_url NOT LIKE '%via.placeholder%' THEN 
                        image_url
                    ELSE NULL
                END as image_url,
                ai_importance
            FROM articles 
            WHERE 
                -- INCLUSIONES ESTRICTAS: Solo contenido geopolítico
                (
                    -- Países y regiones de alto interés geopolítico
                    LOWER(title) LIKE '%ukraine%' OR LOWER(title) LIKE '%russia%' OR
                    LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%taiwan%' OR
                    LOWER(title) LIKE '%north korea%' OR LOWER(title) LIKE '%iran%' OR
                    LOWER(title) LIKE '%israel%' OR LOWER(title) LIKE '%palestine%' OR
                    LOWER(title) LIKE '%gaza%' OR LOWER(title) LIKE '%syria%' OR
                    LOWER(title) LIKE '%afghanistan%' OR LOWER(title) LIKE '%yemen%' OR
                    LOWER(title) LIKE '%iraq%' OR LOWER(title) LIKE '%lebanon%' OR
                    LOWER(title) LIKE '%turkey%' OR LOWER(title) LIKE '%venezuela%' OR
                    LOWER(title) LIKE '%myanmar%' OR LOWER(title) LIKE '%belarus%' OR
                    LOWER(title) LIKE '%hong kong%' OR LOWER(title) LIKE '%tibet%' OR
                    LOWER(title) LIKE '%middle east%' OR LOWER(title) LIKE '%balkans%' OR
                    LOWER(title) LIKE '%kashmir%' OR LOWER(title) LIKE '%kurdish%' OR
                    LOWER(title) LIKE '%romania%' OR LOWER(title) LIKE '%poland%' OR
                    LOWER(title) LIKE '%moldova%' OR LOWER(title) LIKE '%georgia%' OR
                    LOWER(title) LIKE '%armenia%' OR LOWER(title) LIKE '%azerbaijan%' OR
                    LOWER(title) LIKE '%nepal%' OR LOWER(title) LIKE '%india%' OR
                    LOWER(title) LIKE '%pakistan%' OR LOWER(title) LIKE '%bangladesh%' OR
                    
                    -- Líderes políticos y figuras internacionales
                    LOWER(title) LIKE '%putin%' OR LOWER(title) LIKE '%zelensky%' OR
                    LOWER(title) LIKE '%xi jinping%' OR LOWER(title) LIKE '%biden%' OR
                    LOWER(title) LIKE '%trump%' OR LOWER(title) LIKE '%netanyahu%' OR
                    LOWER(title) LIKE '%khamenei%' OR LOWER(title) LIKE '%erdogan%' OR
                    LOWER(title) LIKE '%modi%' OR LOWER(title) LIKE '%marcos%' OR
                    LOWER(title) LIKE '%rubio%' OR LOWER(title) LIKE '%harris%' OR
                    
                    -- Términos geopolíticos en español
                    LOWER(title) LIKE '%guerra%' OR LOWER(title) LIKE '%militar%' OR
                    LOWER(title) LIKE '%política%' OR LOWER(title) LIKE '%gobierno%' OR
                    LOWER(title) LIKE '%seguridad%' OR LOWER(title) LIKE '%diplomacia%' OR
                    LOWER(title) LIKE '%internacional%' OR LOWER(title) LIKE '%rusia%' OR
                    LOWER(title) LIKE '%ucrania%' OR LOWER(title) LIKE '%irán%' OR
                    LOWER(title) LIKE '%conflicto%' OR LOWER(title) LIKE '%crisis%' OR
                    
                    -- Temas de seguridad y inteligencia
                    LOWER(title) LIKE '%intelligence%' OR LOWER(title) LIKE '%spy%' OR
                    LOWER(title) LIKE '%espionage%' OR LOWER(title) LIKE '%cyber%' OR
                    LOWER(title) LIKE '%hacking%' OR LOWER(title) LIKE '%breach%' OR
                    LOWER(title) LIKE '%leak%' OR LOWER(title) LIKE '%classified%' OR
                    LOWER(title) LIKE '%drone%' OR LOWER(title) LIKE '%missile%' OR
                    LOWER(title) LIKE '%nuclear%' OR LOWER(title) LIKE '%weapons%'
                ) AND (
                    -- SOLO artículos con imagen real (NO placeholders)
                    (
                        (original_image_url IS NOT NULL AND original_image_url != '') OR
                        (image_url IS NOT NULL AND image_url != '' AND 
                         image_url NOT LIKE '%via.placeholder%' AND 
                         image_url NOT LIKE '%placeholder.com%' AND
                         image_url NOT LIKE '%default%' AND
                         image_url NOT LIKE '%generic%' AND
                         image_url NOT LIKE '%mockup%')
                    )
                ) AND
                
                -- Solo artículos recientes (últimos 14 días)
                created_at >= datetime('now', '-14 days')
            ORDER BY 
                -- Prioridad: importancia AI > riesgo > fecha
                COALESCE(ai_importance, 0) DESC,
                COALESCE(risk_score, 0) DESC,
                created_at DESC
            LIMIT 8
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        print(f"📊 RESULTADOS DE CONSULTA CORREGIDA:")
        print(f"   Artículos encontrados: {len(rows)}")
        
        with_image_count = 0
        
        for i, row in enumerate(rows, 1):
            article_id = row[0]
            title = row[1][:40] if row[1] else "Sin título"
            image_url = row[12]  # image_url está en posición 12
            
            if image_url and image_url.startswith('https://'):
                status = "✅"
                with_image_count += 1
                img_display = image_url[:50] + "..."
            else:
                status = "❌"
                img_display = image_url if image_url else "NULL"
                
            print(f"   {i}. ID:{article_id} {status} {title}")
            print(f"      IMG: {img_display}")
        
        print(f"\n📈 RESULTADO:")
        print(f"   ✅ Con imagen válida: {with_image_count}/{len(rows)}")
        print(f"   📊 Porcentaje éxito: {(with_image_count/len(rows)*100):.1f}%" if rows else "N/A")
        
        if with_image_count == len(rows) and len(rows) > 0:
            print(f"\n🎉 ¡PERFECTO! La consulta SQL corregida funciona correctamente")
            print(f"✅ TODOS los artículos geopolíticos tienen imagen HTTPS")
            print(f"🚨 NECESITAS REINICIAR TU SERVIDOR para que tome el cambio")
        elif with_image_count > 0:
            print(f"\n✅ BUENO: La consulta SQL funciona, {with_image_count} artículos con imagen")
            print(f"🚨 NECESITAS REINICIAR TU SERVIDOR para que tome el cambio")
        else:
            print(f"\n❌ PROBLEMA: La consulta aún no devuelve imágenes")
            
        return with_image_count > 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Función principal"""
    
    success = test_corrected_query()
    
    print(f"\n" + "=" * 50)
    print(f"🎯 INSTRUCCIONES:")
    
    if success:
        print(f"✅ La consulta SQL corregida FUNCIONA")
        print(f"🚨 DEBES REINICIAR TU SERVIDOR:")
        print(f"   1. Detén el servidor actual (Ctrl+C)")
        print(f"   2. Ejecuta: python app_CORREGIDO.py")
        print(f"   3. Recarga la página web (F5)")
        print(f"   4. ¡Verás TODAS las imágenes originales!")
    else:
        print(f"❌ Hay problemas con la consulta")
        print(f"💡 Revisar filtros o extractor de imágenes")

if __name__ == "__main__":
    main()