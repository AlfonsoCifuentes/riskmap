#!/usr/bin/env python3
"""
Crear filtro SQL mejorado y más estricto para solo mostrar noticias geopolíticas con imágenes reales
"""

def generate_improved_geopolitical_filter():
    """Generar un filtro SQL más estricto para contenido geopolítico"""
    
    # Filtro más estricto que funciona sobre title + content
    improved_filter = """
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
            WHEN original_image_url IS NOT NULL AND original_image_url != '' 
            THEN '/static/images/news/' || SUBSTR(original_image_url, INSTR(original_image_url, 'news_') + 5)
            WHEN image_url IS NOT NULL AND image_url != '' AND image_url NOT LIKE '%via.placeholder%' THEN 
                image_url
            ELSE 
                'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=200&fit=crop'
        END as image_url,
        ai_importance
    FROM articles 
    WHERE 
        -- Solo artículos con imagen real (no placeholder)
        original_image_url IS NOT NULL AND original_image_url != '' AND
        
        -- Campos básicos requeridos
        title IS NOT NULL AND title != '' AND
        content IS NOT NULL AND content != '' AND
        
        -- FILTRO ESTRICTO: Solo contenido claramente geopolítico
        (
            -- Keywords geopolíticas en título o contenido
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%war%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%conflict%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%military%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%politics%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%government%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%security%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%diplomacy%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%election%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%terrorism%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%sanction%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%treaty%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%refugee%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%border%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%territory%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%international%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%crisis%' OR
            
            -- Organizaciones internacionales
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%nato%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%united nations%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%european union%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%g7%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%g20%' OR
            
            -- Países de alta relevancia geopolítica
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%russia%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%ukraine%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%china%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%taiwan%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%north korea%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%iran%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%israel%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%palestine%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%gaza%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%syria%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%afghanistan%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%yemen%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%iraq%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%venezuela%' OR
            
            -- Términos en español
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%guerra%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%militar%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%política%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%gobierno%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%seguridad%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%diplomacia%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%elecciones%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%terrorismo%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%refugiado%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%frontera%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%territorio%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%internacional%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%otan%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%rusia%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%ucrania%' OR
            LOWER(title || ' ' || COALESCE(content, '')) LIKE '%irán%'
        ) AND (
            -- EXCLUSIONES ESTRICTAS: Todo lo que NO es geopolítico
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%sport%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%sports%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%game%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%games%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%match%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%team%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%teams%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%player%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%players%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%goal%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%goals%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%football%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%soccer%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%baseball%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%basketball%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tennis%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%golf%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%hockey%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%boxing%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%wrestling%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%nfl%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%nba%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%mlb%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%nhl%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%fifa%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%olympics%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%championship%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tournament%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%league%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%season%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%playoff%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%fantasy%' AND
            
            -- Entretenimiento
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%emmy%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%emmys%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%oscar%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%oscars%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%grammy%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%grammys%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%movie%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%movies%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%film%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%films%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%actor%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%actress%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%hollywood%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%cinema%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%singer%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%music%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%album%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%song%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%concert%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%celebrity%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%celebrities%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%fashion%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tv show%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%television%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%netflix%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%disney%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%anime%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%gaming%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%video game%' AND
            
            -- Tecnología consumer
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%iphone%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%apple%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%android%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%google%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%meta%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%facebook%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%instagram%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%twitter%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tiktok%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%spotify%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%netflix%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tesla%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%microsoft%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%amazon%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%startup%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%gadget%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%smartphone%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tablet%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%laptop%' AND
            
            -- Salud/lifestyle/personal
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%diet%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%fitness%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%weight loss%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%exercise%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%recipe%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%cooking%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%travel%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tourism%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%vacation%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%wedding%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%dating%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%relationship%' AND
            
            -- Términos en español
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%deporte%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%deportes%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%fútbol%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%música%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%película%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%cine%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%cantante%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%famoso%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%celebridad%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%moda%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%cocina%' AND
            LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%viajes%'
        ) AND (
            -- Excluir fuentes claramente no geopolíticas
            source NOT LIKE '%Sports%' AND 
            source NOT LIKE '%ESPN%' AND 
            source NOT LIKE '%Entertainment%' AND 
            source NOT LIKE '%TMZ%' AND 
            source NOT LIKE '%People%' AND
            source NOT LIKE '%AppleInsider%' AND 
            source NOT LIKE '%9to5Mac%' AND 
            source NOT LIKE '%TechCrunch%' AND
            source NOT LIKE '%Variety%' AND
            source NOT LIKE '%Hollywood Reporter%' AND
            source NOT LIKE '%Rolling Stone%' AND
            source NOT LIKE '%Billboard%' AND
            source NOT LIKE '%Sporting News%' AND
            source NOT LIKE '%Sports Illustrated%' AND
            source NOT LIKE '%CBS Sports%' AND
            source NOT LIKE '%NBC Sports%' AND
            source NOT LIKE '%Fox Sports%' AND
            source NOT LIKE '%The Verge%' AND
            source NOT LIKE '%Engadget%' AND
            source NOT LIKE '%Gizmodo%' AND
            source NOT LIKE '%Wired%'
        )
    ORDER BY 
        risk_score DESC,
        ai_importance DESC,
        published_at DESC
    LIMIT ?
    """
    
    return improved_filter

def test_improved_filter():
    """Test del filtro mejorado"""
    
    import sqlite3
    
    db_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
    
    print("🧪 TESTANDO FILTRO MEJORADO")
    print("=" * 50)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            filter_sql = generate_improved_geopolitical_filter()
            cursor.execute(filter_sql, (20,))
            results = cursor.fetchall()
            
            print(f"✅ Artículos encontrados: {len(results)}")
            
            if results:
                print("\n📰 ARTÍCULOS QUE PASAN EL NUEVO FILTRO:")
                for i, row in enumerate(results, 1):
                    article_id, title, summary, url, source, published_at, country, region, risk_level, conflict_type, sentiment_score, risk_score, image_url, ai_importance = row
                    title_short = title[:60] + "..." if len(title) > 60 else title
                    has_real_image = '/static/images/news/' in image_url
                    image_status = "📸" if has_real_image else "❌"
                    print(f"      {i}. {image_status} [Risk:{risk_score:.2f}] [{source}] {title_short}")
            else:
                print("⚠️  NO HAY ARTÍCULOS que pasen el nuevo filtro!")
                
        return len(results)
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return 0

if __name__ == "__main__":
    count = test_improved_filter()
    print(f"\n📊 RESULTADO: {count} artículos geopolíticos con imagen real")