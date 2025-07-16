"""
Intelligent source manager for automated discovery and management of news sources.
Includes source discovery, reliability assessment, and dynamic source management.
"""

import requests
import feedparser
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
import sys
import time
import re
from urllib.parse import urljoin, urlparse
import hashlib
from collections import defaultdict, Counter

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config, DatabaseManager

logger = logging.getLogger(__name__)


class IntelligentSourceManager:
    """Intelligent manager for news source discovery and optimization."""
    
    def __init__(self):
        self.db = DatabaseManager(config)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; NewsCollectorBot/1.0; +https://example.com/bot)'
        })
        
        # Source discovery patterns
        self.rss_patterns = [
            r'<link[^>]*type=["\']application/rss\+xml["\'][^>]*href=["\']([^"\']+)["\']',
            r'<link[^>]*href=["\']([^"\']*rss[^"\']*)["\']',
            r'<a[^>]*href=["\']([^"\']*rss[^"\']*)["\']',
            r'<a[^>]*href=["\']([^"\']*feed[^"\']*)["\']'
        ]
        
        # Quality indicators for source assessment
        self.quality_indicators = {
            'high_quality_domains': [
                'reuters.com', 'bbc.co.uk', 'theguardian.com', 'nytimes.com',
                'washingtonpost.com', 'ap.org', 'ft.com', 'economist.com'
            ],
            'academic_domains': [
                '.edu', '.ac.uk', '.ac.jp', 'harvard.edu', 'stanford.edu',
                'mit.edu', 'ox.ac.uk', 'cam.ac.uk'
            ],
            'government_domains': [
                '.gov', '.mil', '.europa.eu', '.un.org'
            ],
            'suspicious_indicators': [
                'blogspot.com', 'wordpress.com', 'tumblr.com',
                'click', 'viral', 'shocking', 'you-wont-believe'
            ]
        }
    
    def discover_sources_from_seed(self, seed_urls: List[str], 
                                 max_depth: int = 2) -> List[Dict[str, Any]]:
        """Discover RSS feeds from seed URLs using crawling."""
        discovered_sources = []
        visited_domains = set()
        
        for seed_url in seed_urls:
            try:
                logger.info(f"Discovering sources from seed: {seed_url}")
                domain_sources = self._crawl_for_rss(seed_url, max_depth, visited_domains)
                discovered_sources.extend(domain_sources)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error discovering from seed {seed_url}: {e}")
        
        # Remove duplicates and assess quality
        unique_sources = self._deduplicate_sources(discovered_sources)
        assessed_sources = [self._assess_source_quality(source) for source in unique_sources]
        
        logger.info(f"Discovered {len(assessed_sources)} unique sources from {len(seed_urls)} seeds")
        return assessed_sources
    
    def discover_regional_sources(self, country_code: str, language: str) -> List[Dict[str, Any]]:
        """Discover news sources for a specific country and language."""
        discovered_sources = []
        
        # Common news site patterns for different countries
        search_patterns = self._get_regional_search_patterns(country_code, language)
        
        for pattern in search_patterns:
            try:
                # Use search engines or directories to find news sites
                sources = self._search_regional_news_sites(pattern, country_code, language)
                discovered_sources.extend(sources)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in regional discovery for {country_code}: {e}")
        
        # Filter and assess discovered sources
        filtered_sources = self._filter_regional_sources(discovered_sources, country_code, language)
        assessed_sources = [self._assess_source_quality(source) for source in filtered_sources]
        
        logger.info(f"Discovered {len(assessed_sources)} regional sources for {country_code}/{language}")
        return assessed_sources
    
    def optimize_source_collection(self, hours: int = 168) -> Dict[str, Any]:
        """Optimize source collection based on performance data."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Get source performance data
            cursor.execute('''
                SELECT 
                    source_name,
                    source_url,
                    language,
                    COUNT(*) as attempts,
                    SUM(articles_collected) as total_articles,
                    AVG(articles_collected) as avg_articles,
                    AVG(success_rate) as success_rate,
                    AVG(duration_seconds) as avg_duration
                FROM collection_performance 
                WHERE timestamp > ?
                GROUP BY source_name, source_url, language
            ''', (since_time,))
            
            source_performance = []
            for row in cursor.fetchall():
                source_performance.append({
                    'name': row[0],
                    'url': row[1],
                    'language': row[2],
                    'attempts': row[3],
                    'total_articles': row[4],
                    'avg_articles': row[5],
                    'success_rate': row[6],
                    'avg_duration': row[7]
                })
            
            conn.close()
            
            # Categorize sources for optimization
            optimization_results = {
                'high_performers': [],
                'underperformers': [],
                'unreliable_sources': [],
                'slow_sources': [],
                'recommendations': []
            }
            
            for source in source_performance:
                # High performers: good success rate and article yield
                if source['success_rate'] > 0.8 and source['avg_articles'] > 5:
                    optimization_results['high_performers'].append(source)
                
                # Underperformers: low article yield but reliable
                elif source['success_rate'] > 0.6 and source['avg_articles'] < 2:
                    optimization_results['underperformers'].append(source)
                
                # Unreliable: poor success rate
                elif source['success_rate'] < 0.4:
                    optimization_results['unreliable_sources'].append(source)
                
                # Slow sources: long response times
                elif source['avg_duration'] > 30:
                    optimization_results['slow_sources'].append(source)
            
            # Generate optimization recommendations
            optimization_results['recommendations'] = self._generate_optimization_recommendations(
                optimization_results
            )
            
            logger.info(f"Source optimization analysis completed for {len(source_performance)} sources")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error in source optimization: {e}")
            return {}
    
    def auto_discover_trending_sources(self, language: str = 'en') -> List[Dict[str, Any]]:
        """Automatically discover trending news sources for a language."""
        discovered_sources = []
        
        # Search for trending news sources using various methods
        discovery_methods = [
            self._discover_from_news_aggregators,
            self._discover_from_social_media_trends,
            self._discover_from_domain_directories
        ]
        
        for method in discovery_methods:
            try:
                sources = method(language)
                discovered_sources.extend(sources)
                
                # Rate limiting between methods
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Error in trending source discovery method: {e}")
        
        # Filter and assess discovered sources
        unique_sources = self._deduplicate_sources(discovered_sources)
        assessed_sources = []
        
        for source in unique_sources:
            try:
                assessed_source = self._assess_source_quality(source)
                if assessed_source['quality_score'] > 0.5:  # Only include decent quality
                    assessed_sources.append(assessed_source)
            except Exception as e:
                logger.warning(f"Error assessing source {source.get('url', 'unknown')}: {e}")
        
        logger.info(f"Auto-discovered {len(assessed_sources)} trending sources for {language}")
        return assessed_sources
    
    def validate_existing_sources(self, source_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and update existing news sources."""
        validation_results = {
            'total_sources': len(source_list),
            'valid_sources': [],
            'invalid_sources': [],
            'updated_sources': [],
            'warnings': []
        }
        
        for source in source_list:
            try:
                validation_result = self._validate_single_source(source)
                
                if validation_result['status'] == 'valid':
                    validation_results['valid_sources'].append(validation_result)
                elif validation_result['status'] == 'invalid':
                    validation_results['invalid_sources'].append(validation_result)
                elif validation_result['status'] == 'updated':
                    validation_results['updated_sources'].append(validation_result)
                
                if validation_result.get('warnings'):
                    validation_results['warnings'].extend(validation_result['warnings'])
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error validating source {source.get('name', 'unknown')}: {e}")
                validation_results['invalid_sources'].append({
                    'source': source,
                    'error': str(e),
                    'status': 'error'
                })
        
        logger.info(f"Source validation completed: {len(validation_results['valid_sources'])} valid, "
                   f"{len(validation_results['invalid_sources'])} invalid")
        
        return validation_results
    
    def _crawl_for_rss(self, url: str, max_depth: int, visited_domains: Set[str]) -> List[Dict[str, Any]]:
        """Crawl a website for RSS feeds."""
        discovered_feeds = []
        
        try:
            domain = urlparse(url).netloc
            if domain in visited_domains:
                return discovered_feeds
            
            visited_domains.add(domain)
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Look for RSS links in the HTML
            html_content = response.text
            
            for pattern in self.rss_patterns:
                matches = re.finditer(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    rss_url = match.group(1)
                    if not rss_url.startswith('http'):
                        rss_url = urljoin(url, rss_url)
                    
                    # Validate the RSS feed
                    if self._is_valid_rss_feed(rss_url):
                        discovered_feeds.append({
                            'name': self._extract_site_name(url),
                            'rss_url': rss_url,
                            'source_url': url,
                            'domain': domain,
                            'discovered_from': 'crawl'
                        })
            
            # Look for common RSS paths
            common_rss_paths = ['/rss', '/feed', '/rss.xml', '/feed.xml', '/index.rss']
            for path in common_rss_paths:
                potential_rss = urljoin(url, path)
                if self._is_valid_rss_feed(potential_rss):
                    discovered_feeds.append({
                        'name': self._extract_site_name(url),
                        'rss_url': potential_rss,
                        'source_url': url,
                        'domain': domain,
                        'discovered_from': 'common_path'
                    })
            
        except Exception as e:
            logger.warning(f"Error crawling {url}: {e}")
        
        return discovered_feeds
    
    def _search_regional_news_sites(self, pattern: str, country_code: str, 
                                  language: str) -> List[Dict[str, Any]]:
        """Search for regional news sites using various methods."""
        sources = []
        
        # This would integrate with search APIs or directories
        # For now, we'll use a predefined list based on patterns
        regional_patterns = {
            'us': ['news', 'times', 'post', 'herald', 'tribune', 'gazette'],
            'uk': ['news', 'mail', 'telegraph', 'independent', 'standard'],
            'de': ['zeitung', 'nachrichten', 'tagblatt', 'presse'],
            'fr': ['nouvelles', 'journal', 'presse', 'quotidien'],
            'es': ['noticias', 'diario', 'periódico', 'prensa'],
            'it': ['notizie', 'giornale', 'quotidiano', 'corriere'],
            'ru': ['новости', 'газета', 'известия', 'правда'],
            'zh': ['新闻', '日报', '时报', '晚报'],
            'ar': ['أخبار', 'صحيفة', 'جريدة'],
            'ja': ['新聞', 'ニュース', '日報']
        }
        
        if country_code in regional_patterns:
            # This is a simplified version - in practice, you'd use search APIs
            # or web directories to find actual sites matching these patterns
            pass
        
        return sources
    
    def _discover_from_news_aggregators(self, language: str) -> List[Dict[str, Any]]:
        """Discover sources from news aggregator sites."""
        discovered_sources = []
        
        # Common news aggregators that list sources
        aggregators = {
            'en': ['https://news.google.com', 'https://www.allsides.com'],
            'es': ['https://news.google.com/topstories?hl=es'],
            'fr': ['https://news.google.com/topstories?hl=fr'],
            'de': ['https://news.google.com/topstories?hl=de']
        }
        
        if language in aggregators:
            for aggregator_url in aggregators[language]:
                try:
                    # This would parse aggregator pages to find source lists
                    # Implementation depends on specific aggregator structure
                    pass
                except Exception as e:
                    logger.warning(f"Error discovering from aggregator {aggregator_url}: {e}")
        
        return discovered_sources
    
    def _discover_from_social_media_trends(self, language: str) -> List[Dict[str, Any]]:
        """Discover trending news sources from social media."""
        # This would integrate with social media APIs to find trending news domains
        # For privacy and API limitations, this is a placeholder
        return []
    
    def _discover_from_domain_directories(self, language: str) -> List[Dict[str, Any]]:
        """Discover sources from web directories."""
        # This would query web directories for news sites by language/region
        # Implementation would depend on available directory APIs
        return []
    
    def _is_valid_rss_feed(self, url: str) -> bool:
        """Check if URL is a valid RSS feed."""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return False
            
            content = response.text.lower()
            return any(indicator in content for indicator in ['<rss', '<feed', '<channel'])
        except:
            return False
    
    def _assess_source_quality(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of a news source."""
        quality_assessment = source.copy()
        quality_score = 0.5  # Base score
        quality_factors = []
        
        url = source.get('rss_url', source.get('url', ''))
        domain = urlparse(url).netloc.lower()
        
        # Domain reputation assessment
        if any(hq_domain in domain for hq_domain in self.quality_indicators['high_quality_domains']):
            quality_score += 0.3
            quality_factors.append('high_quality_domain')
        
        if any(domain.endswith(suffix) for suffix in self.quality_indicators['academic_domains']):
            quality_score += 0.2
            quality_factors.append('academic_domain')
        
        if any(domain.endswith(suffix) for suffix in self.quality_indicators['government_domains']):
            quality_score += 0.15
            quality_factors.append('government_domain')
        
        # Suspicious indicators
        if any(indicator in domain for indicator in self.quality_indicators['suspicious_indicators']):
            quality_score -= 0.2
            quality_factors.append('suspicious_domain')
        
        # Check HTTPS
        if url.startswith('https://'):
            quality_score += 0.05
            quality_factors.append('secure_connection')
        
        # Test feed accessibility and content
        try:
            feed_data = feedparser.parse(url)
            if feed_data.entries:
                quality_score += 0.1
                quality_factors.append('active_feed')
                
                # Check for recent content
                if feed_data.entries:
                    latest_entry = feed_data.entries[0]
                    if hasattr(latest_entry, 'published_parsed'):
                        pub_time = datetime(*latest_entry.published_parsed[:6])
                        if (datetime.now() - pub_time).days < 7:
                            quality_score += 0.1
                            quality_factors.append('recent_content')
        except Exception as e:
            quality_score -= 0.1
            quality_factors.append('feed_access_error')
        
        quality_assessment.update({
            'quality_score': min(1.0, max(0.0, quality_score)),
            'quality_factors': quality_factors,
            'assessment_timestamp': datetime.now().isoformat()
        })
        
        return quality_assessment
    
    def _validate_single_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single news source."""
        validation_result = {
            'source': source,
            'status': 'unknown',
            'warnings': [],
            'updated_info': {}
        }
        
        url = source.get('rss', source.get('url', ''))
        if not url:
            validation_result['status'] = 'invalid'
            validation_result['warnings'].append('No URL provided')
            return validation_result
        
        try:
            # Check accessibility
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                validation_result['status'] = 'invalid'
                validation_result['warnings'].append(f'HTTP {response.status_code}')
                return validation_result
            
            # Parse feed
            feed_data = feedparser.parse(url)
            if not feed_data.entries:
                validation_result['status'] = 'invalid'
                validation_result['warnings'].append('No entries in feed')
                return validation_result
            
            # Check for recent content
            latest_entry = feed_data.entries[0]
            if hasattr(latest_entry, 'published_parsed'):
                pub_time = datetime(*latest_entry.published_parsed[:6])
                days_since_update = (datetime.now() - pub_time).days
                
                if days_since_update > 30:
                    validation_result['warnings'].append(f'No updates for {days_since_update} days')
                elif days_since_update > 7:
                    validation_result['warnings'].append(f'Last update {days_since_update} days ago')
            
            # Update source information if available
            if feed_data.feed:
                if hasattr(feed_data.feed, 'title') and feed_data.feed.title:
                    validation_result['updated_info']['title'] = feed_data.feed.title
                if hasattr(feed_data.feed, 'description') and feed_data.feed.description:
                    validation_result['updated_info']['description'] = feed_data.feed.description
            
            validation_result['status'] = 'valid'
            
        except Exception as e:
            validation_result['status'] = 'invalid'
            validation_result['warnings'].append(f'Validation error: {str(e)}')
        
        return validation_result
    
    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sources from a list."""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            url = source.get('rss_url', source.get('url', ''))
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        return unique_sources
    
    def _extract_site_name(self, url: str) -> str:
        """Extract a readable site name from URL."""
        domain = urlparse(url).netloc
        # Remove 'www.' and common subdomains
        domain = re.sub(r'^(www\.|m\.)', '', domain)
        # Convert to title case
        name = domain.replace('.', ' ').title()
        return name
    
    def _get_regional_search_patterns(self, country_code: str, language: str) -> List[str]:
        """Get search patterns for regional source discovery."""
        patterns = []
        
        # Base patterns
        base_terms = ['news', 'noticias', 'nouvelles', 'nachrichten', 'новости', '新闻']
        country_terms = {
            'us': ['american', 'usa', 'united states'],
            'uk': ['british', 'britain', 'england'],
            'ca': ['canadian', 'canada'],
            'au': ['australian', 'australia'],
            'de': ['german', 'deutschland'],
            'fr': ['french', 'france', 'français'],
            'es': ['spanish', 'spain', 'español'],
            'it': ['italian', 'italy', 'italiano'],
            'ru': ['russian', 'russia', 'русский'],
            'cn': ['chinese', 'china', '中国'],
            'jp': ['japanese', 'japan', '日本'],
            'br': ['brazilian', 'brazil', 'brasileiro']
        }
        
        if country_code in country_terms:
            for base_term in base_terms:
                for country_term in country_terms[country_code]:
                    patterns.append(f"{country_term} {base_term}")
        
        return patterns
    
    def _filter_regional_sources(self, sources: List[Dict[str, Any]], 
                               country_code: str, language: str) -> List[Dict[str, Any]]:
        """Filter sources for regional relevance."""
        filtered_sources = []
        
        for source in sources:
            # Basic filtering logic - in practice, this would be more sophisticated
            url = source.get('url', '').lower()
            
            # Check for country code in domain
            if f'.{country_code}' in url:
                filtered_sources.append(source)
            elif any(keyword in url for keyword in ['news', 'media', 'press']):
                filtered_sources.append(source)
        
        return filtered_sources
    
    def _generate_optimization_recommendations(self, optimization_results: Dict[str, Any]) -> List[str]:
        """Generate source optimization recommendations."""
        recommendations = []
        
        # Recommendations for unreliable sources
        if optimization_results['unreliable_sources']:
            count = len(optimization_results['unreliable_sources'])
            recommendations.append(f"Remove or investigate {count} unreliable sources with <40% success rate")
        
        # Recommendations for underperformers
        if optimization_results['underperformers']:
            count = len(optimization_results['underperformers'])
            recommendations.append(f"Review {count} underperforming sources with low article yield")
        
        # Recommendations for slow sources
        if optimization_results['slow_sources']:
            count = len(optimization_results['slow_sources'])
            recommendations.append(f"Optimize or replace {count} slow sources with >30s response time")
        
        # Recommendations for high performers
        if optimization_results['high_performers']:
            count = len(optimization_results['high_performers'])
            recommendations.append(f"Consider increasing collection frequency for {count} high-performing sources")
        
        return recommendations


# Initialize global source manager instance
intelligent_source_manager = IntelligentSourceManager()
