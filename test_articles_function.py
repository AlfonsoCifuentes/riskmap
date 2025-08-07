import sqlite3
import json

def get_top_articles_from_db(limit=10, hero=False):
    """Función de prueba para obtener artículos de la BD"""
    try:
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # CONSULTA CORREGIDA: SOLO ARTÍCULOS GEOPOLÍTICOS (FILTROS RELAJADOS)
        base_filters = """
            WHERE (is_excluded IS NULL OR is_excluded != 1)
        """
        
        # Si es para el artículo hero (limit=1), usar lógica especial
        if limit == 1:
            # Artículo hero: PRIORIZAR ALTO RIESGO, más reciente, con imagen
            hero_query = f"""
                SELECT id, title, content, url, source, published_at, 
                       country, region, risk_level, conflict_type, 
                       sentiment_score, summary, risk_score, image_url
                FROM articles 
                {base_filters}
                AND (image_url IS NOT NULL AND image_url != '' 
                     AND image_url NOT LIKE '%placeholder%')
                ORDER BY 
                    CASE 
                        WHEN risk_level = 'high' THEN 1
                        WHEN risk_level = 'medium' THEN 2
                        WHEN risk_level = 'low' THEN 3
                        ELSE 4
                    END,
                    datetime(published_at) DESC,
                    id DESC
                LIMIT 1
            """
            
            cursor.execute(hero_query)
            hero_result = cursor.fetchone()
            
            # Si no hay artículos con imagen, buscar sin imagen pero PRIORIZANDO ALTO RIESGO
            if not hero_result:
                hero_query = f"""
                    SELECT id, title, content, url, source, published_at, 
                           country, region, risk_level, conflict_type, 
                           sentiment_score, summary, risk_score, image_url
                    FROM articles 
                    {base_filters}
                    ORDER BY 
                        CASE 
                            WHEN risk_level = 'high' THEN 1
                            WHEN risk_level = 'medium' THEN 2
                            WHEN risk_level = 'low' THEN 3
                            ELSE 4
                        END,
                        datetime(published_at) DESC,
                        id DESC
                    LIMIT 1
                """
                
                cursor.execute(hero_query)
                hero_result = cursor.fetchone()
            
            # Si aún no hay, buscar cualquier artículo PRIORIZANDO ALTO RIESGO
            if not hero_result:
                hero_query = f"""
                    SELECT id, title, content, url, source, published_at, 
                           country, region, risk_level, conflict_type, 
                           sentiment_score, summary, risk_score, image_url
                    FROM articles 
                    {base_filters}
                    ORDER BY 
                        CASE 
                            WHEN risk_level = 'high' THEN 1
                            WHEN risk_level = 'medium' THEN 2
                            WHEN risk_level = 'low' THEN 3
                            ELSE 4
                        END,
                        datetime(published_at) DESC,
                        id DESC
                    LIMIT 1
                """
                
                cursor.execute(hero_query)
                hero_result = cursor.fetchone()
            
            if hero_result:
                rows = [hero_result]
            else:
                # Fallback a cualquier artículo geopolítico
                query = f"""
                    SELECT id, title, content, url, source, published_at, 
                           country, region, risk_level, conflict_type, 
                           sentiment_score, summary, risk_score, image_url
                    FROM articles 
                    {base_filters}
                    ORDER BY 
                        CASE 
                            WHEN risk_score IS NOT NULL THEN risk_score 
                            WHEN risk_level = 'high' THEN 0.8
                            WHEN risk_level = 'medium' THEN 0.5
                            WHEN risk_level = 'low' THEN 0.2
                            ELSE 0.1
                        END DESC,
                        datetime(published_at) DESC
                    LIMIT 1
                """
                cursor.execute(query)
                rows = cursor.fetchall()
        else:
            # Consulta normal para múltiples artículos (PRIORIZA ALTO RIESGO)
            query = f"""
                SELECT id, title, content, url, source, published_at, 
                       country, region, risk_level, conflict_type, 
                       sentiment_score, summary, risk_score, image_url
                FROM articles 
                {base_filters}
                ORDER BY 
                    CASE 
                        WHEN risk_level = 'high' THEN 1
                        WHEN risk_level = 'medium' THEN 2
                        WHEN risk_level = 'low' THEN 3
                        ELSE 4
                    END,
                    CASE 
                        WHEN risk_score IS NOT NULL THEN risk_score 
                        ELSE 0.0
                    END DESC,
                    datetime(published_at) DESC,
                    id DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
        
        articles = []
        for row in rows:
            article = {
                'id': row[0],
                'title': row[1] or 'Sin título',
                'content': row[2] or 'Sin contenido',
                'url': row[3],
                'source': row[4] or 'Fuente desconocida',
                'published_at': row[5],
                'country': row[6] or 'Global',
                'region': row[7] or 'Internacional',
                'risk_level': row[8] or 'unknown',
                'conflict_type': row[9],
                'sentiment_score': row[10] or 0.0,
                'summary': row[11],
                'risk_score': row[12] or 0.0,
                'image_url': row[13],
                'location': row[6] or row[7] or 'Global'
            }
            articles.append(article)
        
        conn.close()
        
        print(f"✅ Obtenidos {len(articles)} artículos de la BD")
        return articles
        
    except Exception as e:
        print(f"❌ Error obteniendo artículos: {e}")
        return []

# Probar la función
print("🎯 Probando artículo HERO:")
hero_article = get_top_articles_from_db(limit=1, hero=True)
if hero_article:
    h = hero_article[0]
    print(f"ID: {h['id']}")
    print(f"Título: {h['title'][:80]}...")
    print(f"País: {h['country']}")
    print(f"Riesgo: {h['risk_level']}")
    print(f"¿Tiene imagen?: {'SÍ' if h['image_url'] else 'NO'}")
    if h['image_url']:
        print(f"URL imagen: {h['image_url'][:80]}...")
    print()

print("📰 Probando artículos del MOSAICO:")
mosaic_articles = get_top_articles_from_db(limit=6, hero=False)
print(f"Obtenidos {len(mosaic_articles)} artículos para el mosaico")
for i, article in enumerate(mosaic_articles[:3], 1):
    print(f"{i}. ID: {article['id']} - RIESGO: {article['risk_level']} - {article['title'][:60]}...")
    print(f"   Imagen: {'SÍ' if article['image_url'] else 'NO'}")
    print(f"   Fecha: {article['published_at']}")
    print()
