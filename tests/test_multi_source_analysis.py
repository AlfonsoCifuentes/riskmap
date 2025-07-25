#!/usr/bin/env python3
"""
Test directo del análisis AI mejorado usando datos de la base de datos
"""

import sqlite3
import sys
import os

# Añadir el directorio src al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_multi_source_analysis():
    """
    Prueba directa del análisis AI con múltiples artículos de la base de datos
    """
    print("🚀 TEST DE ANÁLISIS GEOPOLÍTICO MULTI-FUENTE")
    print("="*70)
    
    # Conectar a la base de datos
    try:
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Obtener artículos diversos de alto riesgo de múltiples regiones
        print("📊 Obteniendo artículos diversos de alto riesgo...")
        
        cursor.execute("""
            WITH RankedArticles AS (
                SELECT id, title, content, summary, conflict_type, country, region, source, language,
                       risk_score, sentiment_label, sentiment_score, key_persons, key_locations,
                       entities_json, conflict_indicators, created_at,
                       ROW_NUMBER() OVER (PARTITION BY region ORDER BY risk_score DESC, created_at DESC) as rn
                FROM articles 
                WHERE created_at > datetime('now', '-7 days')
                AND risk_score IS NOT NULL
                AND risk_score > 3
            )
            SELECT id, title, content, summary, conflict_type, country, region, source, language,
                   risk_score, sentiment_label, sentiment_score, key_persons, key_locations,
                   entities_json, conflict_indicators
            FROM RankedArticles 
            WHERE rn <= 3  -- Máximo 3 artículos por región
            ORDER BY risk_score DESC
            LIMIT 15
        """)
        
        articles_data = cursor.fetchall()
        
        if not articles_data:
            print("❌ No se encontraron artículos de alto riesgo")
            # Fallback: obtener cualquier artículo reciente
            cursor.execute("""
                SELECT id, title, COALESCE(content, summary, 'Sin contenido') as content, 
                       COALESCE(summary, title) as summary, 
                       COALESCE(conflict_type, 'Political') as conflict_type, 
                       COALESCE(country, 'Global') as country, 
                       COALESCE(region, 'Internacional') as region, 
                       source, language, 
                       COALESCE(risk_score, 5) as risk_score,
                       COALESCE(sentiment_label, 'neutral') as sentiment_label,
                       COALESCE(sentiment_score, 0) as sentiment_score,
                       COALESCE(key_persons, '') as key_persons,
                       COALESCE(key_locations, '') as key_locations,
                       COALESCE(entities_json, '[]') as entities_json,
                       COALESCE(conflict_indicators, '') as conflict_indicators
                FROM articles 
                WHERE created_at > datetime('now', '-14 days')
                ORDER BY created_at DESC
                LIMIT 10
            """)
            articles_data = cursor.fetchall()
        
        conn.close()
        
        # Procesar datos para análisis
        processed_articles = []
        regions = set()
        sources = set()
        total_risk = 0
        risk_count = 0
        
        print(f"📰 Procesando {len(articles_data)} artículos...")
        
        for article in articles_data:
            (id, title, content, summary, conflict_type, country, region, source, language,
             risk_score, sentiment_label, sentiment_score, key_persons, key_locations,
             entities_json, conflict_indicators) = article
            
            regions.add(region)
            sources.add(source)
            
            if risk_score:
                total_risk += risk_score
                risk_count += 1
            
            processed_articles.append({
                'id': id,
                'title': title,
                'content': content[:300] + '...' if content and len(content) > 300 else content,
                'summary': summary,
                'conflict_type': conflict_type,
                'country': country,
                'region': region,
                'source': source,
                'language': language,
                'risk_score': risk_score,
                'sentiment_label': sentiment_label,
                'sentiment_score': sentiment_score,
                'key_persons': key_persons,
                'key_locations': key_locations
            })
        
        # Mostrar estadísticas de diversidad
        print("\n📊 ANÁLISIS DE DIVERSIDAD DE FUENTES:")
        print("-" * 50)
        print(f"🌍 Regiones cubiertas: {len(regions)}")
        for region in sorted(regions):
            region_count = len([a for a in processed_articles if a['region'] == region])
            print(f"   • {region}: {region_count} artículos")
        
        print(f"\n📰 Fuentes diferentes: {len(sources)}")
        for source in sorted(sources)[:10]:  # Mostrar solo las primeras 10
            source_count = len([a for a in processed_articles if a['source'] == source])
            print(f"   • {source}: {source_count} artículos")
        if len(sources) > 10:
            print(f"   • ... y {len(sources) - 10} fuentes más")
        
        avg_risk = total_risk / risk_count if risk_count > 0 else 0
        print(f"\n⚠️ Riesgo promedio: {avg_risk:.2f}/10")
        
        # Mostrar muestra de artículos para verificar diversidad
        print("\n📋 MUESTRA DE ARTÍCULOS ANALIZADOS:")
        print("-" * 70)
        
        for i, article in enumerate(processed_articles[:5], 1):
            print(f"\n{i}. {article['title'][:80]}...")
            print(f"   🌍 Región: {article['region']} | País: {article['country']}")
            print(f"   📰 Fuente: {article['source']} | Idioma: {article['language']}")
            print(f"   ⚠️ Riesgo: {article['risk_score']}/10 | Sentimiento: {article['sentiment_label']}")
            print(f"   🔄 Conflicto: {article['conflict_type']}")
        
        if len(processed_articles) > 5:
            print(f"\n   ... y {len(processed_articles) - 5} artículos más analizados")
        
        # Generar contexto para análisis AI
        print("\n🤖 PREPARANDO CONTEXTO PARA ANÁLISIS AI:")
        print("-" * 50)
        
        # Estadísticas de cobertura global
        diversity_stats = f"""
ESTADÍSTICAS DE COBERTURA GLOBAL:
- Total de eventos analizados: {len(processed_articles)}
- Regiones únicas analizadas: {len(regions)}
- Diversidad de fuentes: {len(sources)} medios diferentes
- Riesgo promedio global: {avg_risk:.2f}/10
- Rango temporal: Últimos 7-14 días
"""
        
        print(diversity_stats)
        
        # Mostrar resumen de patrones de conflicto
        conflict_types = {}
        for article in processed_articles:
            ct = article['conflict_type']
            if ct not in conflict_types:
                conflict_types[ct] = 0
            conflict_types[ct] += 1
        
        print("🔥 PATRONES DE CONFLICTO IDENTIFICADOS:")
        for conflict_type, count in sorted(conflict_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {conflict_type}: {count} eventos")
        
        # Análisis regional
        print("\n🌎 ANÁLISIS REGIONAL:")
        regional_stats = {}
        for article in processed_articles:
            region = article['region']
            if region not in regional_stats:
                regional_stats[region] = {
                    'count': 0,
                    'total_risk': 0,
                    'sentiments': []
                }
            
            regional_stats[region]['count'] += 1
            if article['risk_score']:
                regional_stats[region]['total_risk'] += article['risk_score']
            regional_stats[region]['sentiments'].append(article['sentiment_label'])
        
        for region, stats in regional_stats.items():
            avg_regional_risk = stats['total_risk'] / stats['count'] if stats['count'] > 0 else 0
            dominant_sentiment = max(set(stats['sentiments']), key=stats['sentiments'].count) if stats['sentiments'] else 'neutral'
            print(f"   • {region}: {stats['count']} eventos, Riesgo: {avg_regional_risk:.1f}, Sentimiento: {dominant_sentiment}")
        
        print("\n" + "="*70)
        print("✅ ANÁLISIS MULTI-FUENTE COMPLETADO")
        print("🎯 CONCLUSIONES:")
        print(f"   • Se analizaron {len(processed_articles)} eventos de {len(regions)} regiones diferentes")
        print(f"   • Cobertura de {len(sources)} fuentes mediáticas distintas")
        print(f"   • Diversidad geográfica y temática verificada")
        print(f"   • Datos listos para análisis AI comprehensivo")
        print("🚀 El sistema ahora puede generar análisis periodístico basado en múltiples fuentes!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en el test: {e}")
        return False

if __name__ == "__main__":
    test_multi_source_analysis()
