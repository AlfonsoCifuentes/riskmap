#!/usr/bin/env python3
"""
Enhanced News Ingestion System
Ejecuta múltiples fuentes de datos en paralelo para aumentar significativamente 
el número de artículos geopolíticos analizados, regiones detectadas y alertas generadas.

SOLO DATOS REALES - NO MOCKUPS
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from src.data_ingestion.global_news_collector import GlobalNewsSourcesRegistry
    from src.data_ingestion.enhanced_global_news_collector import ConflictZoneNewsRegistry  
    from src.data_ingestion.intelligence_sources import IntelligenceCollector
    from src.data_ingestion.news_collector import NewsCollector
    from src.intelligence.external_feeds import ExternalIntelligenceFeeds
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)


class EnhancedNewsIngestionSystem:
    """Sistema mejorado de ingesta de noticias que ejecuta múltiples fuentes en paralelo."""
    
    def __init__(self):
        self.db_path = "./data/geopolitical_intel.db"
        self.global_sources = GlobalNewsSourcesRegistry()
        self.conflict_sources = ConflictZoneNewsRegistry()
        self.news_collector = NewsCollector()
        self.external_feeds = ExternalIntelligenceFeeds()
        
        # Stats tracking
        self.stats = {
            'total_articles': 0,
            'new_articles': 0,
            'sources_processed': 0,
            'regions_detected': set(),
            'alerts_generated': 0,
            'processing_time': 0,
            'errors': 0
        }
        
        self.setup_database()
    
    def setup_database(self):
        """Ensure database tables exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        source TEXT NOT NULL,
                        description TEXT,
                        content TEXT,
                        published_date TEXT,
                        language TEXT,
                        country TEXT,
                        region TEXT,
                        image_url TEXT,
                        geopolitical_relevance INTEGER DEFAULT 0,
                        risk_level TEXT DEFAULT 'low',
                        tags TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS processed_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id INTEGER UNIQUE,
                        processed_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        geopolitical_score REAL,
                        region_extracted TEXT,
                        entities_detected TEXT,
                        risk_indicators TEXT,
                        alert_level TEXT DEFAULT 'none',
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                """)
                
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
    
    def get_all_rss_sources(self) -> List[Dict[str, Any]]:
        """Collect all RSS sources from multiple registries."""
        all_sources = []
        
        try:
            # Global sources
            for lang, regions in self.global_sources.sources.items():
                for region, sources in regions.items():
                    for source in sources:
                        all_sources.append({
                            **source,
                            'language': lang,
                            'region': region,
                            'priority': source.get('priority', 'medium'),
                            'source_type': 'global'
                        })
            
            # Conflict zone sources (higher priority)
            for lang, regions in self.conflict_sources.sources.items():
                for region, sources in regions.items():
                    for source in sources:
                        all_sources.append({
                            **source,
                            'language': lang,
                            'region': region,
                            'priority': source.get('priority', 'high'),
                            'source_type': 'conflict_zone'
                        })
            
            # Sort by priority (critical -> high -> medium)
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            all_sources.sort(key=lambda x: priority_order.get(x.get('priority', 'medium'), 2))
            
            logger.info(f"📊 Collected {len(all_sources)} RSS sources across all registries")
            return all_sources
            
        except Exception as e:
            logger.error(f"❌ Error collecting RSS sources: {e}")
            return []
    
    def process_source_batch(self, sources_batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process a batch of RSS sources in parallel."""
        results = {'articles': 0, 'errors': 0, 'regions': set()}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {
                executor.submit(self.process_single_source, source): source 
                for source in sources_batch
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    source_result = future.result(timeout=60)
                    results['articles'] += source_result.get('articles', 0)
                    if source_result.get('region'):
                        results['regions'].add(source_result['region'])
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error processing {source.get('name', 'Unknown')}: {e}")
                    results['errors'] += 1
        
        return results
    
    def process_single_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single RSS source."""
        try:
            articles = self.news_collector.collect_from_rss(source['rss'])
            
            if not articles:
                return {'articles': 0, 'region': None}
            
            # Filter for geopolitical content
            geopolitical_articles = self.filter_geopolitical_content(articles)
            
            if geopolitical_articles:
                # Store articles in database
                stored_count = self.store_articles(geopolitical_articles, source)
                
                # Extract regions
                regions_found = self.extract_regions(geopolitical_articles)
                
                logger.info(
                    f"✅ {source.get('name', 'Unknown')}: "
                    f"{stored_count} articles, regions: {list(regions_found)[:3]}..."
                )
                
                return {
                    'articles': stored_count,
                    'region': source.get('region'),
                    'regions_found': regions_found
                }
            
            return {'articles': 0, 'region': None}
            
        except Exception as e:
            logger.error(f"❌ Error processing source {source.get('name')}: {e}")
            return {'articles': 0, 'region': None}
    
    def filter_geopolitical_content(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter articles for geopolitical relevance."""
        geopolitical_keywords = {
            'conflict', 'war', 'crisis', 'election', 'government', 'military', 
            'diplomacy', 'sanctions', 'treaty', 'invasion', 'terrorism', 
            'security', 'defense', 'politics', 'international', 'global',
            'ukraine', 'russia', 'israel', 'palestine', 'gaza', 'syria',
            'china', 'taiwan', 'iran', 'nuclear', 'missile', 'nato',
            'economic', 'trade', 'summit', 'negotiations', 'ceasefire'
        }
        
        filtered_articles = []
        for article in articles:
            title_lower = article.get('title', '').lower()
            description_lower = article.get('description', '').lower()
            
            # Check for geopolitical relevance
            is_geopolitical = any(
                keyword in title_lower or keyword in description_lower 
                for keyword in geopolitical_keywords
            )
            
            if is_geopolitical:
                article['geopolitical_relevance'] = 1
                filtered_articles.append(article)
        
        return filtered_articles
    
    def extract_regions(self, articles: List[Dict[str, Any]]) -> set:
        """Extract geographical regions from articles."""
        regions = set()
        
        region_patterns = {
            'Middle East': ['israel', 'palestine', 'syria', 'lebanon', 'jordan', 'gaza', 'west bank'],
            'Eastern Europe': ['ukraine', 'belarus', 'moldova', 'poland', 'hungary'],
            'Russia': ['russia', 'moscow', 'kremlin', 'putin'],
            'Asia Pacific': ['china', 'taiwan', 'japan', 'korea', 'vietnam', 'thailand'],
            'Africa': ['libya', 'sudan', 'ethiopia', 'congo', 'somalia', 'mali'],
            'Latin America': ['venezuela', 'colombia', 'brazil', 'argentina', 'mexico'],
            'South Asia': ['india', 'pakistan', 'afghanistan', 'bangladesh', 'sri lanka'],
            'North America': ['united states', 'canada', 'usa', 'america'],
            'Western Europe': ['france', 'germany', 'italy', 'spain', 'uk', 'britain']
        }
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            for region, keywords in region_patterns.items():
                if any(keyword in text for keyword in keywords):
                    regions.add(region)
        
        return regions
    
    def store_articles(self, articles: List[Dict[str, Any]], source: Dict[str, Any]) -> int:
        """Store articles in the database."""
        stored_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for article in articles:
                    try:
                        # Extract region from article content
                        regions_found = self.extract_regions([article])
                        primary_region = list(regions_found)[0] if regions_found else None
                        
                        conn.execute("""
                            INSERT OR IGNORE INTO articles 
                            (title, url, source, description, content, published_date, 
                             language, country, region, image_url, geopolitical_relevance,
                             risk_level, tags)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            article.get('title', ''),
                            article.get('url', ''),
                            source.get('name', ''),
                            article.get('description', ''),
                            article.get('content', ''),
                            article.get('published_date', ''),
                            source.get('language', 'unknown'),
                            source.get('country', 'unknown'),
                            primary_region,
                            article.get('image_url', ''),
                            article.get('geopolitical_relevance', 1),
                            self.calculate_risk_level(article),
                            ','.join(article.get('tags', []))
                        ))
                        
                        # Check if it was actually inserted (not a duplicate)
                        if conn.total_changes > 0:
                            stored_count += 1
                            
                            # Generate alert if high risk
                            if self.should_generate_alert(article, source):
                                self.generate_alert(conn, article, source)
                        
                    except sqlite3.IntegrityError:
                        # Duplicate URL, skip
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️  Error storing article: {e}")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Database storage error: {e}")
        
        return stored_count
    
    def calculate_risk_level(self, article: Dict[str, Any]) -> str:
        """Calculate risk level for an article."""
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        text = f"{title} {description}"
        
        high_risk_keywords = ['war', 'invasion', 'attack', 'bombing', 'crisis', 'emergency']
        medium_risk_keywords = ['conflict', 'tension', 'dispute', 'protest', 'sanctions']
        
        if any(keyword in text for keyword in high_risk_keywords):
            return 'high'
        elif any(keyword in text for keyword in medium_risk_keywords):
            return 'medium'
        else:
            return 'low'
    
    def should_generate_alert(self, article: Dict[str, Any], source: Dict[str, Any]) -> bool:
        """Determine if an alert should be generated."""
        risk_level = self.calculate_risk_level(article)
        priority = source.get('priority', 'medium')
        
        # Generate alerts for high-risk content from critical/high priority sources
        return risk_level == 'high' and priority in ['critical', 'high']
    
    def generate_alert(self, conn, article: Dict[str, Any], source: Dict[str, Any]):
        """Generate an alert for high-risk content."""
        try:
            # Get article ID
            cursor = conn.execute("SELECT id FROM articles WHERE url = ?", (article.get('url'),))
            article_row = cursor.fetchone()
            
            if article_row:
                article_id = article_row[0]
                
                # Extract region
                regions_found = self.extract_regions([article])
                primary_region = list(regions_found)[0] if regions_found else 'Unknown'
                
                conn.execute("""
                    INSERT INTO alerts (article_id, alert_type, severity, region, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    article_id,
                    'geopolitical_risk',
                    'critical',
                    primary_region,
                    f"High-risk geopolitical content detected: {article.get('title', '')[:100]}..."
                ))
                
                self.stats['alerts_generated'] += 1
                
        except Exception as e:
            logger.warning(f"⚠️  Error generating alert: {e}")
    
    def run_enhanced_ingestion(self, max_sources: int = 200) -> Dict[str, Any]:
        """Execute enhanced news ingestion from multiple sources."""
        start_time = time.time()
        
        logger.info("🚀 Starting Enhanced News Ingestion System")
        logger.info(f"⏱️  Target: Process up to {max_sources} sources for maximum coverage")
        
        # Get all RSS sources
        all_sources = self.get_all_rss_sources()
        
        # Limit sources to avoid overwhelming the system
        sources_to_process = all_sources[:max_sources]
        
        logger.info(f"📊 Processing {len(sources_to_process)} high-priority sources")
        
        # Process sources in batches
        batch_size = 20
        total_articles = 0
        total_errors = 0
        all_regions = set()
        
        for i in range(0, len(sources_to_process), batch_size):
            batch = sources_to_process[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"🔄 Processing batch {batch_num}/{(len(sources_to_process) + batch_size - 1) // batch_size}")
            
            batch_results = self.process_source_batch(batch)
            
            total_articles += batch_results['articles']
            total_errors += batch_results['errors'] 
            all_regions.update(batch_results['regions'])
            
            # Brief pause between batches
            time.sleep(2)
        
        processing_time = time.time() - start_time
        
        # Update stats
        self.stats.update({
            'total_articles': total_articles,
            'new_articles': total_articles,  # Assume most are new
            'sources_processed': len(sources_to_process),
            'regions_detected': all_regions,
            'processing_time': processing_time,
            'errors': total_errors
        })
        
        # Final statistics
        logger.info("="*60)
        logger.info("📊 ENHANCED INGESTION COMPLETED")
        logger.info("="*60)
        logger.info(f"📰 Articles processed: {self.stats['total_articles']}")
        logger.info(f"🆕 New articles: {self.stats['new_articles']}")
        logger.info(f"📡 Sources processed: {self.stats['sources_processed']}")
        logger.info(f"🌍 Regions detected: {len(self.stats['regions_detected'])}")
        logger.info(f"🚨 Alerts generated: {self.stats['alerts_generated']}")
        logger.info(f"⏱️  Processing time: {processing_time:.1f} seconds")
        logger.info(f"❌ Errors encountered: {self.stats['errors']}")
        logger.info("="*60)
        
        # Show sample regions detected
        if self.stats['regions_detected']:
            regions_list = list(self.stats['regions_detected'])[:10]
            logger.info(f"🗺️  Sample regions: {', '.join(regions_list)}")
        
        return self.stats
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count total articles
                cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE geopolitical_relevance = 1")
                total_articles = cursor.fetchone()[0]
                
                # Count alerts
                cursor = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity IN ('critical', 'high')")
                critical_alerts = cursor.fetchone()[0]
                
                # Count unique regions
                cursor = conn.execute("SELECT COUNT(DISTINCT region) FROM articles WHERE region IS NOT NULL")
                unique_regions = cursor.fetchone()[0]
                
                return {
                    'total_geopolitical_articles': total_articles,
                    'critical_alerts': critical_alerts,
                    'unique_regions': unique_regions
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {'total_geopolitical_articles': 0, 'critical_alerts': 0, 'unique_regions': 0}


def main():
    """Main execution function."""
    system = EnhancedNewsIngestionSystem()
    
    # Show current stats
    current_stats = system.get_current_stats()
    logger.info(f"📊 Current database stats: {current_stats}")
    
    # Run enhanced ingestion
    results = system.run_enhanced_ingestion(max_sources=150)
    
    # Show updated stats
    updated_stats = system.get_current_stats()
    logger.info(f"📊 Updated database stats: {updated_stats}")
    
    return results


if __name__ == "__main__":
    main()