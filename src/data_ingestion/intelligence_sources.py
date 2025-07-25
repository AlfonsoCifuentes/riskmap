"""
Specialized intelligence sources collector for geopolitical analysis.
Focuses on think tanks, academic institutions, and intelligence analysis sources.
"""

from utils.config import config, DatabaseManager
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import logging
from pathlib import Path
import sys
import json
import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class IntelligenceSourcesRegistry:
    """Registry of specialized intelligence and analysis sources."""

    def __init__(self):
        self.sources = {'think_tanks': {'us': [{'name': 'Council on Foreign Relations',
                                                'rss': 'https://www.cfr.org/rss/feed',
                                                'category': 'foreign_policy',
                                                'country': 'US',
                                                'credibility': 'high',
                                                'focus': ['diplomacy',
                                                          'international_relations',
                                                          'security']},
                                               {'name': 'Brookings Institution',
                                                'rss': 'https://www.brookings.edu/feed/',
                                                'category': 'policy_analysis',
                                                'country': 'US',
                                                'credibility': 'high',
                                                'focus': ['policy',
                                                            'governance',
                                                            'economics']},
                                               {'name': 'Carnegie Endowment',
                                                'rss': 'https://carnegieendowment.org/rss/rss.xml',
                                                'category': 'international_affairs',
                                                'country': 'US',
                                                'credibility': 'high',
                                                'focus': ['democracy',
                                                          'nuclear_policy',
                                                          'regional_studies']},
                                               {'name': 'Center for Strategic and International Studies',
                                                'rss': 'https://www.csis.org/rss.xml',
                                                'category': 'strategic_analysis',
                                                'country': 'US',
                                                'credibility': 'high',
                                                'focus': ['defense',
                                                          'security',
                                                          'technology']},
                                               {'name': 'Atlantic Council',
                                                'rss': 'https://www.atlanticcouncil.org/feed/',
                                                'category': 'international_security',
                                                'country': 'US',
                                                'credibility': 'high',
                                                'focus': ['nato',
                                                          'transatlantic',
                                                          'emerging_threats']},
                                               {'name': 'Heritage Foundation',
                                                'rss': 'https://www.heritage.org/rss.xml',
                                                'category': 'conservative_policy',
                                                'country': 'US',
                                                'credibility': 'medium',
                                                'focus': ['defense',
                                                          'foreign_policy',
                                                          'economics']},
                                               {'name': 'Center for American Progress',
                                                'rss': 'https://www.americanprogress.org/feed/',
                                                'category': 'progressive_policy',
                                                'country': 'US',
                                                'credibility': 'medium',
                                                'focus': ['climate',
                                                          'democracy',
                                                          'immigration']}],
                                        'uk': [{'name': 'Chatham House',
                                                'rss': 'https://www.chathamhouse.org/rss/all',
                                                'category': 'international_affairs',
                                                'country': 'GB',
                                                'credibility': 'high',
                                                'focus': ['global_governance',
                                                          'conflict',
                                                          'sustainability']},
                                               {'name': 'International Institute for Strategic Studies',
                                                'rss': 'https://www.iiss.org/rss',
                                                'category': 'strategic_studies',
                                                'country': 'GB',
                                                'credibility': 'high',
                                                'focus': ['defense',
                                                          'security',
                                                          'geopolitics']},
                                               {'name': 'Oxford Analytica',
                                                'rss': 'https://www.oxan.com/rss/',
                                                'category': 'country_analysis',
                                                'country': 'GB',
                                                'credibility': 'high',
                                                'focus': ['political_risk',
                                                          'economics',
                                                          'forecasting']}],
                                        'europe': [{'name': 'European Council on Foreign Relations',
                                                    'rss': 'https://ecfr.eu/feed/',
                                                    'category': 'european_policy',
                                                    'country': 'EU',
                                                    'credibility': 'high',
                                                    'focus': ['eu_policy',
                                                              'european_security',
                                                              'multilateralism']},
                                                   {'name': 'German Marshall Fund',
                                                    'rss': 'https://www.gmfus.org/feed',
                                                    'category': 'transatlantic',
                                                    'country': 'DE',
                                                    'credibility': 'high',
                                                    'focus': ['transatlantic_relations',
                                                              'democracy',
                                                              'security']},
                                                   {'name': 'French Institute of International Relations',
                                                    'rss': 'https://www.ifri.org/en/rss.xml',
                                                    'category': 'international_relations',
                                                    'country': 'FR',
                                                    'credibility': 'high',
                                                    'focus': ['european_integration',
                                                              'africa',
                                                              'middle_east']},
                                                   {'name': 'Stockholm International Peace Research Institute',
                                                    'rss': 'https://www.sipri.org/rss.xml',
                                                    'category': 'peace_research',
                                                    'country': 'SE',
                                                    'credibility': 'high',
                                                    'focus': ['arms_control',
                                                              'conflict',
                                                              'security']}],
                                        'asia': [{'name': 'East-West Center',
                                                  'rss': 'https://www.eastwestcenter.org/rss.xml',
                                                  'category': 'asia_pacific',
                                                  'country': 'US',
                                                  'credibility': 'high',
                                                  'focus': ['asia_pacific',
                                                            'regional_cooperation',
                                                            'development']},
                                                 {'name': 'Observer Research Foundation',
                                                  'rss': 'https://www.orfonline.org/feed/',
                                                  'category': 'indian_perspective',
                                                  'country': 'IN',
                                                  'credibility': 'medium',
                                                  'focus': ['south_asia',
                                                            'strategic_studies',
                                                            'economics']},
                                                 {'name': 'Lowy Institute',
                                                  'rss': 'https://www.lowyinstitute.org/rss.xml',
                                                  'category': 'indo_pacific',
                                                  'country': 'AU',
                                                  'credibility': 'high',
                                                  'focus': ['indo_pacific',
                                                            'australia_relations',
                                                            'regional_security']}]},
                        'academic_institutions': [{'name': 'Harvard Kennedy School - Belfer Center',
                                                   'rss': 'https://www.belfercenter.org/rss.xml',
                                                   'category': 'academic_research',
                                                   'country': 'US',
                                                   'credibility': 'high',
                                                   'focus': ['science_policy',
                                                             'international_security',
                                                             'diplomacy']},
                                                  {'name': 'Stanford Freeman Spogli Institute',
                                                   'rss': 'https://fsi.stanford.edu/rss.xml',
                                                   'category': 'academic_research',
                                                   'country': 'US',
                                                   'credibility': 'high',
                                                   'focus': ['international_studies',
                                                             'democracy',
                                                             'development']},
                                                  {'name': 'London School of Economics - IDEAS',
                                                   'rss': 'https://blogs.lse.ac.uk/ideas/feed/',
                                                   'category': 'academic_analysis',
                                                   'country': 'GB',
                                                   'credibility': 'high',
                                                   'focus': ['international_affairs',
                                                             'diplomacy',
                                                             'strategy']}],
                        'government_sources': [{'name': 'US State Department',
                                                'rss': 'https://www.state.gov/rss/',
                                                'category': 'official_statements',
                                                'country': 'US',
                                                'credibility': 'high',
                                                'focus': ['diplomatic_statements',
                                                          'policy_announcements']},
                                               {'name': 'European External Action Service',
                                                'rss': 'https://eeas.europa.eu/rss_en',
                                                'category': 'eu_diplomacy',
                                                'country': 'EU',
                                                'credibility': 'high',
                                                'focus': ['eu_foreign_policy',
                                                          'diplomatic_relations']},
                                               {'name': 'UK Foreign Office',
                                                'rss': 'https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=foreign-commonwealth-development-office',
                                                'category': 'official_statements',
                                                'country': 'GB',
                                                'credibility': 'high',
                                                'focus': ['uk_foreign_policy',
                                                          'diplomatic_announcements']}],
                        'specialized_media': [{'name': 'Foreign Policy Magazine',
                                               'rss': 'https://foreignpolicy.com/feed/',
                                               'category': 'specialized_journalism',
                                               'country': 'US',
                                               'credibility': 'high',
                                               'focus': ['international_affairs',
                                                         'geopolitics',
                                                         'analysis']},
                                              {'name': 'Foreign Affairs',
                                               'rss': 'https://www.foreignaffairs.com/rss.xml',
                                               'category': 'academic_journalism',
                                               'country': 'US',
                                               'credibility': 'high',
                                               'focus': ['international_relations',
                                                         'policy_analysis']},
                                              {'name': 'World Politics Review',
                                               'rss': 'https://www.worldpoliticsreview.com/rss/',
                                               'category': 'analysis',
                                               'country': 'US',
                                               'credibility': 'medium',
                                               'focus': ['global_affairs',
                                                         'regional_analysis']},
                                              {'name': 'The Diplomat',
                                               'rss': 'https://thediplomat.com/feed/',
                                               'category': 'asia_pacific_focus',
                                               'country': 'US',
                                               'credibility': 'medium',
                                               'focus': ['asia_pacific',
                                                         'regional_politics',
                                                         'security']},
                                              {'name': 'Al-Monitor',
                                               'rss': 'https://www.al-monitor.com/rss.xml',
                                               'category': 'middle_east_focus',
                                               'country': 'US',
                                               'credibility': 'medium',
                                               'focus': ['middle_east',
                                                         'regional_politics',
                                                         'security']}],
                        'intelligence_analysis': [{'name': 'Stratfor',
                                                   'rss': 'https://worldview.stratfor.com/rss.xml',
                                                   'category': 'geopolitical_intelligence',
                                                   'country': 'US',
                                                   'credibility': 'medium',
                                                   'focus': ['geopolitical_forecasting',
                                                             'security_analysis']},
                                                  {'name': 'Jane\'s Intelligence',
                                                   'rss': 'https://www.janes.com/feeds/news.rss',
                                                   'category': 'defense_intelligence',
                                                   'country': 'GB',
                                                   'credibility': 'high',
                                                   'focus': ['defense',
                                                             'security',
                                                             'military_analysis']},
                                                  {'name': 'Intelligence Online',
                                                   'rss': 'https://www.intelligenceonline.com/rss',
                                                   'category': 'intelligence_news',
                                                   'country': 'FR',
                                                   'credibility': 'medium',
                                                   'focus': ['intelligence_services',
                                                             'corporate_intelligence']}],
                        'economic_intelligence': [{'name': 'Peterson Institute for International Economics',
                                                   'rss': 'https://www.piie.com/rss.xml',
                                                   'category': 'economic_analysis',
                                                   'country': 'US',
                                                   'credibility': 'high',
                                                   'focus': ['international_economics',
                                                             'trade',
                                                             'monetary_policy']},
                                                  {'name': 'World Economic Forum',
                                                   'rss': 'https://www.weforum.org/rss',
                                                   'category': 'global_economics',
                                                   'country': 'CH',
                                                   'credibility': 'medium',
                                                   'focus': ['global_economy',
                                                             'public_private_cooperation']},
                                                  {'name': 'International Monetary Fund',
                                                   'rss': 'https://www.imf.org/en/News/RSS',
                                                   'category': 'international_finance',
                                                   'country': 'US',
                                                   'credibility': 'high',
                                                   'focus': ['monetary_policy',
                                                             'financial_stability',
                                                             'development']}]}

    def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all intelligence sources."""
        all_sources = []

        for category, sources_dict in self.sources.items():
            if isinstance(sources_dict, dict):
                for region, sources in sources_dict.items():
                    for source in sources:
                        source['source_category'] = category
                        source['region'] = region
                        all_sources.append(source)
            else:  # List format
                for source in sources_dict:
                    source['source_category'] = category
                    all_sources.append(source)

        return all_sources

    def get_sources_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get sources by category."""
        if category not in self.sources:
            return []

        sources = []
        category_data = self.sources[category]

        if isinstance(category_data, dict):
            for region, region_sources in category_data.items():
                for source in region_sources:
                    source['source_category'] = category
                    source['region'] = region
                    sources.append(source)
        else:
            for source in category_data:
                source['source_category'] = category
                sources.append(source)

        return sources

    def get_high_credibility_sources(self) -> List[Dict[str, Any]]:
        """Get only high credibility sources."""
        all_sources = self.get_all_sources()
        return [s for s in all_sources if s.get('credibility') == 'high']

    def get_sources_by_focus(self, focus_area: str) -> List[Dict[str, Any]]:
        """Get sources that focus on specific areas."""
        all_sources = self.get_all_sources()
        return [
            s for s in all_sources if any(
                focus_area.lower() in focus.lower() for focus in s.get(
                    'focus', []))]


class IntelligenceCollector:
    """Collector for specialized intelligence sources."""

    def __init__(self):
        self.sources_registry = IntelligenceSourcesRegistry()
        # Fixed: use config directly, not config.config
        self.db = DatabaseManager(config)
        self.request_timeout = 30
        self.request_delay = 1.0

    async def collect_intelligence_sources_async(
            self, categories: List[str] = None, max_articles_per_source: int = 10) -> List[Dict[str, Any]]:
        """Collect from intelligence sources asynchronously."""
        if categories is None:
            categories = [
                'think_tanks',
                'specialized_media',
                'intelligence_analysis']

        all_sources = []
        for category in categories:
            all_sources.extend(
                self.sources_registry.get_sources_by_category(category))

        # Filter to high credibility sources for quality
        high_credibility_sources = [
            s for s in all_sources if s.get('credibility') == 'high']

        all_articles = []

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
            tasks = []

            for source in high_credibility_sources:
                if 'rss' in source:
                    task = self._fetch_intelligence_rss_async(
                        session, source, max_articles_per_source)
                    tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Intelligence collection error: {result}")

        logger.info(
            f"Collected {len(all_articles)} intelligence articles from {len(high_credibility_sources)} sources")
        return all_articles

    async def _fetch_intelligence_rss_async(self,
                                            session: aiohttp.ClientSession,
                                            source: Dict[str,
                                                         Any],
                                            max_articles: int) -> List[Dict[str,
                                                                            Any]]:
        """Fetch articles from intelligence RSS source."""
        try:
            await asyncio.sleep(self.request_delay)

            async with session.get(source['rss']) as response:
                content = await response.text()

            feed = feedparser.parse(content)
            articles = []

            for entry in feed.entries[:max_articles]:
                article = self._process_intelligence_entry(entry, source)
                if article:
                    articles.append(article)

            logger.debug(
                f"Collected {len(articles)} intelligence articles from {source['name']}")
            return articles

        except Exception as e:
            logger.error(
                f"Error fetching intelligence RSS from {source['name']}: {e}")
            return []

    def _process_intelligence_entry(
            self, entry: Any, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process intelligence RSS entry with enhanced metadata."""
        try:
            # Extract published date
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime(
                    *entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6]).isoformat()

            # Extract content
            content = ''
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value if isinstance(
                    entry.content, list) else entry.content
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description

            # Enhanced metadata for intelligence sources
            intelligence_metadata = {
                'source_type': 'intelligence',
                'category': source.get('category', ''),
                'credibility': source.get('credibility', 'unknown'),
                'focus_areas': source.get('focus', []),
                'source_country': source.get('country', ''),
                'region': source.get('region', ''),
                'collection_method': 'intelligence_rss',
                'intelligence_value': self._assess_intelligence_value(entry, source)
            }

            article = {
                'title': getattr(entry, 'title', ''),
                'content': content,
                'description': getattr(entry, 'summary', ''),
                'url': getattr(entry, 'link', ''),
                'published_at': published_at or datetime.now().isoformat(),
                'source': {
                    'name': source['name'],
                    'type': 'intelligence',
                    'rss_url': source['rss']
                },
                'author': getattr(entry, 'author', ''),
                'language': 'en',  # Most intelligence sources are in English
                'metadata': intelligence_metadata,
                'collected_at': datetime.now().isoformat()
            }

            # Validate article
            if not article['title'] or not article['url']:
                return None

            return article

        except Exception as e:
            logger.error(f"Error processing intelligence RSS entry: {e}")
            return None

    def _assess_intelligence_value(
            self, entry: Any, source: Dict[str, Any]) -> str:
        """Assess the intelligence value of an article."""
        # Simple heuristic based on source credibility and content indicators
        title = getattr(entry, 'title', '').lower()
        content = getattr(entry, 'summary', '').lower()

        high_value_indicators = [
            'analysis', 'assessment', 'forecast', 'intelligence', 'briefing',
            'strategic', 'geopolitical', 'security', 'threat', 'risk'
        ]

        geopolitical_keywords = [
            'diplomatic', 'military', 'conflict', 'alliance', 'treaty',
            'sanctions', 'crisis', 'summit', 'negotiation', 'policy'
        ]

        # Count indicators
        high_value_count = sum(1 for indicator in high_value_indicators
                               if indicator in title or indicator in content)

        geo_count = sum(1 for keyword in geopolitical_keywords
                        if keyword in title or keyword in content)

        # Assess value
        credibility_score = {
            'high': 3,
            'medium': 2,
            'low': 1}.get(
            source.get(
                'credibility',
                'low'),
            1)
        content_score = min(high_value_count + geo_count, 5)

        total_score = credibility_score + content_score

        if total_score >= 6:
            return 'high'
        elif total_score >= 4:
            return 'medium'
        else:
            return 'low'

    def collect_daily_intelligence(self, focus_areas: List[str] = None) -> int:
        """Collect daily intelligence from specialized sources."""
        try:
            # Default focus areas
            if focus_areas is None:
                focus_areas = ['security', 'diplomacy', 'conflict', 'policy']

            # Get sources by focus areas
            relevant_sources = []
            for focus_area in focus_areas:
                relevant_sources.extend(
                    self.sources_registry.get_sources_by_focus(focus_area)
                )

            # Remove duplicates
            unique_sources = []
            seen_urls = set()
            for source in relevant_sources:
                if source['rss'] not in seen_urls:
                    unique_sources.append(source)
                    seen_urls.add(source['rss'])

            # Collect articles asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                articles = loop.run_until_complete(
                    self.collect_intelligence_sources_async(
                        categories=[
                            'think_tanks',
                            'specialized_media',
                            'intelligence_analysis'],
                        max_articles_per_source=5))
            finally:
                loop.close()

            # Save to database with intelligence metadata
            saved_count = self._save_intelligence_articles(articles)

            logger.info(f"Collected {saved_count} intelligence articles")
            return saved_count

        except Exception as e:
            logger.error(f"Error in daily intelligence collection: {e}")
            return 0

    def _save_intelligence_articles(
            self, articles: List[Dict[str, Any]]) -> int:
        """Save intelligence articles to database with enhanced metadata."""
        if not articles:
            return 0

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            saved_count = 0

            for article in articles:
                try:
                    # Enhanced metadata for intelligence articles
                    metadata = article.get('metadata', {})
                    metadata.update({
                        'article_type': 'intelligence',
                        'collection_timestamp': datetime.now().isoformat(),
                        'processing_priority': 'high'  # Intelligence articles get priority processing
                    })

                    article_data = (
                        article.get('title', ''),
                        article.get('content', ''),
                        article.get('url', ''),
                        article.get('published_at'),
                        json.dumps(article.get('source', {})),
                        article.get('language', 'en'),
                        article.get('author', ''),
                        article.get('description', ''),
                        json.dumps(metadata)
                    )

                    cursor.execute("""
                        INSERT INTO articles
                        (title, content, url, published_at, source, language, author, description, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, article_data)

                    saved_count += 1

                except Exception as e:
                    logger.error(f"Error saving intelligence article: {e}")
                    continue

            conn.commit()
            conn.close()

            return saved_count

        except Exception as e:
            logger.error(
                f"Error saving intelligence articles to database: {e}")
            return 0

    def collect_from_sources(self, sources: List[Dict[str, Any]], max_articles_per_source: int = 10) -> List[Dict[str, Any]]:
        """Collect articles from a list of intelligence sources."""
        try:
            # Run async collection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                articles = loop.run_until_complete(
                    self._collect_from_sources_async(sources, max_articles_per_source)
                )
            finally:
                loop.close()
            
            return articles
            
        except Exception as e:
            logger.error(f"Error collecting from intelligence sources: {e}")
            return []
    
    async def _collect_from_sources_async(self, sources: List[Dict[str, Any]], max_articles_per_source: int) -> List[Dict[str, Any]]:
        """Async helper to collect from specific sources."""
        all_articles = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
            tasks = []
            
            for source in sources:
                if 'rss' in source:
                    task = self._fetch_intelligence_rss_async(
                        session, source, max_articles_per_source)
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Intelligence collection error: {result}")
        
        return all_articles
    
    def collect_all_sources(self, max_articles_per_source: int = 10) -> List[Dict[str, Any]]:
        """Collect from all available intelligence sources."""
        try:
            all_sources = self.sources_registry.get_all_sources()
            return self.collect_from_sources(all_sources, max_articles_per_source)
        except Exception as e:
            logger.error(f"Error collecting all intelligence sources: {e}")
            return []

    def get_intelligence_statistics(self) -> Dict[str, Any]:
        """Get statistics about collected intelligence articles."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Intelligence articles count
            cursor.execute("""
                SELECT COUNT(*) FROM articles
                WHERE JSON_EXTRACT(metadata, '$.article_type') = 'intelligence'
            """)
            intelligence_count = cursor.fetchone()[0]

            # By credibility level
            cursor.execute("""
                SELECT
                    JSON_EXTRACT(metadata, '$.credibility') as credibility,
                    COUNT(*)
                FROM articles
                WHERE JSON_EXTRACT(metadata, '$.article_type') = 'intelligence'
                GROUP BY credibility
            """)
            by_credibility = dict(cursor.fetchall())

            # By source category
            cursor.execute("""
                SELECT
                    JSON_EXTRACT(metadata, '$.category') as category,
                    COUNT(*)
                FROM articles
                WHERE JSON_EXTRACT(metadata, '$.article_type') = 'intelligence'
                GROUP BY category
            """)
            by_category = dict(cursor.fetchall())

            # Recent intelligence (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM articles
                WHERE JSON_EXTRACT(metadata, '$.article_type') = 'intelligence'
                AND created_at > datetime('now', '-24 hours')
            """)
            recent_count = cursor.fetchone()[0]

            conn.close()

            return {
                'total_intelligence_articles': intelligence_count,
                'by_credibility': by_credibility,
                'by_category': by_category,
                'recent_24h': recent_count,
                'total_sources': len(
                    self.sources_registry.get_all_sources()),
                'high_credibility_sources': len(
                    self.sources_registry.get_high_credibility_sources())}

        except Exception as e:
            logger.error(f"Error getting intelligence statistics: {e}")
            return {}


# Singleton instances - commented to avoid initialization issues at import time
# intelligence_sources_registry = IntelligenceSourcesRegistry()
# intelligence_collector = IntelligenceCollector()
