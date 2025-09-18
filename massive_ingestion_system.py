#!/usr/bin/env python3
"""
Sistema de Ingesta Masiva de Noticias Reales
Aumenta significativamente el número de artículos, regiones y alertas usando solo fuentes RSS reales.
"""

import sys
import os
import logging
import sqlite3
import feedparser
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MassiveNewsIngestion:
    """Sistema de ingesta masiva de noticias reales."""
    
    def __init__(self):
        self.db_path = "./data/geopolitical_intel.db"
        self.stats = {
            'total_articles': 0,
            'new_articles': 0,
            'sources_processed': 0,
            'regions_detected': set(),
            'alerts_generated': 0,
            'errors': 0
        }
        
        # Massive RSS sources - REAL ONLY
        self.rss_sources = self.get_massive_rss_sources()
        self.setup_database()
    
    def get_massive_rss_sources(self) -> List[Dict[str, Any]]:
        """Return massive list of real RSS sources for geopolitical news."""
        return [
            # International Major Sources
            {'name': 'BBC World', 'rss': 'http://feeds.bbci.co.uk/news/world/rss.xml', 'country': 'GB', 'priority': 'critical'},
            {'name': 'CNN International', 'rss': 'http://rss.cnn.com/rss/edition.rss', 'country': 'US', 'priority': 'critical'},
            {'name': 'Reuters World', 'rss': 'https://www.reuters.com/rssFeed/worldNews', 'country': 'GB', 'priority': 'critical'},
            {'name': 'Associated Press', 'rss': 'https://feeds.washingtonpost.com/rss/world', 'country': 'US', 'priority': 'critical'},
            {'name': 'Al Jazeera English', 'rss': 'https://www.aljazeera.com/xml/rss/all.xml', 'country': 'QA', 'priority': 'critical'},
            {'name': 'France 24', 'rss': 'https://www.france24.com/en/rss', 'country': 'FR', 'priority': 'high'},
            {'name': 'Deutsche Welle', 'rss': 'https://rss.dw.com/rdf/rss-en-all', 'country': 'DE', 'priority': 'high'},
            {'name': 'Euronews', 'rss': 'https://www.euronews.com/rss?format=mrss', 'country': 'FR', 'priority': 'high'},
            
            # Conflict Zone Sources  
            {'name': 'Українська Правда', 'rss': 'https://www.pravda.com.ua/rss/', 'country': 'UA', 'priority': 'critical'},
            {'name': 'BBC Україна', 'rss': 'https://feeds.bbci.co.uk/ukrainian/rss.xml', 'country': 'GB', 'priority': 'critical'},
            {'name': 'DW Українська', 'rss': 'https://rss.dw.com/rdf/rss-uk-all', 'country': 'DE', 'priority': 'critical'},
            
            # Middle East
            {'name': 'الجزيرة', 'rss': 'https://www.aljazeera.net/feed/rss/all', 'country': 'QA', 'priority': 'critical'},
            {'name': 'العربية', 'rss': 'https://www.alarabiya.net/ar/rss.xml', 'country': 'AE', 'priority': 'high'},
            {'name': 'Times of Israel', 'rss': 'https://www.timesofisrael.com/feed/', 'country': 'IL', 'priority': 'high'},
            {'name': 'Haaretz English', 'rss': 'https://www.haaretz.com/cmlink/1.628752', 'country': 'IL', 'priority': 'high'},
            
            # European Sources
            {'name': 'El País Internacional', 'rss': 'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada', 'country': 'ES', 'priority': 'high'},
            {'name': 'Le Monde International', 'rss': 'https://www.lemonde.fr/international/rss_full.xml', 'country': 'FR', 'priority': 'high'},
            {'name': 'Der Spiegel International', 'rss': 'https://www.spiegel.de/international/index.rss', 'country': 'DE', 'priority': 'high'},
            {'name': 'Corriere della Sera Esteri', 'rss': 'https://www.corriere.it/rss/esteri.xml', 'country': 'IT', 'priority': 'high'},
            
            # Russian/Eastern Europe
            {'name': 'РИА Новости', 'rss': 'https://ria.ru/export/rss2/archive/index.xml', 'country': 'RU', 'priority': 'high'},
            {'name': 'ТАСС', 'rss': 'https://tass.ru/rss/v2.xml', 'country': 'RU', 'priority': 'high'},
            {'name': 'Moscow Times', 'rss': 'https://www.themoscowtimes.com/rss/news', 'country': 'RU', 'priority': 'medium'},
            
            # Asia Pacific
            {'name': 'South China Morning Post', 'rss': 'https://www.scmp.com/rss/91/feed', 'country': 'HK', 'priority': 'high'},
            {'name': '联合早报', 'rss': 'https://www.zaobao.com.sg/realtime/china/rss.xml', 'country': 'SG', 'priority': 'high'},
            {'name': 'Japan Times', 'rss': 'https://www.japantimes.co.jp/feed/', 'country': 'JP', 'priority': 'medium'},
            {'name': 'Korea Herald', 'rss': 'http://www.koreaherald.com/common/rss_xml.php?ct=010000000', 'country': 'KR', 'priority': 'medium'},
            
            # Latin America
            {'name': 'Clarín Internacional', 'rss': 'https://www.clarin.com/rss/mundo/', 'country': 'AR', 'priority': 'medium'},
            {'name': 'Folha Internacional', 'rss': 'https://feeds.folha.uol.com.br/mundo/rss091.xml', 'country': 'BR', 'priority': 'medium'},
            {'name': 'El Universal México', 'rss': 'https://www.eluniversal.com.mx/rss.xml', 'country': 'MX', 'priority': 'medium'},
            
            # Africa & Middle East Expansion
            {'name': 'Daily Maverick', 'rss': 'https://www.dailymaverick.co.za/feed/', 'country': 'ZA', 'priority': 'medium'},
            {'name': 'Middle East Eye', 'rss': 'https://www.middleeasteye.net/rss.xml', 'country': 'GB', 'priority': 'high'},
            {'name': 'Middle East Monitor', 'rss': 'https://www.middleeastmonitor.com/feed/', 'country': 'GB', 'priority': 'medium'},
            
            # Think Tanks & Analysis
            {'name': 'Council on Foreign Relations', 'rss': 'https://www.cfr.org/rss/feed', 'country': 'US', 'priority': 'high'},
            {'name': 'Brookings Institution', 'rss': 'https://www.brookings.edu/feed/', 'country': 'US', 'priority': 'high'},
            {'name': 'Carnegie Endowment', 'rss': 'https://carnegieendowment.org/rss/rss.xml', 'country': 'US', 'priority': 'high'},
            {'name': 'Atlantic Council', 'rss': 'https://www.atlanticcouncil.org/feed/', 'country': 'US', 'priority': 'medium'},
            
            # Additional Global Sources
            {'name': 'The Guardian World', 'rss': 'https://www.theguardian.com/world/rss', 'country': 'GB', 'priority': 'high'},
            {'name': 'Washington Post World', 'rss': 'http://feeds.washingtonpost.com/rss/world', 'country': 'US', 'priority': 'high'},
            {'name': 'New York Times World', 'rss': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml', 'country': 'US', 'priority': 'high'},
            {'name': 'Foreign Policy', 'rss': 'https://foreignpolicy.com/feed/', 'country': 'US', 'priority': 'high'},
            {'name': 'Politico Europe', 'rss': 'https://www.politico.eu/rss/', 'country': 'BE', 'priority': 'medium'},
            
            # More Regional Sources
            {'name': 'Hürriyet Daily News', 'rss': 'http://www.hurriyetdailynews.com/rss', 'country': 'TR', 'priority': 'medium'},
            {'name': 'Tehran Times', 'rss': 'https://www.tehrantimes.com/rss', 'country': 'IR', 'priority': 'medium'},
            {'name': 'Dawn Pakistan', 'rss': 'https://www.dawn.com/feeds/world', 'country': 'PK', 'priority': 'medium'},
            {'name': 'Times of India World', 'rss': 'https://timesofindia.indiatimes.com/rssfeeds/296589292.cms', 'country': 'IN', 'priority': 'medium'},
            
            # Additional European
            {'name': 'Euractiv', 'rss': 'https://www.euractiv.com/feed/', 'country': 'BE', 'priority': 'medium'},
            {'name': 'POLITICO Europe', 'rss': 'https://www.politico.eu/rss/', 'country': 'BE', 'priority': 'medium'},
            {'name': 'Financial Times', 'rss': 'https://www.ft.com/world?format=rss', 'country': 'GB', 'priority': 'high'},
            
            # Specialized Geopolitical
            {'name': 'Stratfor', 'rss': 'https://worldview.stratfor.com/xml/rss', 'country': 'US', 'priority': 'high'},
            {'name': 'Defense News', 'rss': 'https://www.defensenews.com/arc/outboundfeeds/rss/', 'country': 'US', 'priority': 'medium'},
            {'name': 'Jane\'s Defence Weekly', 'rss': 'https://www.janes.com/feeds/defence-news', 'country': 'GB', 'priority': 'medium'},
        ]
    
    def setup_database(self):
        """Ensure database tables exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # No need to create table - it already exists with all columns
                pass
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id INTEGER,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        region TEXT,
                        description TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                """)
                
                conn.commit()
                logger.info("✅ Database setup completed")
                
        except Exception as e:
            logger.error(f"❌ Database setup error: {e}")
    
    def process_rss_feed(self, source: Dict[str, Any]) -> Dict[str, int]:
        """Process a single RSS feed."""
        try:
            # Download RSS feed
            response = requests.get(source['rss'], timeout=30, headers={
                'User-Agent': 'RiskMap/1.0 (News Aggregator)'
            })
            response.raise_for_status()
            
            # Parse RSS
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                return {'articles': 0, 'alerts': 0}
            
            articles_stored = 0
            alerts_generated = 0
            
            with sqlite3.connect(self.db_path) as conn:
                for entry in feed.entries[:20]:  # Limit per feed
                    try:
                        # Extract article data (fixing types)
                        title = str(entry.get('title', ''))
                        url = str(entry.get('link', ''))
                        summary = str(entry.get('summary', ''))
                        published = str(entry.get('published', ''))
                        
                        # Skip if missing essential data
                        if not title or not url:
                            continue
                        
                        # Check geopolitical relevance
                        if not self.is_geopolitical(title, summary):
                            continue
                        
                        # Extract region and image
                        region = self.extract_region(title, summary)
                        image_url = self.extract_image_url(entry)
                        risk_level = self.calculate_risk_level(title, summary)
                        
                        # Insert article (fixing SQL to use existing table structure)
                        cursor = conn.execute("""
                            INSERT OR IGNORE INTO articles 
                            (title, url, source, summary, published_at, 
                             country, region, image_url, geopolitical_relevance, risk_level)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            title, url, source['name'], summary, published,
                            source['country'], region, image_url, 1, risk_level
                        ))
                        
                        if conn.total_changes > 0:  # New article inserted
                            articles_stored += 1
                            self.stats['regions_detected'].add(region or 'Unknown')
                            
                            # Generate alert for high-risk articles
                            if risk_level == 'high' and source['priority'] in ['critical', 'high']:
                                article_id = cursor.lastrowid
                                conn.execute("""
                                    INSERT INTO alerts (article_id, alert_type, severity, region, description)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (
                                    article_id, 'geopolitical_risk', 'critical', region or 'Unknown',
                                    f"High-risk content: {title[:100]}..."
                                ))
                                alerts_generated += 1
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error processing article from {source['name']}: {e}")
                        continue
                
                conn.commit()
            
            if articles_stored > 0:
                logger.info(f"✅ {source['name']}: {articles_stored} new articles, {alerts_generated} alerts")
            
            return {'articles': articles_stored, 'alerts': alerts_generated}
            
        except Exception as e:
            logger.error(f"❌ Error processing {source['name']}: {e}")
            self.stats['errors'] += 1
            return {'articles': 0, 'alerts': 0}
    
    def is_geopolitical(self, title: str, description: str) -> bool:
        """Check if content is geopolitically relevant."""
        text = f"{title} {description}".lower()
        
        geopolitical_keywords = {
            'war', 'conflict', 'crisis', 'election', 'government', 'military', 
            'diplomacy', 'sanctions', 'treaty', 'invasion', 'terrorism', 
            'security', 'defense', 'politics', 'international', 'global',
            'ukraine', 'russia', 'israel', 'palestine', 'gaza', 'syria',
            'china', 'taiwan', 'iran', 'nuclear', 'missile', 'nato',
            'economic crisis', 'trade war', 'summit', 'negotiations', 'ceasefire',
            'protest', 'revolution', 'coup', 'diplomatic', 'foreign policy',
            'eu', 'european union', 'united nations', 'un security council'
        }
        
        return any(keyword in text for keyword in geopolitical_keywords)
    
    def extract_region(self, title: str, description: str) -> str:
        """Extract primary geographical region."""
        text = f"{title} {description}".lower()
        
        region_patterns = {
            'Middle East': ['israel', 'palestine', 'syria', 'lebanon', 'jordan', 'gaza', 'west bank', 'iran', 'iraq', 'yemen'],
            'Eastern Europe': ['ukraine', 'belarus', 'moldova', 'poland', 'hungary', 'romania', 'bulgaria'],
            'Russia': ['russia', 'moscow', 'kremlin', 'putin', 'siberia', 'caucasus'],
            'Asia Pacific': ['china', 'taiwan', 'japan', 'korea', 'vietnam', 'thailand', 'philippines', 'indonesia'],
            'Africa': ['libya', 'sudan', 'ethiopia', 'congo', 'somalia', 'mali', 'nigeria', 'egypt'],
            'Latin America': ['venezuela', 'colombia', 'brazil', 'argentina', 'mexico', 'chile', 'cuba'],
            'South Asia': ['india', 'pakistan', 'afghanistan', 'bangladesh', 'sri lanka', 'nepal'],
            'North America': ['united states', 'canada', 'usa', 'america', 'washington'],
            'Western Europe': ['france', 'germany', 'italy', 'spain', 'uk', 'britain', 'netherlands', 'belgium'],
            'Central Asia': ['kazakhstan', 'uzbekistan', 'turkmenistan', 'kyrgyzstan', 'tajikistan'],
            'Southeast Asia': ['myanmar', 'malaysia', 'singapore', 'cambodia', 'laos'],
            'Balkans': ['serbia', 'bosnia', 'kosovo', 'macedonia', 'montenegro', 'albania']
        }
        
        for region, keywords in region_patterns.items():
            if any(keyword in text for keyword in keywords):
                return region
        
        return 'Global'
    
    def calculate_risk_level(self, title: str, description: str) -> str:
        """Calculate risk level."""
        text = f"{title} {description}".lower()
        
        high_risk_keywords = ['war', 'invasion', 'attack', 'bombing', 'crisis', 'emergency', 'nuclear', 'missile']
        medium_risk_keywords = ['conflict', 'tension', 'dispute', 'protest', 'sanctions', 'coup']
        
        if any(keyword in text for keyword in high_risk_keywords):
            return 'high'
        elif any(keyword in text for keyword in medium_risk_keywords):
            return 'medium'
        else:
            return 'low'
    
    def extract_image_url(self, entry: Dict[str, Any]) -> str:
        """Extract image URL from RSS entry."""
        # Try various image sources
        image_url = ''
        
        # Check for media content
        if 'media_content' in entry and entry['media_content']:
            image_url = entry['media_content'][0].get('url', '')
        
        # Check for enclosures
        elif 'enclosures' in entry and entry['enclosures']:
            for enclosure in entry['enclosures']:
                if hasattr(enclosure, 'type') and enclosure.type.startswith('image'):
                    image_url = enclosure.href
                    break
        
        # Check summary for images
        if not image_url and 'summary' in entry:
            import re
            img_match = re.search(r'<img[^>]+src="([^"]+)"', str(entry['summary']))
            if img_match:
                image_url = img_match.group(1)
        
        return image_url
    
    def run_massive_ingestion(self) -> Dict[str, Any]:
        """Execute massive parallel ingestion."""
        start_time = time.time()
        
        logger.info("🚀 STARTING MASSIVE NEWS INGESTION")
        logger.info(f"📊 Processing {len(self.rss_sources)} real RSS sources")
        
        total_articles = 0
        total_alerts = 0
        
        # Process sources in parallel batches
        batch_size = 10
        
        for i in range(0, len(self.rss_sources), batch_size):
            batch = self.rss_sources[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"🔄 Processing batch {batch_num}/{(len(self.rss_sources) + batch_size - 1) // batch_size}")
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_source = {
                    executor.submit(self.process_rss_feed, source): source 
                    for source in batch
                }
                
                for future in as_completed(future_to_source):
                    try:
                        result = future.result(timeout=60)
                        total_articles += result['articles']
                        total_alerts += result['alerts']
                        self.stats['sources_processed'] += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Batch processing error: {e}")
                        self.stats['errors'] += 1
            
            # Brief pause between batches
            time.sleep(3)
        
        processing_time = time.time() - start_time
        
        # Update final stats
        self.stats.update({
            'total_articles': total_articles,
            'new_articles': total_articles,
            'alerts_generated': total_alerts,
            'processing_time': processing_time
        })
        
        # Log final results
        logger.info("="*60)
        logger.info("📊 MASSIVE INGESTION COMPLETED")
        logger.info("="*60)
        logger.info(f"📰 New articles ingested: {total_articles}")
        logger.info(f"🚨 Critical alerts generated: {total_alerts}")
        logger.info(f"📡 Sources processed: {self.stats['sources_processed']}")
        logger.info(f"🌍 Regions detected: {len(self.stats['regions_detected'])}")
        logger.info(f"⏱️  Processing time: {processing_time:.1f} seconds")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("="*60)
        
        # Show regions detected
        if self.stats['regions_detected']:
            regions_list = list(self.stats['regions_detected'])[:15]
            logger.info(f"🗺️  Regions covered: {', '.join(regions_list)}")
        
        return self.stats
    
    def get_current_database_stats(self) -> Dict[str, int]:
        """Get current database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count total geopolitical articles
                cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE geopolitical_relevance = 1")
                total_articles = cursor.fetchone()[0]
                
                # Count critical alerts
                cursor = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity = 'critical'")
                critical_alerts = cursor.fetchone()[0]
                
                # Count unique regions
                cursor = conn.execute("SELECT COUNT(DISTINCT region) FROM articles WHERE region IS NOT NULL AND region != ''")
                unique_regions = cursor.fetchone()[0]
                
                # Count articles from last 24 hours
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE geopolitical_relevance = 1 
                    AND created_at >= datetime('now', '-24 hours')
                """)
                recent_articles = cursor.fetchone()[0]
                
                return {
                    'total_geopolitical_articles': total_articles,
                    'critical_alerts': critical_alerts,
                    'unique_regions': unique_regions,
                    'recent_articles_24h': recent_articles
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {'total_geopolitical_articles': 0, 'critical_alerts': 0, 'unique_regions': 0, 'recent_articles_24h': 0}


def main():
    """Main execution."""
    system = MassiveNewsIngestion()
    
    # Show initial stats
    initial_stats = system.get_current_database_stats()
    logger.info(f"📊 INITIAL STATS: {initial_stats}")
    
    # Run massive ingestion
    results = system.run_massive_ingestion()
    
    # Show final stats
    final_stats = system.get_current_database_stats()
    logger.info(f"📊 FINAL STATS: {final_stats}")
    
    # Show improvement
    improvement = {
        'articles_added': final_stats['total_geopolitical_articles'] - initial_stats['total_geopolitical_articles'],
        'alerts_added': final_stats['critical_alerts'] - initial_stats['critical_alerts'],
        'regions_added': final_stats['unique_regions'] - initial_stats['unique_regions']
    }
    
    logger.info("="*60)
    logger.info("📈 IMPROVEMENT SUMMARY")
    logger.info("="*60)
    logger.info(f"📰 Articles added: {improvement['articles_added']}")
    logger.info(f"🚨 Alerts added: {improvement['alerts_added']}")
    logger.info(f"🌍 New regions: {improvement['regions_added']}")
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    main()