#!/usr/bin/env python3
"""
Reprocess existing articles with the new BERT risk analyzer
"""
import sqlite3
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.utils.bert_risk_analyzer import BERTRiskAnalyzer

def reprocess_articles():
    """Reprocess existing articles with BERT risk analyzer."""
    
    # Initialize BERT analyzer
    print("Initializing BERT Risk Analyzer...")
    analyzer = BERTRiskAnalyzer()
    
    # Connect to database
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Get articles from last 7 days that need reprocessing
    cursor.execute("""
        SELECT id, title, content, country, risk_level
        FROM articles 
        WHERE created_at > datetime('now', '-7 days')
        ORDER BY created_at DESC
        LIMIT 50
    """)
    
    articles = cursor.fetchall()
    print(f"Found {len(articles)} articles to reprocess...")
    
    updated_count = 0
    high_risk_found = 0
    medium_risk_found = 0
    
    for article in articles:
        article_id, title, content, country, old_risk_level = article
        
        print(f"\nProcessing ID {article_id}: {title[:50]}...")
        print(f"  Old risk level: {old_risk_level}")
        
        # Analyze with BERT
        try:
            result = analyzer.analyze_risk(
                title=title or '',
                content=content or '',
                country=country
            )
            
            new_risk_level = result['level']
            new_risk_score = result['score']
            
            print(f"  New risk level: {new_risk_level} (score: {new_risk_score:.3f})")
            print(f"  Model used: {result['model_used']}")
            print(f"  Reasoning: {result['reasoning'][:100]}...")
            
            # Update database if risk level changed
            if new_risk_level != old_risk_level:
                cursor.execute("""
                    UPDATE articles 
                    SET risk_level = ?, risk_score = ?
                    WHERE id = ?
                """, (new_risk_level, new_risk_score, article_id))
                
                updated_count += 1
                print(f"  ✅ UPDATED: {old_risk_level} → {new_risk_level}")
                
                if new_risk_level == 'high':
                    high_risk_found += 1
                elif new_risk_level == 'medium':
                    medium_risk_found += 1
            else:
                print(f"  ℹ️  No change needed")
                
        except Exception as e:
            print(f"  ❌ Error analyzing article: {e}")
            continue
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n🎯 REPROCESSING COMPLETE:")
    print(f"  Total articles processed: {len(articles)}")
    print(f"  Articles updated: {updated_count}")
    print(f"  New high-risk articles: {high_risk_found}")
    print(f"  New medium-risk articles: {medium_risk_found}")
    
    # Show current distribution
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            risk_level,
            COUNT(*) as count
        FROM articles 
        WHERE created_at > datetime('now', '-7 days')
        GROUP BY risk_level
        ORDER BY 
            CASE risk_level 
                WHEN 'high' THEN 1 
                WHEN 'medium' THEN 2 
                WHEN 'low' THEN 3 
                ELSE 4 
            END
    """)
    
    print(f"\n📊 CURRENT RISK DISTRIBUTION (last 7 days):")
    for row in cursor.fetchall():
        risk_level, count = row
        print(f"  {risk_level or 'NULL':>8}: {count:>4} articles")
    
    conn.close()

if __name__ == "__main__":
    reprocess_articles()