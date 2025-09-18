#!/usr/bin/env python3
"""
Test EXACT get_top_articles_from_db method used by API
"""
import sqlite3
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MockAPICall:
    """Mock the exact API call logic"""
    
    def get_top_articles_from_db(self, limit=20, exclude_hero_id=None):
        """EXACT COPY from app_BUENA.py"""
        try:
            import sqlite3
            
            # Obtener ruta de la base de datos usando la función correcta
            try:
                from src.utils.config import get_database_path
                db_path = get_database_path()
            except ImportError:
                db_path = r"data\geopolitical_intel.db"
            
            if not os.path.exists(db_path):
                logger.warning(f"Base de datos no encontrada en: {db_path}")
                return self._get_real_articles_from_db(limit)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # FILTRO INTELIGENTE: Confiar en la clasificación del sistema de ingesta
            base_query = """
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
                    -- Solo artículos marcados como geopolíticos por el sistema inteligente
                    geopolitical_relevance = 1 AND
                    
                    -- Campos básicos requeridos 
                    title IS NOT NULL AND title != '' AND
                    (
                        (content IS NOT NULL AND content != '') OR 
                        (summary IS NOT NULL AND summary != '')
                    ) AND
                    
                    -- Solo artículos con imagen real (no placeholder)
                    (
                        (original_image_url IS NOT NULL AND original_image_url != '') OR
                        (image_url IS NOT NULL AND image_url != '' AND 
                         image_url NOT LIKE '%placeholder%' AND 
                         image_url NOT LIKE '%via.placeholder%' AND
                         image_url NOT LIKE '%default%')
                    ) AND
                    
                    -- Exclusiones mínimas para casos extremos
                    (
                        LOWER(title) NOT LIKE '%sport%' AND LOWER(title) NOT LIKE '%sports%' AND
                        LOWER(title) NOT LIKE '%game%' AND LOWER(title) NOT LIKE '%games%' AND
                        LOWER(title) NOT LIKE '%football%' AND LOWER(title) NOT LIKE '%soccer%' AND
                        LOWER(title) NOT LIKE '%basketball%' AND LOWER(title) NOT LIKE '%baseball%' AND
                        LOWER(title) NOT LIKE '%emmy%' AND LOWER(title) NOT LIKE '%oscar%' AND
                        LOWER(title) NOT LIKE '%movie%' AND LOWER(title) NOT LIKE '%actor%' AND
                        LOWER(title) NOT LIKE '%hollywood%' AND LOWER(title) NOT LIKE '%singer%' AND
                        LOWER(title) NOT LIKE '%music%' AND LOWER(title) NOT LIKE '%celebrity%' AND
                        LOWER(title) NOT LIKE '%netflix%' AND
                        LOWER(title) NOT LIKE '%iphone%' AND LOWER(title) NOT LIKE '%nintendo%' AND
                        LOWER(title) NOT LIKE '%deporte%' AND LOWER(title) NOT LIKE '%deportes%' AND
                        LOWER(title) NOT LIKE '%fútbol%' AND LOWER(title) NOT LIKE '%música%'
                    ) AND
                    source NOT LIKE '%Yahoo Entertainment%' AND
                    
                    -- Excluir HERO si se especifica
                    {exclude_clause} AND
                    
                    -- Solo artículos recientes (últimos 30 días para más cobertura)
                    created_at >= datetime('now', '-30 days')
                ORDER BY 
                    -- Prioridad: importancia AI > riesgo > fecha
                    COALESCE(ai_importance, 0) DESC,
                    COALESCE(risk_score, 0) DESC,
                    created_at DESC
                LIMIT ?
            """
            
            exclude_clause = "id != ?" if exclude_hero_id else "1=1"
            query = base_query.format(exclude_clause=exclude_clause)
            
            if exclude_hero_id:
                cursor.execute(query, (exclude_hero_id, limit))
            else:
                cursor.execute(query, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convertir a formato diccionario
            articles = []
            for row in rows:
                article = {
                    'id': row[0],
                    'title': row[1] or 'Sin título',
                    'summary': row[2] or 'Sin resumen disponible',
                    'url': row[3] or '',
                    'source': row[4] or 'Fuente desconocida',
                    'published_at': row[5],
                    'country': row[6] or 'Global',
                    'region': row[7] or 'Internacional',
                    'risk_level': row[8] or 'medium',
                    'conflict_type': row[9] or '',
                    'sentiment_score': row[10] or 0.0,
                    'risk_score': row[11] or 0.0,
                    'image_url': row[12],  # Solo imagen real o None
                    'ai_importance': row[13] or 0.0,
                    'location': row[6] or 'Global'
                }
                articles.append(article)
            
            logger.info(f"✅ Filtro geopolítico ESTRICTO aplicado: {len(articles)} artículos válidos de BD")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error al obtener artículos de BD: {e}")
            # Fallback a método alternativo
            return self._get_real_articles_from_db(limit)
    
    def _get_real_articles_from_db(self, limit=20):
        """Fallback method"""
        return []  # We'll implement if needed

def test_api_method():
    print("🔍 TESTING EXACT API METHOD get_top_articles_from_db")
    print("="*60)
    
    mock_api = MockAPICall()
    
    # Test 1: Get hero article first (mimicking API logic)
    print("Step 1: Getting hero article...")
    hero_articles = mock_api.get_top_articles_from_db(1)
    hero_id = hero_articles[0]['id'] if hero_articles else None
    print(f"Hero ID: {hero_id}")
    if hero_articles:
        print(f"Hero article: {hero_articles[0]['title']}")
        print(f"Hero image: {hero_articles[0]['image_url']}")
    
    # Test 2: Get regular articles excluding hero
    print(f"\nStep 2: Getting regular articles (excluding hero {hero_id})...")
    articles = mock_api.get_top_articles_from_db(20, exclude_hero_id=hero_id)
    
    print(f"Articles returned: {len(articles)}")
    
    if articles:
        print("\n📋 Sample results:")
        for i, article in enumerate(articles[:5]):
            has_image = bool(article.get('image_url'))
            image_text = article.get('image_url', 'NULL')[:60] if has_image else 'NULL'
            print(f"   {i+1}. ID {article['id']}: {article['title'][:50]}...")
            print(f"      Image: {image_text}{'...' if len(str(article.get('image_url', ''))) > 60 else ''}")

if __name__ == "__main__":
    test_api_method()