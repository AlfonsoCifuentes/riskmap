#!/usr/bin/env python3
"""
Create sample articles with real URLs for testing the dashboard
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random

# Database path
BASE_DIR = Path('.').resolve()
DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')

# Sample articles with real-looking URLs from our sources
SAMPLE_ARTICLES = [
    {
        'title': 'Tensions Rise in Eastern Europe as NATO Increases Military Presence',
        'content': 'NATO has announced a significant increase in military presence along its eastern borders following recent geopolitical developments. The alliance cited growing security concerns and the need to reassure member states in the region.',
        'url': 'https://www.reuters.com/world/europe/nato-increases-military-presence-eastern-europe-2025-01-15/',
        'source': 'Reuters',
        'language': 'en',
        'country': 'Ukraine',
        'risk_level': 'high',
        'risk_score': 0.85,
        'image_url': 'https://www.reuters.com/resizer/images/nato-military-presence.jpg'
    },
    {
        'title': 'Middle East Peace Talks Resume After Six-Month Hiatus',
        'content': 'International mediators have successfully brought key stakeholders back to the negotiating table after a prolonged break in diplomatic efforts. The talks aim to address ongoing regional conflicts and establish sustainable peace frameworks.',
        'url': 'https://www.bbc.com/news/world-middle-east-peace-talks-resume-2025',
        'source': 'BBC News',
        'language': 'en',
        'country': 'Israel',
        'risk_level': 'medium',
        'risk_score': 0.65,
        'image_url': 'https://ichef.bbci.co.uk/news/peace-talks-middle-east.jpg'
    },
    {
        'title': 'China Announces New Trade Initiatives with African Nations',
        'content': 'Beijing has unveiled a comprehensive trade package aimed at strengthening economic ties with African countries. The initiative includes infrastructure investments and technology transfer agreements.',
        'url': 'https://www.aljazeera.com/economy/china-africa-trade-initiatives-2025',
        'source': 'Al Jazeera',
        'language': 'en',
        'country': 'China',
        'risk_level': 'medium',
        'risk_score': 0.55,
        'image_url': 'https://www.aljazeera.com/wp-content/uploads/china-africa-trade.jpg'
    },
    {
        'title': 'European Union Implements New Climate Security Framework',
        'content': 'The EU has adopted a groundbreaking climate security framework that links environmental policies with defense strategies. The initiative addresses climate-related security threats and migration patterns.',
        'url': 'https://www.theguardian.com/world/2025/jan/15/eu-climate-security-framework',
        'source': 'The Guardian',
        'language': 'en',
        'country': 'Germany',
        'risk_level': 'low',
        'risk_score': 0.35,
        'image_url': 'https://i.guim.co.uk/img/media/eu-climate-security.jpg'
    },
    {
        'title': 'Latin American Summit Addresses Regional Economic Integration',
        'content': 'Leaders from across Latin America have gathered to discuss enhanced economic cooperation and regional integration initiatives. The summit focuses on trade agreements and infrastructure development.',
        'url': 'https://apnews.com/article/latin-america-economic-summit-2025',
        'source': 'Associated Press',
        'language': 'en',
        'country': 'Brazil',
        'risk_level': 'low',
        'risk_score': 0.25,
        'image_url': 'https://storage.googleapis.com/afs-prod/media/latin-america-summit.jpg'
    },
    {
        'title': 'Cyber Security Threats Target Critical Infrastructure Globally',
        'content': 'International cybersecurity agencies have reported a significant increase in attacks targeting critical infrastructure worldwide. Governments are implementing enhanced protection measures.',
        'url': 'https://www.washingtonpost.com/technology/cyber-threats-infrastructure-2025',
        'source': 'Washington Post',
        'language': 'en',
        'country': 'Global',
        'risk_level': 'high',
        'risk_score': 0.80,
        'image_url': 'https://www.washingtonpost.com/wp-apps/imrs.php?cyber-security-threats.jpg'
    },
    {
        'title': 'Asian Economic Forum Discusses Post-Pandemic Recovery Strategies',
        'content': 'Economic leaders from across Asia have convened to address recovery strategies and future economic resilience. The forum emphasizes sustainable development and technological innovation.',
        'url': 'https://www.ft.com/content/asian-economic-forum-recovery-2025',
        'source': 'Financial Times',
        'language': 'en',
        'country': 'Japan',
        'risk_level': 'low',
        'risk_score': 0.30,
        'image_url': 'https://www.ft.com/__origami/service/image/asian-economic-forum.jpg'
    },
    {
        'title': 'Arctic Council Addresses Climate Change and Territorial Disputes',
        'content': 'The Arctic Council has convened an emergency session to address accelerating climate change impacts and emerging territorial disputes in the region. New cooperation frameworks are being discussed.',
        'url': 'https://www.reuters.com/world/arctic-council-climate-territorial-disputes-2025',
        'source': 'Reuters',
        'language': 'en',
        'country': 'Russia',
        'risk_level': 'medium',
        'risk_score': 0.60,
        'image_url': 'https://www.reuters.com/resizer/arctic-council-meeting.jpg'
    }
]

def create_sample_articles():
    """Create sample articles in the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Clear existing articles to avoid conflicts
        print("🧹 Clearing existing articles...")
        cursor.execute('DELETE FROM processed_data')
        cursor.execute('DELETE FROM articles')
        
        added_count = 0
        
        for i, article_data in enumerate(SAMPLE_ARTICLES):
            # Create article with timestamp spread over last 7 days
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            created_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
            
            cursor.execute('''
                INSERT INTO articles (
                    title, content, url, source, language, country, 
                    risk_level, risk_score, image_url, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_data['title'],
                article_data['content'],
                article_data['url'],
                article_data['source'],
                article_data['language'],
                article_data['country'],
                article_data['risk_level'],
                article_data['risk_score'],
                article_data['image_url'],
                created_at.isoformat()
            ))
            
            article_id = cursor.lastrowid
            
            # Create corresponding processed_data entry
            cursor.execute('''
                INSERT INTO processed_data (
                    article_id, summary, category, keywords, sentiment, entities
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                article_id,
                article_data['content'][:200] + '...',
                'geopolitical_analysis',
                '["geopolitics", "international", "security", "diplomacy"]',
                random.uniform(-0.2, 0.2),  # Neutral sentiment
                '["government", "international_organization"]'
            ))
            
            added_count += 1
            print(f"✓ Added: {article_data['title'][:50]}...")
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 Successfully created {added_count} sample articles")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample articles: {e}")
        return False

def show_articles_summary():
    """Show summary of created articles."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Count by risk level
        cursor.execute('''
            SELECT risk_level, COUNT(*) as count
            FROM articles
            GROUP BY risk_level
            ORDER BY 
                CASE risk_level 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END
        ''')
        
        print(f"\n📈 Articles by Risk Level:")
        for risk_level, count in cursor.fetchall():
            print(f"   {risk_level}: {count} articles")
        
        # Count by country
        cursor.execute('''
            SELECT country, COUNT(*) as count
            FROM articles
            GROUP BY country
            ORDER BY count DESC
        ''')
        
        print(f"\n🌍 Articles by Country:")
        for country, count in cursor.fetchall():
            print(f"   {country}: {count} articles")
        
        # Show recent articles
        cursor.execute('''
            SELECT title, risk_level, country, created_at
            FROM articles
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        
        print(f"\n📰 Most Recent Articles:")
        for title, risk_level, country, created_at in cursor.fetchall():
            print(f"   [{risk_level.upper()}] {title[:40]}... ({country})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing summary: {e}")

if __name__ == "__main__":
    print("📰 Creating Sample Articles for Geopolitical Intelligence Dashboard")
    print("=" * 65)
    
    if create_sample_articles():
        show_articles_summary()
        print(f"\n✅ Sample articles successfully created!")
        print(f"🔄 Restart your dashboard to see the new articles.")
    else:
        print(f"\n❌ Failed to create sample articles")