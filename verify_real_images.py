#!/usr/bin/env python3
"""
Verificar que las imágenes reales se guardaron y el SQL funciona correctamente
"""
import sqlite3
import os

def check_real_images_in_db():
    """Verificar que las imágenes reales están en la base de datos"""
    print("🔍 VERIFICANDO IMÁGENES REALES EN LA BASE DE DATOS")
    print("=" * 60)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar si la columna original_image_url existe
            cursor.execute("PRAGMA table_info(articles)")
            columns = [col[1] for col in cursor.fetchall()]
            has_original_column = 'original_image_url' in columns
            
            print(f"📋 Columna 'original_image_url': {'✅ Existe' if has_original_column else '❌ No existe'}")
            
            # Contar artículos con imágenes reales (locales)
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM articles 
                WHERE image_url LIKE '/static/images/news/%'
            """)
            local_images = cursor.fetchone()['count']
            
            # Contar artículos con placeholders
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM articles 
                WHERE image_url LIKE '%placeholder%'
            """)
            placeholder_images = cursor.fetchone()['count']
            
            print(f"📊 ESTADÍSTICAS:")
            print(f"- Imágenes locales: {local_images}")
            print(f"- Placeholders: {placeholder_images}")
            
            # Mostrar ejemplos de artículos con imágenes reales
            cursor.execute("""
                SELECT id, title, image_url, original_image_url
                FROM articles 
                WHERE image_url LIKE '/static/images/news/%'
                ORDER BY id DESC
                LIMIT 5
            """)
            
            real_images = cursor.fetchall()
            
            print(f"\n🖼️  ARTÍCULOS CON IMÁGENES REALES:")
            for article in real_images:
                print(f"- ID {article['id']}: {article['title'][:50]}...")
                print(f"  Local: {article['image_url']}")
                if has_original_column and article['original_image_url']:
                    print(f"  Original: {article['original_image_url']}")
                
                # Verificar que el archivo existe
                file_path = f"./static/images/news/{os.path.basename(article['image_url'])}"
                exists = os.path.exists(file_path)
                print(f"  Archivo: {'✅ Existe' if exists else '❌ No existe'}")
                print()
                
    except Exception as e:
        print(f"❌ Error: {e}")

def test_sql_with_real_images():
    """Probar el SQL actualizado con imágenes reales"""
    print("🧪 PROBANDO SQL CON IMÁGENES REALES")
    print("=" * 60)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        
        # SQL actualizado que prefiere imágenes locales
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
                    WHEN image_url LIKE '/static/images/news/%' THEN 
                        image_url  -- Usar imagen local si existe
                    WHEN image_url IS NOT NULL AND image_url != '' AND image_url NOT LIKE '%via.placeholder%' THEN 
                        image_url  -- Usar imagen externa válida
                    ELSE 
                        'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=200&fit=crop'
                END as image_url,
                ai_importance
            FROM articles 
            WHERE 
                -- Campos básicos requeridos
                title IS NOT NULL AND title != '' AND
                content IS NOT NULL AND content != '' AND
                
                -- Riesgo válido
                risk_score >= 0.0 AND
                
                -- Excluir artículos HERO (solo para mosaic)
                (content NOT LIKE '%HERO ARTICLE%' OR content IS NULL) AND
                (title NOT LIKE '%HERO%' OR title IS NULL)
            ORDER BY 
                CASE WHEN image_url LIKE '/static/images/news/%' THEN 1 ELSE 2 END,  -- Priorizar imágenes locales
                ai_importance DESC, 
                published_at DESC
            LIMIT 10
        """
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            articles = [dict(row) for row in cursor.fetchall()]
            
        print(f"✅ SQL ejecutado exitosamente: {len(articles)} artículos")
        
        local_count = 0
        external_count = 0
        placeholder_count = 0
        
        for i, article in enumerate(articles):
            image_url = article['image_url']
            
            if image_url.startswith('/static/images/news/'):
                image_type = "🖼️  Local"
                local_count += 1
            elif 'unsplash' in image_url:
                image_type = "🌐 Placeholder"
                placeholder_count += 1
            else:
                image_type = "🔗 Externa"
                external_count += 1
            
            print(f"{i+1}. ID {article['id']}: {article['title'][:50]}...")
            print(f"   {image_type}: {image_url}")
            print()
        
        print(f"📊 TIPOS DE IMAGEN EN RESULTADOS:")
        print(f"- Locales: {local_count}")
        print(f"- Externas: {external_count}")
        print(f"- Placeholders: {placeholder_count}")
        
        return local_count > 0  # Success if we have local images
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 VERIFICACIÓN: Sistema de imágenes reales")
    print("=" * 70)
    
    # Paso 1: Verificar base de datos
    check_real_images_in_db()
    
    print("\n" + "=" * 70)
    
    # Paso 2: Probar SQL
    sql_success = test_sql_with_real_images()
    
    print("=" * 70)
    print("📋 RESULTADO:")
    if sql_success:
        print("🎉 SISTEMA FUNCIONANDO: Artículos con imágenes reales disponibles")
        print("✅ La base de datos contiene imágenes locales")
        print("✅ El SQL prioriza imágenes reales")
        print("💡 Listo para usar en el frontend")
    else:
        print("⚠️  Sistema parcialmente funcional")
        print("💡 Ejecutar más extracciones de imágenes")

if __name__ == "__main__":
    main()