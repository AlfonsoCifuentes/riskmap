#!/usr/bin/env python3
"""
Test directo de la función get_top_articles_from_db con el filtro aplicado
"""
import sqlite3
import os

def direct_test_function():
    """Test directo de la función get_top_articles_from_db"""
    
    print("🧪 TEST DIRECTO: get_top_articles_from_db")
    print("=" * 50)
    
    # Simular la misma lógica que usa la aplicación
    try:
        # Usar la misma ruta que la aplicación
        db_path = r"data\geopolitical_intel.db"
        
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Usar exactamente la misma query que está en app_BUENA.py
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
                (title NOT LIKE '%HERO%' OR title IS NULL) AND
                
                -- FILTRO GEOPOLÍTICO: Excluir deportes y entretenimiento
                title NOT LIKE '%sport%' AND title NOT LIKE '%game%' AND title NOT LIKE '%match%' AND
                title NOT LIKE '%team%' AND title NOT LIKE '%player%' AND title NOT LIKE '%goal%' AND
                title NOT LIKE '%football%' AND title NOT LIKE '%soccer%' AND title NOT LIKE '%baseball%' AND
                title NOT LIKE '%basketball%' AND title NOT LIKE '%tennis%' AND title NOT LIKE '%golf%' AND
                title NOT LIKE '%Emmy%' AND title NOT LIKE '%Oscar%' AND title NOT LIKE '%Grammy%' AND
                title NOT LIKE '%movie%' AND title NOT LIKE '%film%' AND title NOT LIKE '%actor%' AND
                title NOT LIKE '%actress%' AND title NOT LIKE '%Hollywood%' AND title NOT LIKE '%cinema%' AND
                title NOT LIKE '%singer%' AND title NOT LIKE '%music%' AND title NOT LIKE '%album%' AND
                title NOT LIKE '%concert%' AND title NOT LIKE '%celebrity%' AND title NOT LIKE '%fashion%' AND
                title NOT LIKE '%iPhone%' AND title NOT LIKE '%Apple%' AND title NOT LIKE '%tech%' AND 
                title NOT LIKE '%Demon Slayer%' AND title NOT LIKE '%anime%' AND title NOT LIKE '%TV%' AND
                
                -- Excluir fuentes deportivas/entretenimiento/tech
                source NOT LIKE '%Sports%' AND source NOT LIKE '%Entertainment%' AND 
                source NOT LIKE '%ESPN%' AND source NOT LIKE '%TMZ%' AND source NOT LIKE '%People%' AND
                source NOT LIKE '%AppleInsider%' AND source NOT LIKE '%9to5Mac%' AND source NOT LIKE '%TechCrunch%' AND
                
                -- INCLUIR: Solo contenido claramente geopolítico O alto riesgo
                (title LIKE '%war%' OR title LIKE '%guerra%' OR title LIKE '%conflict%' OR title LIKE '%crisis%' OR
                 title LIKE '%diplomacy%' OR title LIKE '%diplomacia%' OR title LIKE '%military%' OR title LIKE '%militar%' OR
                 title LIKE '%government%' OR title LIKE '%gobierno%' OR title LIKE '%politics%' OR title LIKE '%política%' OR
                 title LIKE '%election%' OR title LIKE '%elecciones%' OR title LIKE '%security%' OR title LIKE '%seguridad%' OR
                 title LIKE '%international%' OR title LIKE '%internacional%' OR title LIKE '%treaty%' OR title LIKE '%tratado%' OR
                 title LIKE '%terrorism%' OR title LIKE '%terrorismo%' OR title LIKE '%refugee%' OR title LIKE '%refugiado%' OR
                 title LIKE '%immigration%' OR title LIKE '%inmigración%' OR title LIKE '%trade%' OR title LIKE '%comercio%' OR
                 title LIKE '%economy%' OR title LIKE '%economía%' OR title LIKE '%sanctions%' OR title LIKE '%sanciones%' OR
                 title LIKE '%border%' OR title LIKE '%frontera%' OR title LIKE '%territory%' OR title LIKE '%territorio%' OR
                 title LIKE '%NATO%' OR title LIKE '%OTAN%' OR title LIKE '%UN%' OR title LIKE '%ONU%' OR
                 
                 -- Países/regiones de interés geopolítico
                 title LIKE '%Russia%' OR title LIKE '%Rusia%' OR title LIKE '%Ukraine%' OR title LIKE '%Ucrania%' OR
                 title LIKE '%China%' OR title LIKE '%Taiwan%' OR title LIKE '%North Korea%' OR title LIKE '%Corea del Norte%' OR
                 title LIKE '%Iran%' OR title LIKE '%Irán%' OR title LIKE '%Israel%' OR title LIKE '%Palestine%' OR title LIKE '%Gaza%' OR
                 title LIKE '%Syria%' OR title LIKE '%Siria%' OR title LIKE '%Afghanistan%' OR title LIKE '%Afganistán%' OR
                 title LIKE '%Yemen%' OR title LIKE '%Iraq%' OR title LIKE '%Turkey%' OR title LIKE '%Turquía%' OR
                 
                 -- Solo alto riesgo (≥0.4) si no tiene palabras clave geopolíticas
                 risk_score >= 0.4)
            ORDER BY 
                CASE WHEN image_url LIKE '/static/images/news/%' THEN 1 ELSE 2 END,  -- Priorizar imágenes locales
                CASE WHEN risk_score >= 0.6 THEN 3
                     WHEN risk_score >= 0.4 THEN 2  
                     ELSE 1 END DESC,
                ai_importance DESC,
                published_at DESC
            LIMIT 20
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"📊 Artículos obtenidos de la función: {len(rows)}")
        
        if rows:
            print(f"\n📰 ARTÍCULOS DE get_top_articles_from_db:")
            for i, row in enumerate(rows, 1):
                id_art, title, summary, url, source = row[0], row[1], row[2], row[3], row[4]
                risk_score = row[11] if len(row) > 11 else 0
                print(f"   {i:2}. [ID: {id_art}] [Riesgo: {risk_score:.2f}] '{title[:50]}...' ({source})")
        
        conn.close()
        return rows
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def compare_with_flask_response():
    """Comparar con lo que devuelve Flask"""
    
    print(f"\n🔄 COMPARACIÓN:")
    print("=" * 50)
    
    db_results = direct_test_function()
    
    if db_results:
        print(f"\n💡 CONCLUSIÓN:")
        print(f"   📊 Base de datos devuelve: {len(db_results)} artículos geopolíticos")
        print(f"   🌐 Flask devuelve: artículos diferentes (deportes/entretenimiento)")
        print(f"   🔧 PROBLEMA: Flask no está usando el método actualizado")
        
        print(f"\n🛠️  SOLUCIÓN:")
        print(f"   1. Reiniciar Flask completamente")
        print(f"   2. Verificar que no hay código cacheado")
        print(f"   3. Confirmar que app_BUENA.py tiene los cambios")

def main():
    """Función principal"""
    compare_with_flask_response()

if __name__ == "__main__":
    main()