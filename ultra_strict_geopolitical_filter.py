#!/usr/bin/env python3
"""
ULTRA FILTRO GEOPOLÍTICO - VERSIÓN MEJORADA
===========================================

Filtro ultra-estricto para asegurar que SOLO aparezcan noticias
geopolíticas reales con imágenes originales, sin duplicación
entre hero y mosaico.

Autor: GitHub Copilot
Fecha: 2025
"""

import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_ultra_strict_filter():
    """Crear el filtro más estricto posible"""
    
    # Palabras clave OBLIGATORIAS para considerar un artículo geopolítico
    REQUIRED_GEOPOLITICAL_KEYWORDS = [
        # Guerra y conflicto
        'war', 'conflict', 'militar', 'military', 'guerra', 'conflicto', 'battle', 'combat',
        'invasion', 'invaded', 'invade', 'attack', 'attacked', 'bombing', 'bomb', 'missile',
        'drone', 'weapon', 'arms', 'defense', 'defence', 'security', 'nato', 'alliance',
        
        # Países y regiones de alta tensión geopolítica
        'ukraine', 'russia', 'putin', 'zelensky', 'crimea', 'donetsk', 'luhansk',
        'israel', 'palestine', 'gaza', 'hamas', 'hezbollah', 'lebanon', 'syria',
        'iran', 'tehran', 'sanctions', 'nuclear', 'ballistic',
        'china', 'taiwan', 'beijing', 'xi jinping', 'south china sea',
        'north korea', 'kim jong', 'pyongyang',
        
        # Términos geopolíticos específicos
        'sanctions', 'sanctions', 'embargo', 'treaty', 'diplomatic', 'embassy',
        'geopolitical', 'geopolitics', 'international', 'foreign policy',
        'trade war', 'tariff', 'export', 'import', 'border', 'territory',
        'coup', 'revolution', 'protest', 'uprising', 'referendum',
        
        # Organizaciones internacionales
        'united nations', 'european union', 'nato', 'g7', 'g20', 'security council',
        'international court', 'world bank', 'imf',
        
        # Términos en español
        'sanciones', 'tratado', 'diplomático', 'embajada', 'frontera',
        'revolución', 'protesta', 'referéndum', 'naciones unidas', 'unión europea'
    ]
    
    # Palabras clave PROHIBIDAS (definitivamente NO geopolíticas)
    FORBIDDEN_KEYWORDS = [
        # Entretenimiento
        'sport', 'sports', 'game', 'games', 'football', 'soccer', 'basketball', 'baseball',
        'tennis', 'golf', 'olympics', 'fifa', 'uefa', 'nba', 'nfl', 'mlb',
        'movie', 'film', 'actor', 'actress', 'hollywood', 'celebrity', 'singer', 'music',
        'album', 'song', 'concert', 'tour', 'netflix', 'disney', 'streaming',
        'emmy', 'oscar', 'grammy', 'award', 'prize',
        
        # Tecnología consumer
        'iphone', 'android', 'apple', 'google', 'facebook', 'instagram', 'tiktok',
        'nintendo', 'playstation', 'xbox', 'gaming', 'video game',
        'crypto', 'bitcoin', 'cryptocurrency', 'blockchain',
        
        # Otros no geopolíticos
        'weather', 'climate change', 'environment', 'health', 'medical', 'science',
        'business', 'economy', 'stock market', 'earnings', 'company',
        
        # En español
        'deporte', 'deportes', 'fútbol', 'música', 'película', 'cantante',
        'tiempo', 'clima', 'salud', 'médico', 'ciencia', 'empresa', 'bolsa'
    ]
    
    return REQUIRED_GEOPOLITICAL_KEYWORDS, FORBIDDEN_KEYWORDS

def test_ultra_strict_filter():
    """Probar el filtro con artículos de la base de datos"""
    print("🧪 PROBANDO ULTRA FILTRO GEOPOLÍTICO")
    print("=" * 60)
    
    required_keywords, forbidden_keywords = create_ultra_strict_filter()
    
    db_path = "data/geopolitical_intel.db"
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener muestra de artículos
        cursor.execute("""
            SELECT id, title, 
                   CASE WHEN original_image_url IS NOT NULL AND original_image_url != '' 
                        AND original_image_url LIKE 'https://%' 
                   THEN original_image_url
                   WHEN image_url IS NOT NULL AND image_url != '' 
                        AND image_url LIKE 'https://%' 
                        AND image_url NOT LIKE '%placeholder%'
                   THEN image_url 
                   ELSE NULL END as real_image,
                   geopolitical_relevance
            FROM unified_articles 
            ORDER BY created_at DESC 
            LIMIT 50
        """)
        
        articles = cursor.fetchall()
        conn.close()
        
        print(f"📊 Analizando {len(articles)} artículos recientes...")
        
        valid_articles = []
        rejected_articles = []
        
        for article_id, title, image_url, geo_relevance in articles:
            if not title:
                rejected_articles.append((title, "Sin título"))
                continue
                
            if not image_url:
                rejected_articles.append((title, "Sin imagen real"))
                continue
            
            title_lower = title.lower()
            
            # Verificar palabras prohibidas
            has_forbidden = any(keyword in title_lower for keyword in forbidden_keywords)
            if has_forbidden:
                rejected_articles.append((title, "Contiene palabras prohibidas"))
                continue
            
            # Verificar palabras requeridas
            has_required = any(keyword in title_lower for keyword in required_keywords)
            if not has_required:
                rejected_articles.append((title, "No contiene palabras geopolíticas"))
                continue
            
            # Si pasa todos los filtros
            valid_articles.append((article_id, title, image_url))
        
        print(f"\n✅ ARTÍCULOS VÁLIDOS: {len(valid_articles)}")
        for i, (art_id, title, img) in enumerate(valid_articles[:10], 1):
            print(f"   {i}. [{art_id}] {title[:60]}...")
        
        print(f"\n❌ ARTÍCULOS RECHAZADOS: {len(rejected_articles)}")
        rejection_reasons = {}
        for title, reason in rejected_articles:
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        
        for reason, count in rejection_reasons.items():
            print(f"   - {reason}: {count}")
        
        print(f"\n📈 ESTADÍSTICAS:")
        print(f"   - Total analizado: {len(articles)}")
        print(f"   - Válidos: {len(valid_articles)} ({len(valid_articles)/len(articles)*100:.1f}%)")
        print(f"   - Rechazados: {len(rejected_articles)} ({len(rejected_articles)/len(articles)*100:.1f}%)")
        
        return len(valid_articles) >= 5  # Al menos 5 artículos válidos
        
    except Exception as e:
        print(f"❌ Error probando filtro: {e}")
        return False

if __name__ == "__main__":
    test_ultra_strict_filter()