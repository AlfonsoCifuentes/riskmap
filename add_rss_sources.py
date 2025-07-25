#!/usr/bin/env python3
"""
Script to add RSS news sources to the geopolitical intelligence database
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# Database path
BASE_DIR = Path('.').resolve()
DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')

# RSS Sources list
RSS_SOURCES = [
    # International News Agencies
    ("Reuters World", "https://www.reuters.com/world/rss", "en", "global", "high", True),
    ("AP News Top Stories", "https://apnews.com/hub/ap-top-news?output=rss", "en", "global", "high", True),
    ("AFP News Hub", "https://www.afp.com/en/news-hub/rss", "en", "global", "high", True),
    ("Bloomberg Politics", "https://www.bloomberg.com/politics/feeds/site.xml", "en", "global", "high", True),
    ("BBC World News", "https://www.bbc.com/news/world/rss.xml", "en", "global", "high", True),
    ("Al Jazeera English", "https://www.aljazeera.com/xml/rss/all.xml", "en", "global", "high", True),
    ("Al Jazeera Arabic", "https://www.aljazeera.net/aljazeera/rss", "ar", "middle_east", "high", True),
    ("Deutsche Welle World", "https://rss.dw.com/rdf/rss-en-world", "en", "europe", "medium", True),
    ("Euronews English", "https://www.euronews.com/rss?level=theme&name=news", "en", "europe", "medium", True),
    ("Euronews French", "https://fr.euronews.com/rss?level=theme&name=news", "fr", "europe", "medium", True),
    ("Euronews Spanish", "https://es.euronews.com/rss?level=theme&name=news", "es", "europe", "medium", True),
    ("The Guardian World", "https://www.theguardian.com/world/rss", "en", "global", "high", True),
    ("New York Times World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "en", "global", "high", True),
    ("Washington Post World", "https://feeds.washingtonpost.com/rss/world", "en", "global", "high", True),
    ("Financial Times World", "https://www.ft.com/world?format=rss", "en", "global", "high", True),
    ("Politico", "https://www.politico.com/rss/politics-news.xml", "en", "us", "medium", True),
    ("Voice of America", "https://www.voanews.com/rss", "en", "global", "medium", True),
    ("VOA Noticias", "https://www.voanoticias.com/rss", "es", "latin_america", "medium", True),
    ("Radio Free Europe", "https://www.rferl.org/api/zrqiteuuir", "en", "europe", "medium", True),
    ("RFI World French", "https://www.rfi.fr/fr/monde/rss", "fr", "global", "medium", True),
    ("RFI Africa", "https://www.rfi.fr/fr/afrique/rss", "fr", "africa", "medium", True),
    
    # News APIs (require configuration)
    ("GDELT Events", "https://api.gdeltproject.org/api/v2/events/doc?query={keywords}", "en", "global", "high", False),
    ("GDELT Documents", "https://api.gdeltproject.org/api/v2/doc/doc?query={keywords}", "en", "global", "high", False),
    ("Event Registry", "https://eventregistry.org/documentation", "en", "global", "high", False),
    ("MediaStack API", "https://api.mediastack.com/v1/news?access_key=YOUR_KEY", "en", "global", "high", False),
    ("NewsAPI Geopolitics", "https://newsapi.org/v2/everything?q=geopolitics", "en", "global", "high", False),
    ("Currents API", "https://api.currentsapi.services/v1/latest-news", "en", "global", "medium", False),
    ("Aylien News API", "https://newsapi.aylien.com/news", "en", "global", "medium", False),
    
    # Social and Aggregated Sources
    ("Reddit WorldNews", "https://www.reddit.com/r/worldnews/.rss", "en", "global", "low", True),
    ("Google News Geopolitics", "https://news.google.com/rss/search?q=geopolitics", "en", "global", "medium", True),
    ("Bing News Geopolitics", "https://api.bing.microsoft.com/v7.0/news/search?q=geopolitics", "en", "global", "medium", False),
    
    # Spanish Language Sources
    ("El País Internacional", "https://elpais.com/rss/internacional.xml", "es", "spain", "high", True),
    ("El Mundo Internacional", "https://www.elmundo.es/rss/internacional.xml", "es", "spain", "high", True),
    ("BBC Mundo", "https://www.bbc.com/mundo/temas/internacional/index.xml", "es", "latin_america", "high", True),
    ("DW Español", "https://rss.dw.com/rdf/rss-es-mundo", "es", "latin_america", "medium", True),
    ("France24 Español", "https://www.france24.com/es/rss", "es", "latin_america", "medium", True),
    ("RTVE Internacional", "https://www.rtve.es/rss/noticias/internacional/", "es", "spain", "medium", True),
    ("Infobae Mundo", "https://www.infobae.com/america/mundo/rss", "es", "latin_america", "medium", True),
    ("La Jornada Mundo", "https://www.jornada.com.mx/rss/mundo.xml", "es", "mexico", "medium", True),
    
    # French Language Sources
    ("Le Monde International", "https://www.lemonde.fr/international/rss_full.xml", "fr", "france", "high", True),
    ("Le Figaro International", "https://www.lefigaro.fr/rss/figaro_international.xml", "fr", "france", "high", True),
    ("France24 French", "https://www.france24.com/fr/monde/rss", "fr", "france", "medium", True),
    ("TV5Monde", "https://www.tv5monde.com/rss/actualite-inter", "fr", "france", "medium", True),
    
    # Portuguese Language Sources
    ("Folha Mundo", "https://feeds.folha.uol.com.br/mundo/rss091.xml", "pt", "brazil", "medium", True),
    ("O Globo Mundo", "https://oglobo.globo.com/rss/mundo", "pt", "brazil", "medium", True),
    ("RTP Notícias", "https://www.rtp.pt/noticias/rss", "pt", "portugal", "medium", True),
    ("DW Português", "https://rss.dw.com/rdf/rss-pt-br", "pt", "brazil", "medium", True),
    
    # German Language Sources
    ("Der Spiegel International", "https://www.spiegel.de/international/index.rss", "de", "germany", "high", True),
    ("Die Welt Ausland", "https://www.welt.de/feeds/section/politik/ausland.rss", "de", "germany", "medium", True),
    ("Tagesschau", "https://www.tagesschau.de/xml/rss2", "de", "germany", "medium", True),
    
    # Arabic Language Sources
    ("Al Arabiya", "https://www.alarabiya.net/.mrss/ar.xml", "ar", "middle_east", "high", True),
    ("Asharq Al-Awsat", "https://aawsat.com/feed", "ar", "middle_east", "high", True),
    ("Sky News Arabia", "https://www.skynewsarabia.com/web/rss", "ar", "middle_east", "medium", True),
    
    # Russian Language Sources
    ("TASS", "https://tass.com/rss/v2.xml", "ru", "russia", "high", True),
    ("RT News", "https://www.rt.com/rss/news/", "ru", "russia", "medium", True),
    ("RBC Politics", "https://rssexport.rbc.ru/rbcnews/politics/index.rss", "ru", "russia", "medium", True),
    ("Interfax", "https://www.interfax.ru/rss.asp", "ru", "russia", "medium", True),
    
    # Chinese Language Sources
    ("Xinhua World", "http://www.xinhuanet.com/english/rss/worldrss.xml", "zh", "china", "high", True),
    ("Global Times World", "https://www.globaltimes.cn/rss/world.xml", "zh", "china", "medium", True),
    ("China Daily World", "http://www.chinadaily.com.cn/rss/world_rss.xml", "zh", "china", "medium", True),
    
    # Japanese Language Sources
    ("NHK World", "https://www3.nhk.or.jp/nhkworld/en/news/rss/", "ja", "japan", "medium", True),
    ("Japan Times World", "https://www.japantimes.co.jp/news_category/world/feed/", "ja", "japan", "medium", True),
    
    # Korean Language Sources
    ("Yonhap Politics", "https://en.yna.co.kr/RSS/news?section=politics", "ko", "south_korea", "medium", True),
    ("KBS World Politics", "http://world.kbs.co.kr/rss/news_list.htm?lang=e&id=Po", "ko", "south_korea", "medium", True),
    
    # Indian Sources
    ("The Hindu International", "https://www.thehindu.com/news/international/feeder/default.rss", "en", "india", "medium", True),
    ("Hindustan Times World", "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml", "en", "india", "medium", True),
    ("Dawn Pakistan", "https://www.dawn.com/feeds/home", "en", "pakistan", "medium", True),
    
    # African Sources
    ("AllAfrica", "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "en", "africa", "medium", True),
    ("Nation Africa", "https://nation.africa/kenya/rssfeed", "en", "africa", "medium", True),
    ("Mail & Guardian", "https://mg.co.za/rss/", "en", "south_africa", "medium", True),
    ("Jeune Afrique", "https://www.jeuneafrique.com/rss", "fr", "africa", "medium", True),
    
    # Latin American Sources
    ("Clarín Mundo", "https://www.clarin.com/rss/mundo/", "es", "argentina", "medium", True),
    ("El Mercurio Mundo", "https://www.emol.com/rss/rss.asp?canal=mundo", "es", "chile", "medium", True),
    ("La Nación Internacional", "https://www.lanacion.com.ar/rss/categoria_id=30", "es", "argentina", "medium", True),
    ("Semana Mundo", "https://www.semana.com/rss/mundo/", "es", "colombia", "medium", True),
    
    # Think Tanks and Analysis
    ("Chatham House", "https://www.chathamhouse.org/rss.xml", "en", "global", "high", True),
    ("Carnegie Endowment", "https://carnegieendowment.org/rss/global", "en", "global", "high", True),
    ("CSIS", "https://www.csis.org/rss.xml", "en", "global", "high", True),
    ("Brookings Foreign Policy", "https://www.brookings.edu/topic/foreign-policy/feed/", "en", "global", "high", True),
    ("Council on Foreign Relations", "https://www.cfr.org/rss/newsletter", "en", "global", "high", True),
    ("International Crisis Group", "https://www.crisisgroup.org/rss.xml", "en", "global", "high", True),
]

def create_sources_table(cursor):
    """Create the sources table if it doesn't exist."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            language TEXT NOT NULL,
            region TEXT NOT NULL,
            priority TEXT NOT NULL,
            active BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_fetched TIMESTAMP,
            fetch_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            last_error TEXT
        )
    ''')

def add_rss_sources():
    """Add all RSS sources to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create sources table
        create_sources_table(cursor)
        print("✓ Sources table created/verified")
        
        # Add sources
        added_count = 0
        skipped_count = 0
        
        for name, url, language, region, priority, active in RSS_SOURCES:
            try:
                cursor.execute('''
                    INSERT INTO sources (name, url, language, region, priority, active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, url, language, region, priority, active))
                added_count += 1
                print(f"✓ Added: {name}")
            except sqlite3.IntegrityError:
                skipped_count += 1
                print(f"⚠ Skipped (already exists): {name}")
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 Summary:")
        print(f"   Added: {added_count} sources")
        print(f"   Skipped: {skipped_count} sources")
        print(f"   Total in list: {len(RSS_SOURCES)} sources")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding RSS sources: {e}")
        return False

def show_sources_summary():
    """Show summary of added sources."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Count by language
        cursor.execute('''
            SELECT language, COUNT(*) as count
            FROM sources
            GROUP BY language
            ORDER BY count DESC
        ''')
        
        print(f"\n📈 Sources by Language:")
        for lang, count in cursor.fetchall():
            print(f"   {lang}: {count} sources")
        
        # Count by region
        cursor.execute('''
            SELECT region, COUNT(*) as count
            FROM sources
            GROUP BY region
            ORDER BY count DESC
        ''')
        
        print(f"\n🌍 Sources by Region:")
        for region, count in cursor.fetchall():
            print(f"   {region}: {count} sources")
        
        # Count by priority
        cursor.execute('''
            SELECT priority, COUNT(*) as count
            FROM sources
            GROUP BY priority
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END
        ''')
        
        print(f"\n⭐ Sources by Priority:")
        for priority, count in cursor.fetchall():
            print(f"   {priority}: {count} sources")
        
        # Active vs inactive
        cursor.execute('''
            SELECT active, COUNT(*) as count
            FROM sources
            GROUP BY active
        ''')
        
        print(f"\n🔄 Source Status:")
        for active, count in cursor.fetchall():
            status = "Active" if active else "Inactive"
            print(f"   {status}: {count} sources")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing summary: {e}")

if __name__ == "__main__":
    print("🚀 Adding RSS News Sources to Geopolitical Intelligence Database")
    print("=" * 60)
    
    if add_rss_sources():
        show_sources_summary()
        print(f"\n✅ RSS sources successfully added to database!")
        print(f"📍 Database location: {DB_PATH}")
    else:
        print(f"\n❌ Failed to add RSS sources")