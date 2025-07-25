#!/usr/bin/env python3
"""
Check if NLP processing is working correctly
"""
import sqlite3

def check_nlp_processing():
    # Connect to database
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    print("=== ANÁLISIS DEL PROCESAMIENTO NLP ===\n")
    
    # Check if articles have been processed
    cursor.execute("""
        SELECT 
            COUNT(*) as total_articles,
            COUNT(CASE WHEN risk_level IS NOT NULL THEN 1 END) as with_risk_level,
            COUNT(CASE WHEN risk_level = 'high' THEN 1 END) as high_risk,
            COUNT(CASE WHEN risk_level = 'medium' THEN 1 END) as medium_risk,
            COUNT(CASE WHEN risk_level = 'low' THEN 1 END) as low_risk
        FROM articles 
        WHERE created_at > datetime('now', '-24 hours')
    """)
    
    stats = cursor.fetchone()
    total, with_risk, high, medium, low = stats
    
    print("📊 ESTADÍSTICAS DE PROCESAMIENTO (últimas 24h):")
    print("-" * 50)
    print(f"Total artículos: {total}")
    print(f"Con nivel de riesgo: {with_risk}")
    print(f"Alto riesgo: {high}")
    print(f"Riesgo medio: {medium}")
    print(f"Bajo riesgo: {low}")
    print(f"Sin procesar: {total - with_risk}")
    
    # Check processed_data table
    cursor.execute("""
        SELECT 
            COUNT(*) as total_processed,
            COUNT(CASE WHEN pd.sentiment IS NOT NULL THEN 1 END) as with_sentiment,
            COUNT(CASE WHEN pd.keywords IS NOT NULL AND pd.keywords != '[]' THEN 1 END) as with_keywords,
            COUNT(CASE WHEN pd.category IS NOT NULL THEN 1 END) as with_category,
            COUNT(CASE WHEN pd.summary IS NOT NULL THEN 1 END) as with_summary
        FROM processed_data pd
        JOIN articles a ON pd.article_id = a.id
        WHERE a.created_at > datetime('now', '-24 hours')
    """)
    
    processed_stats = cursor.fetchone()
    if processed_stats:
        total_proc, with_sent, with_keys, with_cat, with_summ = processed_stats
        print(f"\n🔬 DATOS PROCESADOS NLP (últimas 24h):")
        print("-" * 50)
        print(f"Total procesados: {total_proc}")
        print(f"Con sentiment: {with_sent}")
        print(f"Con keywords: {with_keys}")
        print(f"Con categoría: {with_cat}")
        print(f"Con resumen: {with_summ}")
    
    # Check some recent RSS articles to see their content
    cursor.execute("""
        SELECT 
            a.id,
            a.title,
            a.content,
            a.risk_level,
            a.source,
            a.created_at,
            pd.sentiment,
            pd.keywords,
            pd.category
        FROM articles a
        LEFT JOIN processed_data pd ON a.id = pd.article_id
        WHERE a.source = 'RSS Feed'
        AND a.created_at > datetime('now', '-24 hours')
        ORDER BY a.created_at DESC
        LIMIT 10
    """)
    
    print(f"\n📰 MUESTRA DE ARTÍCULOS RSS RECIENTES:")
    print("=" * 80)
    
    for i, row in enumerate(cursor.fetchall(), 1):
        article_id, title, content, risk_level, source, created_at, sentiment, keywords, category = row
        
        print(f"\n{i}. ID: {article_id}")
        print(f"   Título: {title[:70]}...")
        print(f"   Contenido: {(content or 'SIN CONTENIDO')[:100]}...")
        print(f"   Risk Level: {risk_level or 'SIN PROCESAR'}")
        print(f"   Sentiment: {sentiment or 'SIN PROCESAR'}")
        print(f"   Keywords: {keywords or 'SIN PROCESAR'}")
        print(f"   Category: {category or 'SIN PROCESAR'}")
        print(f"   Fecha: {created_at}")
        
        # Check if this looks like it should be high risk
        title_lower = (title or '').lower()
        content_lower = (content or '').lower()
        
        high_risk_keywords = ['war', 'conflict', 'military', 'sanctions', 'nuclear', 'terrorism', 'coup', 'invasion', 'ceasefire', 'hamas', 'ukraine', 'russia', 'china', 'iran', 'israel', 'gaza', 'syria', 'attack', 'bomb', 'missile', 'threat']
        
        found_keywords = [kw for kw in high_risk_keywords if kw in title_lower or kw in content_lower]
        
        if found_keywords:
            print(f"   🚨 PALABRAS DE ALTO RIESGO DETECTADAS: {', '.join(found_keywords)}")
            if risk_level == 'low':
                print(f"   ⚠️  PROBLEMA: Debería ser alto riesgo pero está marcado como bajo!")
        
        print("-" * 80)
    
    # Check if there are articles without processing
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles a
        LEFT JOIN processed_data pd ON a.id = pd.article_id
        WHERE a.created_at > datetime('now', '-24 hours')
        AND pd.article_id IS NULL
    """)
    
    unprocessed = cursor.fetchone()[0]
    print(f"\n❌ ARTÍCULOS SIN PROCESAR (últimas 24h): {unprocessed}")
    
    if unprocessed > 0:
        print("\n🔍 MUESTRA DE ARTÍCULOS SIN PROCESAR:")
        cursor.execute("""
            SELECT a.id, a.title, a.content, a.created_at
            FROM articles a
            LEFT JOIN processed_data pd ON a.id = pd.article_id
            WHERE a.created_at > datetime('now', '-24 hours')
            AND pd.article_id IS NULL
            ORDER BY a.created_at DESC
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            article_id, title, content, created_at = row
            print(f"ID {article_id}: {title[:50]}... ({created_at})")
    
    conn.close()

if __name__ == "__main__":
    check_nlp_processing()