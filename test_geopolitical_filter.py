#!/usr/bin/env python3
"""
Test del filtro geopolítico - Verificar que solo se muestran noticias relevantes
"""
import sqlite3
import os

def test_geopolitical_filter():
    """Test el nuevo filtro geopolítico"""
    
    print("🧪 TEST: Filtro Geopolítico")
    print("=" * 50)
    
    db_path = r"data\geopolitical_intel.db"
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # La nueva query con filtros geopolíticos
        base_query = """
            SELECT id, title, source, risk_score
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
            ORDER BY risk_score DESC, published_at DESC
            LIMIT 20
        """
        
        cursor.execute(base_query)
        filtered_articles = cursor.fetchall()
        
        print(f"✅ Artículos que pasaron el filtro geopolítico: {len(filtered_articles)}")
        
        if filtered_articles:
            print(f"\n📰 ARTÍCULOS GEOPOLÍTICOS SELECCIONADOS:")
            for i, (id_art, title, source, risk_score) in enumerate(filtered_articles, 1):
                print(f"   {i:2}. [Riesgo: {risk_score:.2f}] '{title[:60]}...' ({source})")
        
        # Comparar con artículos sin filtro
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE title IS NOT NULL AND title != '' AND content IS NOT NULL AND content != ''
        """)
        total_articles = cursor.fetchone()[0]
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   📈 Total artículos en BD: {total_articles}")
        print(f"   ✅ Artículos geopolíticos: {len(filtered_articles)}")
        print(f"   🔴 Artículos filtrados: {total_articles - len(filtered_articles)}")
        print(f"   📊 Porcentaje geopolítico: {(len(filtered_articles)/total_articles*100):.1f}%")
        
        # Verificar que se excluyeron deportes y entretenimiento
        cursor.execute("""
            SELECT title, source FROM articles
            WHERE (title LIKE '%sport%' OR title LIKE '%game%' OR title LIKE '%match%' 
               OR title LIKE '%team%' OR title LIKE '%player%' OR title LIKE '%Emmy%'
               OR title LIKE '%actor%' OR title LIKE '%movie%' OR source LIKE '%Sports%')
            AND title IS NOT NULL AND content IS NOT NULL
            LIMIT 10
        """)
        
        excluded_articles = cursor.fetchall()
        print(f"\n❌ ARTÍCULOS EXCLUIDOS (deportes/entretenimiento): {len(excluded_articles)}")
        for title, source in excluded_articles[:5]:
            print(f"   - '{title[:50]}...' ({source})")
        
        conn.close()
        
        return {
            'geopolitical_count': len(filtered_articles),
            'total_count': total_articles,
            'excluded_count': len(excluded_articles)
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Función principal"""
    result = test_geopolitical_filter()
    
    if result:
        print(f"\n🎯 RESULTADO DEL FILTRO:")
        if result['geopolitical_count'] > 0:
            print(f"✅ FILTRO FUNCIONANDO")
            print(f"🌐 Se mostrarán solo {result['geopolitical_count']} noticias geopolíticas")
            print(f"🚫 Se excluyeron {result['excluded_count']} noticias de deportes/entretenimiento")
        else:
            print(f"⚠️  No se encontraron artículos que pasen el filtro")
            print(f"💡 Verificar criterios de filtrado")

if __name__ == "__main__":
    main()