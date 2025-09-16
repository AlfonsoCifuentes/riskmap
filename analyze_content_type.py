#!/usr/bin/env python3
"""
Análisis de contenido para identificar artículos no geopolíticos
"""
import sqlite3
import os
from collections import Counter

def analyze_current_content():
    """Analizar el contenido actual para identificar patrones no geopolíticos"""
    
    print("🔍 ANÁLISIS DE CONTENIDO ACTUAL")
    print("=" * 50)
    
    db_path = r"data\geopolitical_intel.db"
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener artículos recientes con sus fuentes
        cursor.execute("""
            SELECT id, title, source, content, 
                   CASE WHEN content LIKE '%deporte%' OR content LIKE '%fútbol%' OR content LIKE '%soccer%' OR content LIKE '%baseball%' OR content LIKE '%basketball%' THEN 'DEPORTES'
                        WHEN content LIKE '%cine%' OR content LIKE '%película%' OR content LIKE '%Hollywood%' OR content LIKE '%actor%' OR content LIKE '%actress%' THEN 'ENTRETENIMIENTO'
                        WHEN content LIKE '%música%' OR content LIKE '%cantante%' OR content LIKE '%album%' OR content LIKE '%concierto%' THEN 'MÚSICA'
                        WHEN content LIKE '%celebridad%' OR content LIKE '%famoso%' THEN 'CELEBRIDADES'
                        ELSE 'OTROS'
                   END as categoria
            FROM articles 
            ORDER BY published_at DESC 
            LIMIT 50
        """)
        
        rows = cursor.fetchall()
        
        print(f"📊 Artículos analizados: {len(rows)}")
        
        # Contar por categorías
        categorias = Counter()
        fuentes = Counter()
        
        print(f"\n📝 ANÁLISIS POR CATEGORÍAS:")
        deportes_count = 0
        entretenimiento_count = 0
        otros_count = 0
        
        for row in rows:
            id_art, title, source, content, categoria = row
            categorias[categoria] += 1
            fuentes[source] += 1
            
            # Mostrar ejemplos de no geopolíticos
            if categoria in ['DEPORTES', 'ENTRETENIMIENTO', 'MÚSICA', 'CELEBRIDADES']:
                print(f"   ❌ {categoria}: '{title[:60]}...' - {source}")
                if categoria == 'DEPORTES':
                    deportes_count += 1
                elif categoria in ['ENTRETENIMIENTO', 'MÚSICA', 'CELEBRIDADES']:
                    entretenimiento_count += 1
            else:
                otros_count += 1
        
        print(f"\n📊 RESUMEN:")
        for cat, count in categorias.most_common():
            print(f"   {cat}: {count} artículos")
        
        # Detectar palabras clave problemáticas
        print(f"\n🔍 IDENTIFICANDO PATRONES NO GEOPOLÍTICOS:")
        
        cursor.execute("""
            SELECT title, source FROM articles
            WHERE title LIKE '%sport%' OR title LIKE '%game%' OR title LIKE '%match%' 
               OR title LIKE '%team%' OR title LIKE '%player%' OR title LIKE '%goal%'
               OR title LIKE '%movie%' OR title LIKE '%film%' OR title LIKE '%actor%'
               OR title LIKE '%singer%' OR title LIKE '%music%' OR title LIKE '%album%'
               OR title LIKE '%Emmy%' OR title LIKE '%Oscar%' OR title LIKE '%Grammy%'
            ORDER BY published_at DESC
            LIMIT 20
        """)
        
        non_geo_articles = cursor.fetchall()
        print(f"   🎯 Artículos detectados como no geopolíticos: {len(non_geo_articles)}")
        
        for title, source in non_geo_articles[:10]:
            print(f"      - '{title[:50]}...' ({source})")
        
        # Analizar fuentes
        print(f"\n📺 FUENTES MÁS FRECUENTES:")
        for fuente, count in fuentes.most_common(10):
            print(f"   {fuente}: {count} artículos")
        
        conn.close()
        
        return {
            'deportes': deportes_count,
            'entretenimiento': entretenimiento_count, 
            'geopoliticos': otros_count,
            'patrones_detectados': len(non_geo_articles)
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def suggest_filters():
    """Sugerir filtros para contenido geopolítico"""
    
    print(f"\n💡 FILTROS SUGERIDOS PARA CONTENIDO GEOPOLÍTICO:")
    print("=" * 60)
    
    print("✅ INCLUIR (palabras clave geopolíticas):")
    geo_keywords = [
        'guerra', 'conflict', 'diplomacia', 'sanción', 'militar',
        'gobierno', 'política', 'elecciones', 'crisis', 'seguridad',
        'internacional', 'tratado', 'territorio', 'frontera',
        'terrorismo', 'refugiado', 'inmigración', 'comercio',
        'economía', 'inflación', 'riesgo', 'tensión'
    ]
    
    for i, keyword in enumerate(geo_keywords):
        print(f"   {i+1:2}. {keyword}")
    
    print(f"\n❌ EXCLUIR (palabras clave no geopolíticas):")
    non_geo_keywords = [
        'sport', 'game', 'match', 'team', 'player', 'goal', 'football',
        'movie', 'film', 'actor', 'actress', 'Hollywood', 'cinema',
        'singer', 'music', 'album', 'concert', 'Grammy', 'Emmy', 'Oscar',
        'celebrity', 'fashion', 'entertainment', 'TV show', 'series'
    ]
    
    for i, keyword in enumerate(non_geo_keywords):
        print(f"   {i+1:2}. {keyword}")

def main():
    """Función principal"""
    stats = analyze_current_content()
    
    if stats:
        suggest_filters()
        
        print(f"\n📋 RECOMENDACIONES:")
        print(f"   🎯 Artículos no geopolíticos detectados: {stats['patrones_detectados']}")
        print(f"   🔧 Implementar filtro SQL con palabras clave")
        print(f"   ⚡ Mejorar precisión del contenido mostrado")

if __name__ == "__main__":
    main()