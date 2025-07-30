#!/usr/bin/env python3
"""
RSS Fetcher for Geopolitical Intelligence System
Fetches, processes, translates and analyzes news from RSS sources
"""

import feedparser
import requests
import sqlite3
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import time
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import hashlib

# Add parent directories to path
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.config import config
from utils.translation import TranslationService
from utils.bert_risk_analyzer import BERTRiskAnalyzer
from utils.content_classifier import ContentClassifier

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import advanced NLP analyzer
try:
    from nlp_processing.advanced_analyzer import AdvancedNLPAnalyzer
    ADVANCED_NLP_AVAILABLE = True
    logger.info("Advanced NLP analyzer available")
except ImportError as e:
    logger.warning(f"Advanced NLP analyzer not available: {e}")
    ADVANCED_NLP_AVAILABLE = False

class RSSFetcher:
    """RSS Fetcher with translation, risk analysis and content filtering."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.translation_service = TranslationService()
        self.risk_analyzer = BERTRiskAnalyzer()
        self.content_classifier = ContentClassifier()
        
        # Initialize advanced NLP analyzer if available
        if ADVANCED_NLP_AVAILABLE:
            try:
                self.advanced_nlp_analyzer = AdvancedNLPAnalyzer()
                logger.info("Advanced NLP analyzer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize advanced NLP analyzer: {e}")
                self.advanced_nlp_analyzer = None
        else:
            self.advanced_nlp_analyzer = None
        
        # Geopolitical keywords for content filtering
        self.geopolitical_keywords = {
            'en': [
                'politics', 'political', 'government', 'election', 'democracy', 'diplomacy',
                'military', 'defense', 'security', 'war', 'conflict', 'peace', 'treaty',
                'sanctions', 'embargo', 'trade war', 'tariff', 'economic policy',
                'climate change', 'global warming', 'environmental policy', 'carbon',
                'energy', 'oil', 'gas', 'renewable', 'nuclear', 'coal', 'petroleum',
                'resources', 'mining', 'water', 'food security', 'agriculture',
                'geopolitics', 'international', 'foreign policy', 'alliance', 'nato',
                'terrorism', 'cyber', 'intelligence', 'espionage', 'migration',
                'refugee', 'border', 'sovereignty', 'independence', 'revolution',
                'protest', 'uprising', 'crisis', 'emergency', 'disaster'
            ],
            'es': [
                'política', 'político', 'gobierno', 'elección', 'democracia', 'diplomacia',
                'militar', 'defensa', 'seguridad', 'guerra', 'conflicto', 'paz', 'tratado',
                'sanciones', 'embargo', 'guerra comercial', 'arancel', 'política económica',
                'cambio climático', 'calentamiento global', 'política ambiental', 'carbono',
                'energía', 'petróleo', 'gas', 'renovable', 'nuclear', 'carbón',
                'recursos', 'minería', 'agua', 'seguridad alimentaria', 'agricultura',
                'geopolítica', 'internacional', 'política exterior', 'alianza',
                'terrorismo', 'cibernético', 'inteligencia', 'espionaje', 'migración',
                'refugiado', 'frontera', 'soberanía', 'independencia', 'revolución',
                'protesta', 'levantamiento', 'crisis', 'emergencia', 'desastre'
            ],
            'fr': [
                'politique', 'gouvernement', 'élection', 'démocratie', 'diplomatie',
                'militaire', 'défense', 'sécurité', 'guerre', 'conflit', 'paix', 'traité',
                'sanctions', 'embargo', 'guerre commerciale', 'tarif', 'politique économique',
                'changement climatique', 'réchauffement', 'politique environnementale',
                'énergie', 'pétrole', 'gaz', 'renouvelable', 'nucléaire', 'charbon',
                'ressources', 'exploitation minière', 'eau', 'sécurité alimentaire',
                'géopolitique', 'international', 'politique étrangère', 'alliance',
                'terrorisme', 'cyber', 'renseignement', 'espionnage', 'migration',
                'réfugié', 'frontière', 'souveraineté', 'ind��pendance', 'révolution',
                'manifestation', 'soulèvement', 'crise', 'urgence', 'catastrophe'
            ]
        }
    
    def get_db_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def fetch_all_sources(self, target_language: str = 'es') -> Dict[str, int]:
        """Fetch articles from all active RSS sources."""
        logger.info(f"Starting RSS fetch for all sources (target language: {target_language})")
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get active RSS sources
        cursor.execute('''
            SELECT id, name, url, language, region, priority
            FROM sources 
            WHERE active = 1
            ORDER BY priority DESC, name
        ''')
        
        sources = cursor.fetchall()
        conn.close()
        
        results = {
            'total_sources': len(sources),
            'processed_sources': 0,
            'total_articles': 0,
            'new_articles': 0,
            'filtered_articles': 0,
            'errors': 0
        }
        
        for source in sources:
            try:
                logger.info(f"Processing source: {source['name']}")
                source_result = self.fetch_source(
                    source['id'], 
                    source['url'], 
                    source['language'],
                    source['region'],
                    target_language
                )
                
                results['processed_sources'] += 1
                results['total_articles'] += source_result['total_articles']
                results['new_articles'] += source_result['new_articles']
                results['filtered_articles'] += source_result['filtered_articles']
                
                # Update source fetch statistics
                self.update_source_stats(source['id'], source_result['total_articles'], None)
                
                # Small delay between sources to be respectful
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing source {source['name']}: {e}")
                results['errors'] += 1
                self.update_source_stats(source['id'], 0, str(e))
        
        logger.info(f"RSS fetch completed: {results}")
        return results
    
    def fetch_source(self, source_id: int, url: str, source_language: str, 
                    region: str, target_language: str = 'es') -> Dict[str, int]:
        """Fetch articles from a single RSS source."""
        
        # Skip API endpoints that require configuration
        if any(pattern in url for pattern in ['{keywords}', 'YOUR_KEY', 'access_key=YOUR_KEY']):
            logger.info(f"Skipping API endpoint that requires configuration: {url}")
            return {'total_articles': 0, 'new_articles': 0, 'filtered_articles': 0}
        
        try:
            # Fetch RSS feed
            logger.info(f"Fetching RSS from: {url}")
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"RSS feed has issues: {url}")
            
            result = {
                'total_articles': len(feed.entries),
                'new_articles': 0,
                'filtered_articles': 0
            }
            
            for entry in feed.entries:
                try:
                    # Extract article data
                    article_data = self.extract_article_data(entry, source_language, region)
                    
                    if not article_data:
                        continue
                    
                    # Check if article already exists
                    if self.article_exists(article_data['url']):
                        continue
                    
                    # Filter geopolitical content
                    if not self.is_geopolitical_content(article_data['title'], article_data['content'], source_language):
                        result['filtered_articles'] += 1
                        continue
                    
                    # Additional filter using content classifier to exclude sports/entertainment
                    text_for_classification = f"{article_data['title']} {article_data['content']}"
                    category = self.content_classifier.classify(text_for_classification)
                    if category == 'sports_entertainment':
                        result['filtered_articles'] += 1
                        logger.info(f"Filtered sports/entertainment article: {article_data['title'][:50]}...")
                        continue
                    
                    # Translate if needed
                    if source_language != target_language:
                        article_data = self.translate_article(article_data, source_language, target_language)
                    
                    # Analyze risk and extract metadata
                    article_data = self.analyze_article(article_data)
                    
                    # Save to database
                    article_id = self.save_article(article_data, source_id)
                    
                    if article_id:
                        result['new_articles'] += 1
                        logger.info(f"Saved article: {article_data['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching RSS source {url}: {e}")
            raise
    
    def extract_article_data(self, entry, source_language: str, region: str) -> Optional[Dict]:
        """Extract article data from RSS entry."""
        try:
            # Get publication date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except (TypeError, ValueError):
                    published = datetime.now()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                try:
                    published = datetime(*entry.updated_parsed[:6])
                except (TypeError, ValueError):
                    published = datetime.now()
            else:
                published = datetime.now()
            
            # Skip articles older than 7 days
            if published < datetime.now() - timedelta(days=7):
                return None
            
            # Extract content with better error handling
            content = ""
            try:
                if hasattr(entry, 'content') and entry.content:
                    if isinstance(entry.content, list) and len(entry.content) > 0:
                        content = getattr(entry.content[0], 'value', str(entry.content[0]))
                    else:
                        content = str(entry.content)
                elif hasattr(entry, 'summary') and entry.summary:
                    content = str(entry.summary)
                elif hasattr(entry, 'description') and entry.description:
                    content = str(entry.description)
            except (AttributeError, TypeError) as e:
                logger.warning(f"Error extracting content: {e}")
                content = ""
            
            # Clean HTML tags and normalize whitespace
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Extract image URL with better error handling
            image_url = None
            try:
                if hasattr(entry, 'media_content') and entry.media_content:
                    if isinstance(entry.media_content, list) and len(entry.media_content) > 0:
                        image_url = entry.media_content[0].get('url')
                elif hasattr(entry, 'enclosures') and entry.enclosures:
                    for enclosure in entry.enclosures:
                        if hasattr(enclosure, 'type') and enclosure.type and 'image' in enclosure.type:
                            if hasattr(enclosure, 'href'):
                                image_url = enclosure.href
                                break
            except (AttributeError, TypeError, IndexError) as e:
                logger.warning(f"Error extracting image URL: {e}")
                image_url = None
            
            # Extract title and URL with error handling
            try:
                title = getattr(entry, 'title', 'No title')
                if title and hasattr(title, 'strip'):
                    title = title.strip()
                else:
                    title = str(title) if title else 'No title'
            except (AttributeError, TypeError):
                title = 'No title'
            
            try:
                url = getattr(entry, 'link', '')
                if not url:
                    url = getattr(entry, 'id', '')
                url = str(url) if url else ''
            except (AttributeError, TypeError):
                url = ''
            
            # Validate required fields
            if not title or title == 'No title' or not url:
                logger.warning(f"Skipping article with missing title or URL: title='{title}', url='{url}'")
                return None
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'published': published,
                'language': source_language,
                'region': region,
                'image_url': image_url
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None
    
    def is_geopolitical_content(self, title: str, content: str, language: str) -> bool:
        """Check if content is geopolitically relevant."""
        text = f"{title} {content}".lower()
        
        # Get keywords for the language
        keywords = self.geopolitical_keywords.get(language, self.geopolitical_keywords['en'])
        
        # Check for keyword matches
        matches = sum(1 for keyword in keywords if keyword.lower() in text)
        
        # Require at least 2 keyword matches for relevance
        is_relevant = matches >= 2
        
        # Additional checks for obvious non-geopolitical content
        # Enhanced sports filtering with multilingual support
        non_relevant_patterns = [
            # Cricket specific patterns (high priority)
            r'\bcricket\b', r'\bcríquet\b', r'\bpcb\b', r'\bbcci\b', r'\bicc\b',
            r'\bcricket board\b', r'\bcricket council\b', r'\bcricket asia\b',
            
            # Sports - English
            r'\bsports?\b', r'\bfootball\b', r'\bbasketball\b', r'\bsoccer\b',
            r'\bbaseball\b', r'\btennis\b', r'\bgolf\b', r'\bhockey\b',
            r'\bvolleyball\b', r'\bswimming\b', r'\bathletics\b', r'\bgymnastics\b',
            r'\boxing\b', r'\bwrestling\b', r'\bmma\b', r'\bufc\b',
            r'\bolympics?\b', r'\bworld cup\b', r'\bchampionship\b(?!.*political)',
            r'\bteam\b.*\b(wins?|lost?|defeats?|victory|champion)\b',
            r'\bplayer\b', r'\bcoach\b', r'\bstadium\b', r'\bmatch\b(?!.*diplomatic)',
            r'\btournament\b', r'\bleague\b', r'\bseason\b(?!.*political)',
            
            # Major sports organizations
            r'\bfifa\b', r'\buefa\b', r'\bnba\b', r'\bnfl\b', r'\bmlb\b', r'\bnhl\b',
            
            # Sports - Spanish
            r'\bdeporte\b', r'\bfútbol\b', r'\bbaloncesto\b', r'\btenis\b',
            r'\bgolf\b', r'\bjockey\b', r'\bvoleibol\b', r'\bnatación\b',
            r'\batletismo\b', r'\bgimnasia\b', r'\bbox\b', r'\blucha\b',
            r'\bolímpicos?\b', r'\bmundial\b(?!.*político)', r'\bcampeonato\b(?!.*político)',
            r'\bequipo\b.*\b(gana|ganó|pierde|perdió|derrota|victoria|campeón)\b',
            r'\bjugador\b', r'\bentrenador\b', r'\bestadio\b', r'\bpartido\b(?!.*político)',
            r'\btorneo\b', r'\bliga\b', r'\btemporada\b(?!.*política)',
            
            # Sports - French
            r'\bsport\b', r'\bfootball\b', r'\bbasket\b', r'\btennis\b',
            r'\bgolf\b', r'\bhockey\b', r'\bvolley\b', r'\bnatation\b',
            r'\bathlétisme\b', r'\bgymnastique\b', r'\bbox\b', r'\blutte\b',
            r'\bolympiques?\b', r'\bmondial\b(?!.*politique)', r'\bchampionnat\b(?!.*politique)',
            r'\béquipe\b.*\b(gagne|gagné|perd|perdu|défaite|victoire|champion)\b',
            r'\bjoueur\b', r'\bentraîneur\b', r'\bstade\b', r'\bmatch\b(?!.*diplomatique)',
            r'\btournoi\b', r'\bligue\b', r'\bsaison\b(?!.*politique)',
            
            # Sports - German
            r'\bsport\b', r'\bfußball\b', r'\bbasketball\b', r'\btennis\b',
            r'\bgolf\b', r'\bhockey\b', r'\bvolleyball\b', r'\bschwimmen\b',
            r'\bleichtathletik\b', r'\bturnen\b', r'\bbox\b', r'\bringen\b',
            r'\bolympische?\b', r'\bweltmeisterschaft\b(?!.*politisch)',
            r'\bmannschaft\b.*\b(gewinnt|gewonnen|verliert|verloren|niederlage|sieg|meister)\b',
            r'\bspieler\b', r'\btrainer\b', r'\bstadion\b', r'\bspiel\b(?!.*diplomatisch)',
            r'\bturnier\b', r'\bliga\b', r'\bsaison\b(?!.*politisch)',
            
            # Entertainment and lifestyle
            r'\bentertainment\b', r'\bcelebrity\b', r'\bmovie\b', r'\bmusic\b',
            r'\bfashion\b', r'\bbeauty\b', r'\brecipe\b', r'\bcooking\b',
            r'\bhealth\b(?!.*public)', r'\bfitness\b', r'\bdiet\b', r'\bweight loss\b',
            r'\btechnology\b(?!.*security)', r'\bgaming\b', r'\bapp\b(?!.*government)',
            
            # Entertainment - Spanish
            r'\bentretenimiento\b', r'\bcelebridad\b', r'\bpelícula\b', r'\bmúsica\b',
            r'\bmoda\b', r'\bbelleza\b', r'\breceta\b', r'\bcocina\b',
            r'\bsalud\b(?!.*pública)', r'\bejercicio\b', r'\bdieta\b',
            
            # Entertainment - French
            r'\bdivertissement\b', r'\bcélébrité\b', r'\bfilm\b', r'\bmusique\b',
            r'\bmode\b', r'\bbeauté\b', r'\brecette\b', r'\bcuisine\b',
            r'\bsanté\b(?!.*publique)', r'\bexercice\b', r'\brégime\b',
            
            # Entertainment - German
            r'\bunterhaltung\b', r'\bprominente\b', r'\bfilm\b', r'\bmusik\b',
            r'\bmode\b', r'\bschönheit\b', r'\brezept\b', r'\bkochen\b',
            r'\bgesundheit\b(?!.*öffentlich)', r'\bübung\b', r'\bdiät\b'
        ]
        
        for pattern in non_relevant_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                is_relevant = False
                break
        
        return is_relevant
    
    def translate_article(self, article_data: Dict, source_lang: str, target_lang: str) -> Dict:
        """Translate article to target language."""
        try:
            # Translate title
            article_data['title'] = self.translation_service.translate(
                article_data['title'], source_lang, target_lang
            )
            
            # Translate content (limit to first 1000 chars for efficiency)
            content_to_translate = article_data['content'][:1000]
            article_data['content'] = self.translation_service.translate(
                content_to_translate, source_lang, target_lang
            )
            
            # Update language
            article_data['language'] = target_lang
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error translating article: {e}")
            return article_data
    
    def analyze_article(self, article_data: Dict) -> Dict:
        """Analyze article for risk level and extract metadata."""
        try:
            text = f"{article_data['title']} {article_data['content']}"
            
            # Analyze risk level using title and content separately
            risk_analysis = self.risk_analyzer.analyze_risk(
                title=article_data['title'],
                content=article_data['content'],
                country=article_data.get('country')
            )
            article_data['risk_level'] = risk_analysis['level']
            article_data['risk_score'] = risk_analysis['score']
            
            # Extract country/region
            country = self.extract_country(text)
            if country:
                article_data['country'] = country
            
            # Classify content category
            category = self.content_classifier.classify(text)
            article_data['category'] = category
            
            # Extract keywords
            keywords = self.extract_keywords(text)
            article_data['keywords'] = keywords
            
            # Analyze sentiment
            sentiment = self.analyze_sentiment(text)
            article_data['sentiment'] = sentiment
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return article_data
    
    def extract_country(self, text: str) -> Optional[str]:
        """Extract country/region from text."""
        # Country patterns (extend as needed)
        country_patterns = {
            'Ukraine': [r'\bukraine\b', r'\bkyiv\b', r'\bkiev\b'],
            'Russia': [r'\brussia\b', r'\bmoscow\b', r'\bkremlin\b'],
            'China': [r'\bchina\b', r'\bbeijing\b', r'\bchinese\b'],
            'United States': [r'\busa\b', r'\bunited states\b', r'\bamerica\b', r'\bwashington\b'],
            'Iran': [r'\biran\b', r'\btehran\b', r'\biranian\b'],
            'Israel': [r'\bisrael\b', r'\bjerusalem\b', r'\btel aviv\b'],
            'Germany': [r'\bgermany\b', r'\bberlin\b', r'\bgerman\b'],
            'France': [r'\bfrance\b', r'\bparis\b', r'\bfrench\b'],
            'United Kingdom': [r'\buk\b', r'\bunited kingdom\b', r'\bbritain\b', r'\blondon\b'],
            'Japan': [r'\bjapan\b', r'\btokyo\b', r'\bjapanese\b'],
            'India': [r'\bindia\b', r'\bnew delhi\b', r'\bindian\b'],
            'Brazil': [r'\bbrazil\b', r'\bbrasilia\b', r'\bbrazilian\b'],
            'Turkey': [r'\bturkey\b', r'\bankara\b', r'\bturkish\b'],
            'Saudi Arabia': [r'\bsaudi arabia\b', r'\briyadh\b', r'\bsaudi\b'],
            'South Korea': [r'\bsouth korea\b', r'\bseoul\b', r'\bkorean\b'],
            'North Korea': [r'\bnorth korea\b', r'\bpyongyang\b'],
            'Syria': [r'\bsyria\b', r'\bdamascus\b', r'\bsyrian\b'],
            'Iraq': [r'\biraq\b', r'\bbaghdad\b', r'\biraqi\b'],
            'Afghanistan': [r'\bafghanistan\b', r'\bkabul\b', r'\bafghan\b'],
            'Pakistan': [r'\bpakistan\b', r'\bislamabad\b', r'\bpakistani\b']
        }
        
        text_lower = text.lower()
        
        for country, patterns in country_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return country
        
        return None
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Filter common words and get geopolitical terms
        relevant_keywords = []
        for lang_keywords in self.geopolitical_keywords.values():
            for keyword in lang_keywords:
                if keyword.lower() in words:
                    relevant_keywords.append(keyword)
        
        return list(set(relevant_keywords))[:10]  # Limit to 10 keywords
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text (simplified)."""
        # Simple sentiment analysis based on keywords
        positive_words = ['peace', 'agreement', 'cooperation', 'stability', 'progress', 'success']
        negative_words = ['war', 'conflict', 'crisis', 'threat', 'attack', 'violence', 'tension']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def article_exists(self, url: str) -> bool:
        """Check if article already exists in database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM articles WHERE url = ?', (url,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def save_article(self, article_data: Dict, source_id: int) -> Optional[int]:
        """Save article to database with MANDATORY advanced NLP analysis."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Insert article
            cursor.execute('''
                INSERT INTO articles (
                    title, content, url, source, language, country, region,
                    risk_level, risk_score, image_url, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_data['title'],
                article_data['content'],
                article_data['url'],
                article_data.get('source', 'RSS Feed'),
                article_data['language'],
                article_data.get('country'),
                article_data['region'],
                article_data.get('risk_level', 'low'),
                article_data.get('risk_score', 0.0),
                article_data.get('image_url'),
                article_data['published'].isoformat()
            ))
            
            article_id = cursor.lastrowid
            
            # ===== MANDATORY ADVANCED NLP ANALYSIS =====
            logger.info(f"🧠 Performing MANDATORY advanced NLP analysis for article {article_id}")
            
            # Prepare article data for comprehensive analysis
            article_for_nlp = {
                'title': article_data['title'] or '',
                'content': article_data['content'] or '',
                'description': ''
            }
            
            # Initialize default values
            advanced_nlp_data = None
            nlp_entities = {}
            nlp_sentiment = {'score': 0.0, 'label': 'neutral'}
            bert_results = {'level': 'low', 'score': 0.0, 'confidence': 0.0, 'reasoning': 'Basic analysis'}
            
            # Perform advanced NLP analysis if available
            if self.advanced_nlp_analyzer:
                try:
                    logger.info(f"🔬 Running comprehensive NLP analysis...")
                    nlp_results = self.advanced_nlp_analyzer.analyze_article_comprehensive(article_for_nlp)
                    
                    # Perform BERT risk analysis
                    bert_results = self.risk_analyzer.analyze_risk(
                        title=article_data['title'] or '',
                        content=article_data['content'] or '',
                        country=article_data.get('country')
                    )
                    
                    # Update article with BERT risk analysis
                    cursor.execute('''
                        UPDATE articles 
                        SET risk_level = ?, risk_score = ?
                        WHERE id = ?
                    ''', (bert_results['level'], bert_results['score'], article_id))
                    
                    # Combine all analysis results
                    advanced_nlp_data = {
                        'nlp_entities': nlp_results['entities'],
                        'sentiment_analysis': nlp_results['sentiment'],
                        'title_sentiment': nlp_results['title_sentiment'],
                        'nlp_risk_score': nlp_results['risk_score'],
                        'bert_risk_level': bert_results['level'],
                        'bert_risk_score': bert_results['score'],
                        'bert_confidence': bert_results['confidence'],
                        'bert_reasoning': bert_results['reasoning'],
                        'key_factors': bert_results.get('key_factors', []),
                        'geographic_impact': bert_results.get('geographic_impact', 'Unknown'),
                        'escalation_potential': bert_results.get('potential_escalation', 'Unknown'),
                        'key_persons': nlp_results['key_persons'],
                        'key_locations': nlp_results['key_locations'],
                        'conflict_indicators': nlp_results['conflict_indicators'],
                        'total_entities': nlp_results['total_entities'],
                        'ai_powered': bert_results['ai_powered'],
                        'model_used': bert_results['model_used'],
                        'analysis_timestamp': nlp_results['analysis_timestamp']
                    }
                    
                    nlp_entities = nlp_results['entities']
                    nlp_sentiment = nlp_results['sentiment']
                    
                    logger.info(f"✅ Advanced NLP analysis completed:")
                    logger.info(f"   - BERT Risk: {bert_results['level']} ({bert_results['score']:.3f})")
                    logger.info(f"   - Sentiment: {nlp_sentiment['label']} ({nlp_sentiment['score']:.3f})")
                    logger.info(f"   - Entities: {nlp_results['total_entities']}")
                    logger.info(f"   - Key persons: {', '.join(nlp_results['key_persons'][:3])}")
                    logger.info(f"   - Key locations: {', '.join(nlp_results['key_locations'][:3])}")
                    
                except Exception as e:
                    logger.error(f"❌ Advanced NLP analysis failed for article {article_id}: {e}")
                    # Continue with basic analysis
                    pass
            else:
                logger.warning(f"⚠️  Advanced NLP analyzer not available, using basic analysis")
            
            # Insert processed data with advanced NLP results
            cursor.execute('''
                INSERT INTO processed_data (
                    article_id, summary, category, keywords, sentiment, entities, advanced_nlp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_id,
                article_data['content'][:300] + '...' if len(article_data['content']) > 300 else article_data['content'],
                article_data.get('category', 'geopolitical_analysis'),
                json.dumps(article_data.get('keywords', []) + nlp_entities.get('persons', [])[:3] + nlp_entities.get('locations', [])[:3]),
                nlp_sentiment['score'],
                json.dumps(nlp_entities),
                json.dumps(advanced_nlp_data) if advanced_nlp_data else None
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Article {article_id} saved with complete NLP analysis")
            return article_id
            
        except Exception as e:
            logger.error(f"❌ Error saving article with NLP analysis: {e}")
            return None
    
    def update_source_stats(self, source_id: int, fetch_count: int, error: Optional[str]):
        """Update source fetch statistics."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            if error:
                cursor.execute('''
                    UPDATE sources 
                    SET last_fetched = ?, error_count = error_count + 1, last_error = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), error, source_id))
            else:
                cursor.execute('''
                    UPDATE sources 
                    SET last_fetched = ?, fetch_count = fetch_count + ?, last_error = NULL
                    WHERE id = ?
                ''', (datetime.now().isoformat(), fetch_count, source_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating source stats: {e}")

def main():
    """Main function for testing."""
    # Database path
    BASE_DIR = Path(__file__).resolve().parents[2]
    DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')
    
    # Create fetcher
    fetcher = RSSFetcher(DB_PATH)
    
    # Fetch all sources
    results = fetcher.fetch_all_sources(target_language='es')
    
    print(f"RSS Fetch Results: {results}")

if __name__ == "__main__":
    main()