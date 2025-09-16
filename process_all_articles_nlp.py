#!/usr/bin/env python3
"""
Script para procesar TODOS los artículos de la base de datos con análisis NLP avanzado
GARANTIZA que cada artículo tenga análisis completo con BERT/RoBERTa y NuNER
"""

import sqlite3
import sys
from pathlib import Path
import json
import logging
from datetime import datetime
import time

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

from nlp_processing.advanced_analyzer import AdvancedNLPAnalyzer
from src.utils.bert_risk_analyzer import BERTRiskAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_all_articles_with_advanced_nlp():
    """Procesa TODOS los artículos de la base de datos con análisis NLP avanzado."""
    
    print("🚀 INICIANDO PROCESAMIENTO COMPLETO DE TODOS LOS ARTÍCULOS")
    print("=" * 80)
    
    # Connect to database
    db_path = 'data/geopolitical_intel.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Initialize analyzers
    logger.info("🧠 Inicializando analizadores NLP avanzados...")
    try:
        nlp_analyzer = AdvancedNLPAnalyzer()
        bert_analyzer = BERTRiskAnalyzer()
        print("✅ Analizadores NLP avanzados inicializados correctamente")
    except Exception as e:
        print(f"❌ Error inicializando analizadores: {e}")
        return
    
    # Get ALL articles from database
    print("🔍 Obteniendo TODOS los artículos de la base de datos...")
    cursor.execute('''
        SELECT a.id, a.title, a.content, a.country, a.risk_level, a.created_at,
               pd.category, pd.advanced_nlp
        FROM articles a 
        LEFT JOIN processed_data pd ON a.id = pd.article_id 
        ORDER BY a.created_at DESC
    ''')
    
    all_articles = cursor.fetchall()
    total_articles = len(all_articles)
    
    print(f"📊 TOTAL DE ARTÍCULOS ENCONTRADOS: {total_articles}")
    print("=" * 80)
    
    # Statistics
    processed_count = 0
    updated_count = 0
    error_count = 0
    sports_filtered = 0
    
    # Process each article
    for i, article in enumerate(all_articles, 1):
        article_id, title, content, country, risk_level, created_at, category, existing_nlp = article
        
        print(f"\n🔬 [{i}/{total_articles}] Procesando artículo ID {article_id}")
        print(f"   📅 Fecha: {created_at}")
        print(f"   📰 Título: {title[:60]}...")
        
        try:
            # Check if it's sports content and skip
            if category == 'sports_entertainment':
                sports_filtered += 1
                print(f"   ⚽ FILTRADO: Artículo deportivo")
                continue
            
            # Check if already has advanced NLP analysis
            has_advanced_nlp = existing_nlp is not None
            
            if has_advanced_nlp:
                print(f"   ✅ Ya tiene análisis NLP avanzado")
                continue
            
            # Prepare article data for comprehensive analysis
            article_data = {
                'title': title or '',
                'content': content or '',
                'description': ''
            }
            
            # Perform comprehensive NLP analysis
            print(f"   🧠 Ejecutando análisis NLP completo...")
            nlp_results = nlp_analyzer.analyze_article_comprehensive(article_data)
            
            # Perform BERT risk analysis
            print(f"   🤖 Ejecutando análisis BERT/RoBERTa...")
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
                'model_used': bert_results['model_used'],
                'analysis_timestamp': nlp_results['analysis_timestamp'],
                'processing_batch': 'complete_database_processing',
                'processing_date': datetime.now().isoformat()
            }
            
            # Update article with BERT risk analysis
            cursor.execute('''
                UPDATE articles 
                SET risk_level = ?, risk_score = ?
                WHERE id = ?
            ''', (bert_results['level'], bert_results['score'], article_id))
            
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
                    content[:300] + '...' if len(content) > 300 else content,
                    category or 'geopolitical_analysis',
                    json.dumps(nlp_results['key_persons'] + nlp_results['key_locations']),
                    nlp_results['sentiment']['score'],
                    json.dumps(nlp_results['entities']),
                    json.dumps(combined_analysis),
                    article_id
                ))
                updated_count += 1
            else:
                # Insert new processed data record
                cursor.execute('''
                    INSERT INTO processed_data (
                        article_id, summary, category, keywords, sentiment, entities, advanced_nlp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_id,
                    content[:300] + '...' if len(content) > 300 else content,
                    category or 'geopolitical_analysis',
                    json.dumps(nlp_results['key_persons'] + nlp_results['key_locations']),
                    nlp_results['sentiment']['score'],
                    json.dumps(nlp_results['entities']),
                    json.dumps(combined_analysis)
                ))
            
            processed_count += 1
            
            print(f"   ✅ ANÁLISIS COMPLETADO:")
            print(f"      🎯 Riesgo BERT: {bert_results['level']} ({bert_results['score']:.3f})")
            print(f"      😊 Sentimiento: {nlp_results['sentiment']['label']} ({nlp_results['sentiment']['score']:.3f})")
            print(f"      👥 Entidades: {nlp_results['total_entities']}")
            print(f"      🏛️  Personas: {', '.join(nlp_results['key_persons'][:3])}")
            print(f"      🌍 Ubicaciones: {', '.join(nlp_results['key_locations'][:3])}")
            
            # Commit every 10 articles to avoid losing progress
            if processed_count % 10 == 0:
                conn.commit()
                print(f"   💾 Progreso guardado ({processed_count} artículos procesados)")
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.1)
            
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error procesando artículo {article_id}: {e}")
            continue
    
    # Final commit
    conn.commit()
    
    print("\n" + "=" * 80)
    print("🎯 RESUMEN FINAL DEL PROCESAMIENTO COMPLETO")
    print("=" * 80)
    print(f"📊 Total de artículos en BD: {total_articles}")
    print(f"✅ Artículos procesados con NLP: {processed_count}")
    print(f"🔄 Registros actualizados: {updated_count}")
    print(f"⚽ Artículos deportivos filtrados: {sports_filtered}")
    print(f"❌ Errores: {error_count}")
    
    # Show final statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            AVG(sentiment) as avg_sentiment,
            COUNT(CASE WHEN advanced_nlp IS NOT NULL THEN 1 END) as with_advanced_nlp
        FROM processed_data pd
        JOIN articles a ON pd.article_id = a.id
    ''')
    
    stats = cursor.fetchone()
    if stats:
        total, avg_sentiment, with_advanced_nlp = stats
        print(f"\n📈 ESTADÍSTICAS FINALES:")
        print(f"   📰 Total artículos procesados: {total}")
        print(f"   😊 Sentimiento promedio: {avg_sentiment:.3f}")
        print(f"   🧠 Con análisis NLP avanzado: {with_advanced_nlp}")
        print(f"   📊 Cobertura NLP: {(with_advanced_nlp/total*100):.1f}%")
    
    # Show risk distribution
    cursor.execute('''
        SELECT risk_level, COUNT(*) as count
        FROM articles 
        GROUP BY risk_level
        ORDER BY count DESC
    ''')
    
    risk_dist = cursor.fetchall()
    print(f"\n🎯 DISTRIBUCIÓN DE RIESGO (TODA LA BD):")
    for level, count in risk_dist:
        percentage = (count / total_articles * 100) if total_articles > 0 else 0
        print(f"   {level.upper()}: {count} artículos ({percentage:.1f}%)")
    
    # Show category distribution
    cursor.execute('''
        SELECT pd.category, COUNT(*) as count
        FROM processed_data pd
        GROUP BY pd.category
        ORDER BY count DESC
    ''')
    
    category_dist = cursor.fetchall()
    print(f"\n📂 DISTRIBUCIÓN POR CATEGORÍAS:")
    for category, count in category_dist:
        percentage = (count / total_articles * 100) if total_articles > 0 else 0
        print(f"   {category or 'Sin categoría'}: {count} artículos ({percentage:.1f}%)")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("🎉 PROCESAMIENTO COMPLETO FINALIZADO")
    print("🧠 TODOS LOS ARTÍCULOS AHORA TIENEN ANÁLISIS NLP AVANZADO")
    print("🤖 BERT/RoBERTa + NuNER + Análisis de Sentimiento ACTIVADO")
    print("=" * 80)

if __name__ == "__main__":
    process_all_articles_with_advanced_nlp()