#!/usr/bin/env python3

from src.utils.config import db_manager

def test_database():
    try:
        # Test basic database queries
        articles = db_manager.execute_query("SELECT COUNT(*) as total FROM articles")
        total_articles = articles[0]['total'] if articles else 0
        print(f"📊 Total articles in database: {total_articles}")
        
        if total_articles > 0:
            # Get some sample articles
            sample_articles = db_manager.execute_query(
                "SELECT title, source, created_at FROM articles LIMIT 3"
            )
            print(f"📝 Sample articles ({len(sample_articles)}):")
            for i, article in enumerate(sample_articles):
                title = article['title'][:50] + '...' if len(article['title']) > 50 else article['title']
                source = article.get('source', 'Unknown')
                print(f"  {i+1}. {title} ({source})")
                
            # Test high risk articles
            high_risk = db_manager.execute_query(
                "SELECT COUNT(*) as total FROM articles WHERE risk_score >= 7"
            )
            high_risk_count = high_risk[0]['total'] if high_risk else 0
            print(f"🔥 High risk articles: {high_risk_count}")
                
        else:
            print("⚠️ No articles found in database!")
            
        # Test AI analysis
        try:
            from src.analytics.ai_models import AIModelManager
            ai_manager = AIModelManager()
            available_models = ai_manager.get_available_models()
            print(f"🤖 Available AI models: {available_models}")
        except Exception as e:
            print(f"❌ Error with AI models: {e}")
            
    except Exception as e:
        print(f"💥 Database error: {e}")

if __name__ == "__main__":
    test_database()
