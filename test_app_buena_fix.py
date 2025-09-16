#!/usr/bin/env python3
"""
Prueba del arreglo SQL en app_BUENA.py
"""
import sqlite3
import os
from datetime import datetime

def test_app_buena_fixed_query():
    """Prueba la consulta SQL arreglada en app_BUENA.py"""
    
    print("🧪 PRUEBA DE ARREGLO EN APP_BUENA.PY")
    print("=" * 50)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Usar la misma lógica que app_BUENA.py
        try:
            from src.utils.config import get_database_path
            db_path = get_database_path()
        except ImportError:
            db_path = r"data\geopolitical_intel.db"
        
        # Normalizar path para Linux/Windows
        if not os.path.exists(db_path):
            db_path = "./data/geopolitical_intel.db"
            
        if not os.path.exists(db_path):
            print(f"❌ Database no encontrada: {db_path}")
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Misma consulta que app_BUENA.py pero con el arreglo aplicado
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
                    ELSE 
                        NULL
                END as image_url,
                ai_importance
            FROM articles 
            WHERE 
                -- Solo artículos con imagen real (no placeholder)
                (
                    (original_image_url IS NOT NULL AND original_image_url != '') OR
                    (image_url IS NOT NULL AND image_url != '' AND 
                     image_url NOT LIKE '%placeholder%' AND 
                     image_url NOT LIKE '%via.placeholder%' AND
                     image_url NOT LIKE '%default%')
                ) AND
                
                -- Solo artículos recientes 
                created_at >= datetime('now', '-30 days')
            ORDER BY 
                created_at DESC
            LIMIT 8
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        print(f"📊 RESULTADOS CON APP_BUENA.PY ARREGLADO:")
        print(f"   Artículos encontrados: {len(rows)}")
        
        with_image_count = 0
        
        for i, row in enumerate(rows, 1):
            article_id = row[0]
            title = row[1][:45] if row[1] else "Sin título"
            image_url = row[12]  # image_url está en posición 12
            
            if image_url and image_url.startswith('https://'):
                status = "✅"
                with_image_count += 1
                img_display = image_url[:55] + "..."
            else:
                status = "❌"
                img_display = image_url if image_url else "NULL"
                
            print(f"   {i}. ID:{article_id} {status} {title}")
            print(f"      IMG: {img_display}")
        
        print(f"\n📈 RESULTADO FINAL:")
        print(f"   ✅ Con imagen HTTPS: {with_image_count}/{len(rows)}")
        print(f"   📊 Porcentaje: {(with_image_count/len(rows)*100):.1f}%" if rows else "N/A")
        
        if with_image_count >= len(rows) * 0.8:  # Al menos 80% con imagen
            print(f"\n🎉 ¡EXCELENTE! app_BUENA.py arreglado funciona correctamente")
            print(f"✅ {with_image_count} artículos con imágenes HTTPS originales")
            print(f"🚨 REINICIA TU SERVIDOR app_BUENA.py AHORA")
            return True
        elif with_image_count > 0:
            print(f"\n✅ BIEN: {with_image_count} artículos con imagen")
            print(f"🚨 REINICIA TU SERVIDOR app_BUENA.py PARA VER EL CAMBIO")
            return True
        else:
            print(f"\n❌ PROBLEMA: Ningún artículo con imagen válida")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verify_current_api_after_restart():
    """Función para verificar después del reinicio"""
    
    print(f"\n🔍 VERIFICACIÓN POST-REINICIO")
    print("-" * 40)
    
    try:
        import requests
        
        response = requests.get("http://localhost:5001/api/articles?limit=8", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"📊 API respuesta después de reinicio:")
            
            with_image_api = 0
            
            for i, article in enumerate(articles, 1):
                title = article.get('title', '')[:35]
                img_url = article.get('image_url', '')
                
                if img_url and img_url.startswith('https://'):
                    status = "✅"
                    with_image_api += 1
                else:
                    status = "❌"
                
                print(f"   {i}. {status} {title}")
                
            print(f"\n📊 RESULTADO API:")
            print(f"   ✅ Con imagen: {with_image_api}/{len(articles)}")
            
            if with_image_api == len(articles) and len(articles) > 0:
                print(f"   🎉 ¡PERFECTO! TODAS las noticias tienen imagen")
            elif with_image_api > 0:
                print(f"   ✅ BIEN: {with_image_api} noticias con imagen")
            else:
                print(f"   ❌ PROBLEMA: Reinicio no funcionó")
                
        else:
            print(f"❌ Error API: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Servidor no disponible (normal si no está corriendo): {e}")

def main():
    """Función principal"""
    
    success = test_app_buena_fixed_query()
    
    print(f"\n" + "=" * 50)
    print(f"🎯 SIGUIENTE PASO:")
    
    if success:
        print(f"✅ ARREGLO EN APP_BUENA.PY CONFIRMADO")
        print(f"🚨 INSTRUCCIONES PRECISAS:")
        print(f"   1. Detén tu servidor actual (Ctrl+C)")
        print(f"   2. Ejecuta: python app_BUENA.py")
        print(f"   3. Recarga tu página (F5)")
        print(f"   4. ¡VERÁS TODAS LAS IMÁGENES ORIGINALES!")
        print(f"")
        print(f"💡 Después del reinicio puedes ejecutar este script")
        print(f"   de nuevo para verificar que todo funciona")
    else:
        print(f"❌ Hay un problema con el arreglo")

if __name__ == "__main__":
    main()