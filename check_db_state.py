#!/usr/bin/env python3
"""
Quick database check to understand the current state
"""
import sqlite3

def check_database_state():
    db_path = "./data/geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 VERIFICACIÓN RÁPIDA DE BASE DE DATOS")
        print("=" * 50)
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tablas: {', '.join(tables)}")
        
        # Check processed_data structure
        if 'processed_data' in tables:
            cursor.execute("PRAGMA table_info(processed_data)")
            columns = cursor.fetchall()
            print(f"\n📊 Columnas en processed_data:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            # Count records with advanced_nlp
            cursor.execute("SELECT COUNT(*) FROM processed_data WHERE advanced_nlp IS NOT NULL AND advanced_nlp != ''")
            advanced_count = cursor.fetchone()[0]
            print(f"\n🧠 Registros con advanced_nlp: {advanced_count}")
            
            # Total records in processed_data
            cursor.execute("SELECT COUNT(*) FROM processed_data")
            total_processed = cursor.fetchone()[0]
            print(f"📊 Total registros en processed_data: {total_processed}")
        
        # Check articles with risk_level (this indicates BERT processing was successful)
        cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level IS NOT NULL")
        articles_with_risk = cursor.fetchone()[0]
        print(f"\n🎯 Artículos con risk_level: {articles_with_risk}")
        
        # Check recent articles
        cursor.execute("""
            SELECT COUNT(*) 
            FROM articles 
            WHERE created_at >= datetime('now', '-1 day')
        """)
        recent_articles = cursor.fetchone()[0]
        print(f"📅 Artículos de las últimas 24h: {recent_articles}")
        
        # Sample some articles to see their processing status
        cursor.execute("""
            SELECT a.id, a.title, a.risk_level, 
                   (pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != '') as has_nlp
            FROM articles a
            LEFT JOIN processed_data pd ON a.url = pd.url
            WHERE a.id IN (1117, 1116, 1115, 1114, 1113)
            ORDER BY a.id DESC
        """)
        
        print(f"\n🔬 MUESTRA DE ARTÍCULOS PROBLEMÁTICOS:")
        samples = cursor.fetchall()
        for article_id, title, risk_level, has_nlp in samples:
            title_short = title[:50] + "..." if len(title) > 50 else title
            nlp_status = "✅" if has_nlp else "❌"
            risk_display = risk_level or "None"
            print(f"   ID {article_id}: {nlp_status} NLP | Risk: {risk_display} | {title_short}")
        
        conn.close()
        
        print(f"\n💡 INTERPRETACIÓN:")
        if articles_with_risk > 0:
            print(f"   ✅ El procesamiento BERT está funcionando ({articles_with_risk} artículos)")
        if advanced_count == 0:
            print(f"   ⚠️ Los registros processed_data no se están creando/actualizando correctamente")
            print(f"   🔧 Posible problema: JOIN entre articles y processed_data por URL")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database_state()