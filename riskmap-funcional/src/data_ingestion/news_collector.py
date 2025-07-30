"""
News collection module for gathering articles from multiple sources.
Supports multilingual collection (Spanish, English, Russian, Chinese, Arabic).
"""

from src.utils.config import config, db_manager as DatabaseManager
import requests
import feedparser
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class NewsAPICollector:
    """Collector for NewsAPI.org service."""

    def __init__(self):
        self.api_key = config.get_newsapi_key()
        self.base_url = config.get(
            'data_sources.newsapi.base_url',
            'https://newsapi.org/v2')
        self.supported_languages = config.get_supported_languages()
        self.db = DatabaseManager

        if not self.api_key:
            logger.warning(
                "NewsAPI key not configured. Some features may not work.")

    def collect_headlines(self,
                          language: str = 'en',
                          category: str = None,
                          country: str = None,
                          max_articles: int = 100) -> List[Dict[str,
                                                                Any]]:
        """Collect top headlines from NewsAPI."""
        if not self.api_key:
            logger.error("NewsAPI key not available")
            return []

        url = f"{self.base_url}/top-headlines"
        params = {
            'apiKey': self.api_key,
            'language': language,
            'pageSize': min(max_articles, 100)
        }

        if category:
            params['category'] = category
        if country:
            params['country'] = country

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            articles = data.get('articles', [])

            logger.info(
                f"Collected {len(articles)} headlines for language {language}")
            formatted_articles = self._format_articles(articles, language)

            # Save articles automatically
            if formatted_articles:
                self._save_articles(formatted_articles)

            return formatted_articles

        except requests.RequestException as e:
            logger.error(f"Error collecting headlines: {e}")
            return []

    def search_everything(self,
                          query: str,
                          language: str = 'en',
                          from_date: str = None,
                          max_articles: int = 100) -> List[Dict[str,
                                                                Any]]:
        """Search everything endpoint for specific queries."""
        if not self.api_key:
            logger.error("NewsAPI key not available")
            return []

        url = f"{self.base_url}/everything"
        params = {
            'apiKey': self.api_key,
            'q': query,
            'language': language,
            'pageSize': min(max_articles, 100),
            'sortBy': 'publishedAt'
        }

        if from_date:
            params['from'] = from_date

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            articles = data.get('articles', [])

            logger.info(
                f"Found {len(articles)} articles for query '{query}' in {language}")
            formatted_articles = self._format_articles(articles, language)

            # Save articles automatically
            if formatted_articles:
                self._save_articles(formatted_articles)

            return formatted_articles

        except requests.RequestException as e:
            logger.error(f"Error searching articles: {e}")
            return []

    def _format_articles(
            self, articles: List[Dict], language: str) -> List[Dict[str, Any]]:
        """Format articles from NewsAPI response."""
        formatted_articles = []

        for article in articles:
            formatted_article = {
                'title': article.get('title', ''),
                'content': article.get('content', '') or article.get('description', '') or '',
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'published_at': self._parse_date(article.get('publishedAt')),
                'language': language,
                'author': article.get('author', ''),
                'image_url': article.get('urlToImage', '')
            }

            # Filter out articles with insufficient content
            content = formatted_article.get('content', '') or ''
            if len(content) > 50:
                formatted_articles.append(formatted_article)

        return formatted_articles

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse ISO date string to datetime object."""
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return None

    def _save_articles(self, articles: List[Dict[str, Any]]):
        """Save articles to database."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        saved_count = 0
        for article in articles:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO articles
                    (title, content, url, source, published_at, language)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    article['title'],
                    article['content'],
                    article['url'],
                    article['source'],
                    article['published_at'],
                    article['language']
                ))

                if cursor.rowcount > 0:
                    saved_count += 1

            except sqlite3.Error as e:
                logger.error(f"Error saving article: {e}")

        conn.commit()
        conn.close()

        if saved_count > 0:
            logger.info(f"Saved {saved_count} new articles to database")


class RSSCollector:
    """Collector for RSS feeds from various news sources."""

    def __init__(self):
        self.sources = config.get('data_sources.manual_sources', [])
        self.db = DatabaseManager

    def collect_from_feed(self, feed_url: str,
                          language: str) -> List[Dict[str, Any]]:
        """Collect articles from a single RSS feed."""
        try:
            feed = feedparser.parse(feed_url)
            articles = []

            for entry in feed.entries:
                article = {
                    'title': entry.get(
                        'title', ''), 'content': entry.get(
                        'description', ''), 'url': entry.get(
                        'link', ''), 'source': feed.feed.get(
                        'title', 'RSS Feed'), 'published_at': self._parse_rss_date(
                        entry.get('published')), 'language': language}

                # Filter out articles with insufficient content
                if len(article['content']) > 50:
                    articles.append(article)

            logger.info(f"Collected {len(articles)} articles from RSS feed")
            return articles

        except Exception as e:
            logger.error(f"Error collecting from RSS feed {feed_url}: {e}")
            return []

    def collect_from_rss(self, rss_url: str, source_name: str, max_articles: int = 20) -> int:
        """Collect articles from RSS feed and save to database."""
        try:
            feed = feedparser.parse(rss_url)
            articles_saved = 0
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            for i, entry in enumerate(feed.entries[:max_articles]):
                try:
                    article = {
                        'title': entry.get('title', ''),
                        'content': entry.get('description', '') or entry.get('summary', ''),
                        'url': entry.get('link', ''),
                        'source': source_name,
                        'published_at': self._parse_rss_date(entry.get('published')),
                        'language': 'en'  # Default, should be passed as parameter
                    }
                    
                    # Skip if content is too short
                    if len(article['content']) < 50:
                        continue
                        
                    cursor.execute('''
                        INSERT OR IGNORE INTO articles
                        (title, content, url, source, published_at, language)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        article['title'],
                        article['content'],
                        article['url'],
                        article['source'],
                        article['published_at'],
                        article['language']
                    ))
                    
                    if cursor.rowcount > 0:
                        articles_saved += 1
                        
                except Exception as e:
                    logger.error(f"Error saving article from {source_name}: {e}")
                    continue
                    
            conn.commit()
            conn.close()
            
            return articles_saved
            
        except Exception as e:
            logger.error(f"Error collecting from RSS {rss_url}: {e}")
            return 0

    def collect_all_feeds(self) -> List[Dict[str, Any]]:
        """Collect articles from all configured RSS feeds."""
        all_articles = []

        for source in self.sources:
            articles = self.collect_from_feed(
                source.get('url', ''),
                source.get('language', 'en')
            )
            all_articles.extend(articles)
            time.sleep(1)  # Rate limiting

        return all_articles

    def _parse_rss_date(self, date_str: str) -> Optional[datetime]:
        """Parse RSS date string to datetime object."""
        if not date_str:
            return None

        # Common RSS date formats
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse RSS date: {date_str}")
        return None


class GeopoliticalNewsCollector:
    """High-level collector that orchestrates all news collection."""

    def __init__(self):
        self.newsapi = NewsAPICollector()
        self.rss = RSSCollector()

        # Keywords for geopolitical monitoring by language
        self.geopolitical_keywords = {
            'en': [
                'conflict',
                'war',
                'diplomacy',
                'sanctions',
                'protest',
                'crisis',
                'military',
                'government'],
            'es': [
                'conflicto',
                'guerra',
                'diplomacia',
                'sanciones',
                'protesta',
                'crisis',
                'militar',
                'gobierno'],
            'ru': [
                'конфликт',
                'война',
                'дипломатия',
                'санкции',
                'протест',
                'кризис',
                'военный',
                'правительство'],
            'zh': [
                '冲突',
                '战争',
                '外交',
                '制裁',
                '抗议',
                '危机',
                '军事',
                '政府'],
            'ar': [
                'صراع',
                'حرب',
                'دبلوماسية',
                'عقوبات',
                'احتجاج',
                'أزمة',
                'عسكري',
                'حكومة']}

    def collect_daily_news(self) -> int:
        """Collect daily news from all sources."""
        logger.info("Starting daily news collection")
        total_articles = 0

        # Collect from NewsAPI for each supported language
        for language in config.get_supported_languages():
            # Get general headlines
            headlines = self.newsapi.collect_headlines(
                language=language, max_articles=50)
            total_articles += len(headlines)

            # Search for specific geopolitical terms
            keywords = self.geopolitical_keywords.get(language, [])
            # Limit to 3 keywords per language to avoid API limits
            for keyword in keywords[:3]:
                articles = self.newsapi.search_everything(
                    query=keyword,
                    language=language,
                    from_date=(
                        datetime.now() -
                        timedelta(
                            days=1)).strftime('%Y-%m-%d'),
                    max_articles=20)
                total_articles += len(articles)

                # Respect API rate limits
                time.sleep(2)

        # Collect from RSS feeds
        rss_articles = self.rss.collect_all_feeds()
        total_articles += len(rss_articles)

        logger.info(f"Collected {total_articles} articles total")
        return total_articles


# Legacy compatibility
class GlobalNewsCollector(GeopoliticalNewsCollector):
    """Legacy alias for GeopoliticalNewsCollector."""
    pass
