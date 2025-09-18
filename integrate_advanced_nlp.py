#!/usr/bin/env python3
"""
Script para integrar el analizador NLP avanzado con BERT/RoBERTa en el sistema principal
"""

import sqlite3
import sys
from pathlib import Path
import json
import logging

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

from nlp_processing.advanced_analyzer import AdvancedNLPAnalyzer
from src.utils.bert_risk_analyzer import BERTRiskAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_advanced_nlp():
    """Integra el análisis NLP avanzado en artículos existentes."""
    
    # Connect to database
    db_path = 'data/geopolitical_intel.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Initialize analyzers
    logger.info("🧠 Inicializando analizadores NLP avanzados...")
    nlp_analyzer = AdvancedNLPAnalyzer()
    bert_analyzer = BERTRiskAnalyzer()
    
    print("🔍 Buscando artículos para análisis NLP avanzado...")
    
    # Get articles that need advanced NLP processing
    cursor.execute('''
        SELECT a.id, a.title, a.content, a.country, a.risk_level, pd.category
        FROM articles a 
        LEFT JOIN processed_data pd ON a.id = pd.article_id 
        WHERE a.created_at > datetime('now', '-7 days')
        AND (pd.category IS NULL OR pd.category != 'sports_entertainment')
        ORDER BY a.created_at DESC
        LIMIT 20
    ''')
    
    articles = cursor.fetchall()
    print(f"📰 Encontrados {len(articles)} artículos para procesar")
    
    processed_count = 0
    
    for article in articles:
        article_id, title, content, country, risk_level, category = article
        
        print(f"\n🔬 Procesando artículo ID {article_id}:")
        print(f"   Título: {title[:60]}...")
        
        try:
            # Prepare article data for comprehensive analysis
            article_data = {
                'title': title or '',
                'content': content or '',
                'description': ''  # Could be extracted from content
            }
            
            # Perform comprehensive NLP analysis
            nlp_results = nlp_analyzer.analyze_article_comprehensive(article_data)
            
            # Perform BERT risk analysis
            bert_results = bert_analyzer.analyze_risk(
                title=title or '',
                content=content or '',
                country=country
            )
            
            # Combine results
            combined_analysis = {
                'nlp_entities': nlp_results['entities'],
                'sentiment_analysis': nlp_results['sentiment'],
                'title_sentiment': nlp_results['title_sentiment'],
                'nlp_risk_score': nlp_results['risk_score'],
                'bert_risk_level': bert_results['level'],
                'bert_risk_score': bert_results['score'],
                'bert_confidence': bert_results['confidence'],
                'bert_reasoning': bert_results['reasoning'],
                'key_factors': bert_results.get('key_factors', []),
                'geographic_impact': bert_results.get('geographic_impact', 'Unknown'),
                'escalation_potential': bert_results.get('potential_escalation', 'Unknown'),
                'key_persons': nlp_results['key_persons'],
                'key_locations': nlp_results['key_locations'],
                'conflict_indicators': nlp_results['conflict_indicators'],
                'total_entities': nlp_results['total_entities'],
                'ai_powered': bert_results['ai_powered'],
                'model_used': bert_results['model_used']
            }
            
            # Update or insert processed data
            cursor.execute('''
                SELECT id FROM processed_data WHERE article_id = ?
            ''', (article_id,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record with advanced NLP data
                cursor.execute('''
                    UPDATE processed_data 
                    SET 
                        summary = ?,
                        category = ?,
                        keywords = ?,
                        sentiment = ?,
                        entities = ?,
                        advanced_nlp = ?
                    WHERE article_id = ?
                ''', (
                    (content[:300] + '...' if len(content or '') > 300 else content) or '',
                    category or 'geopolitical_analysis',
                    json.dumps((nlp_results.get('key_persons', []) or []) + (nlp_results.get('key_locations', []) or [])),
                    nlp_results.get('sentiment', {}).get('score') if nlp_results.get('sentiment') else 0.0,
                    json.dumps(nlp_results.get('entities', []) or []),
                    json.dumps(combined_analysis),
                    article_id
                ))
            else:
                # Insert new processed data record
                cursor.execute('''
                    INSERT INTO processed_data (
                        article_id, summary, category, keywords, sentiment, entities, advanced_nlp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_id,
                    (content[:300] + '...' if len(content or '') > 300 else content) or '',
                    category or 'geopolitical_analysis',
                    json.dumps((nlp_results.get('key_persons', []) or []) + (nlp_results.get('key_locations', []) or [])),
                    nlp_results.get('sentiment', {}).get('score') if nlp_results.get('sentiment') else 0.0,
                    json.dumps(nlp_results.get('entities', []) or []),
                    json.dumps(combined_analysis)
                ))
            
            # Update article with BERT risk analysis
            cursor.execute('''
                UPDATE articles 
                SET 
                    risk_level = ?,
                    risk_score = ?
                WHERE id = ?
            ''', (
                bert_results['level'],
                bert_results['score'],
                article_id
            ))
            
            processed_count += 1
            
            print(f"   ✅ Análisis completado:")
            print(f"      - Riesgo BERT: {bert_results['level']} ({bert_results['score']:.3f})")
            sentiment_label = nlp_results.get('sentiment', {}).get('label', 'neutral') if nlp_results.get('sentiment') else 'neutral'
            sentiment_score = nlp_results.get('sentiment', {}).get('score', 0.0) if nlp_results.get('sentiment') else 0.0
            print(f"      - Sentimiento: {sentiment_label} ({sentiment_score:.3f})")
            print(f"      - Entidades: {nlp_results['total_entities']}")
            print(f"      - Personas clave: {', '.join(nlp_results['key_persons'][:3])}")
            print(f"      - Ubicaciones: {', '.join(nlp_results['key_locations'][:3])}")
            
        except Exception as e:
            logger.error(f"Error procesando artículo {article_id}: {e}")
            continue
    
    # Commit changes
    conn.commit()
    
    print(f"\n🎯 Resumen del procesamiento:")
    print(f"   Artículos procesados: {processed_count}")
    
    # Show some statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            AVG(sentiment) as avg_sentiment,
            COUNT(CASE WHEN advanced_nlp IS NOT NULL THEN 1 END) as with_advanced_nlp
        FROM processed_data pd
        JOIN articles a ON pd.article_id = a.id
        WHERE a.created_at > datetime('now', '-7 days')
    ''')
    
    stats = cursor.fetchone()
    if stats:
        print(f"   Total artículos (7 días): {stats[0]}")
        print(f"   Sentimiento promedio: {stats[1]:.3f}")
        print(f"   Con análisis NLP avanzado: {stats[2]}")
    
    # Show risk distribution
    cursor.execute('''
        SELECT risk_level, COUNT(*) as count
        FROM articles 
        WHERE created_at > datetime('now', '-7 days')
        GROUP BY risk_level
        ORDER BY count DESC
    ''')
    
    risk_dist = cursor.fetchall()
    print(f"\n📊 Distribución de riesgo (últimos 7 días):")
    for level, count in risk_dist:
        print(f"   {level}: {count} artículos")
    
    conn.close()
    print("\n✅ Integración de NLP avanzado completada!")

def add_advanced_nlp_column():
    """Añade columna para análisis NLP avanzado si no existe."""
    db_path = 'data/geopolitical_intel.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            ALTER TABLE processed_data 
            ADD COLUMN advanced_nlp TEXT
        ''')
        conn.commit()
        print("✅ Columna advanced_nlp añadida a processed_data")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️  Columna advanced_nlp ya existe")
        else:
            print(f"❌ Error añadiendo columna: {e}")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando integración de análisis NLP avanzado...")
    print("=" * 60)
    
    # Add column if needed
    add_advanced_nlp_column()
    
    # Run integration
    integrate_advanced_nlp()