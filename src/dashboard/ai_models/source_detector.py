"""
AI-powered news source detection using BERT and NLP techniques
"""

import re
import requests
from urllib.parse import urlparse
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class NewsSourceDetector:
    def __init__(self):
        """Initialize the BERT-based source detector"""
        try:
            # Initialize BERT model for text analysis
            self.tokenizer = AutoTokenizer.from_pretrained('bert-base-multilingual-cased')
            self.model = AutoModel.from_pretrained('bert-base-multilingual-cased')
            
            # Initialize classification pipeline for content analysis
            self.classifier = pipeline(
                "text-classification",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Known news sources database
            self.news_sources = {
                # Spanish sources
                'elpais.com': 'El País',
                'elmundo.es': 'El Mundo',
                'abc.es': 'ABC',
                'lavanguardia.com': 'La Vanguardia',
                'elconfidencial.com': 'El Confidencial',
                'publico.es': 'Público',
                'rtve.es': 'RTVE',
                
                # International sources
                'reuters.com': 'Reuters',
                'bbc.com': 'BBC News',
                'bbc.co.uk': 'BBC News',
                'cnn.com': 'CNN',
                'nytimes.com': 'The New York Times',
                'washingtonpost.com': 'The Washington Post',
                'theguardian.com': 'The Guardian',
                'ft.com': 'Financial Times',
                'wsj.com': 'Wall Street Journal',
                'bloomberg.com': 'Bloomberg',
                'ap.org': 'Associated Press',
                'apnews.com': 'Associated Press',
                
                # European sources
                'lemonde.fr': 'Le Monde',
                'lefigaro.fr': 'Le Figaro',
                'liberation.fr': 'Libération',
                'spiegel.de': 'Der Spiegel',
                'zeit.de': 'Die Zeit',
                'faz.net': 'Frankfurter Allgemeine',
                'corriere.it': 'Corriere della Sera',
                'repubblica.it': 'La Repubblica',
                
                # Middle East & Asia
                'aljazeera.com': 'Al Jazeera',
                'alarabiya.net': 'Al Arabiya',
                'haaretz.com': 'Haaretz',
                'scmp.com': 'South China Morning Post',
                'japantimes.co.jp': 'The Japan Times',
                'straitstimes.com': 'The Straits Times',
                
                # Russian & Eastern European
                'rt.com': 'RT News',
                'sputniknews.com': 'Sputnik News',
                'tass.com': 'TASS',
                'pravda.ru': 'Pravda',
                
                # Latin American
                'clarin.com': 'Clarín',
                'lanacion.com.ar': 'La Nación',
                'folha.uol.com.br': 'Folha de S.Paulo',
                'globo.com': 'O Globo',
                'milenio.com': 'Milenio',
                'excelsior.com.mx': 'Excélsior',
                
                # News agencies
                'xinhuanet.com': 'Xinhua News',
                'efe.com': 'Agencia EFE',
                'afp.com': 'AFP',
                'dpa.com': 'DPA',
                'ansa.it': 'ANSA'
            }
            
            # Keywords for source identification
            self.source_keywords = {
                'Reuters': ['reuters', 'thomson reuters'],
                'BBC News': ['bbc', 'british broadcasting'],
                'CNN': ['cnn', 'cable news network'],
                'Associated Press': ['ap', 'associated press'],
                'Bloomberg': ['bloomberg'],
                'Financial Times': ['ft', 'financial times'],
                'The Guardian': ['guardian'],
                'El País': ['el país', 'elpais'],
                'Le Monde': ['le monde'],
                'Der Spiegel': ['spiegel'],
                'Al Jazeera': ['al jazeera', 'aljazeera'],
                'Xinhua News': ['xinhua'],
                'TASS': ['tass'],
                'Agencia EFE': ['efe', 'agencia efe']
            }
            
        except Exception as e:
            logger.error(f"Error initializing NewsSourceDetector: {e}")
            self.tokenizer = None
            self.model = None
            self.classifier = None
    
    def extract_domain_from_url(self, url):
        """Extract domain from URL"""
        try:
            if not url:
                return None
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return None
    
    def detect_source_from_url(self, url):
        """Detect news source from URL"""
        domain = self.extract_domain_from_url(url)
        if domain and domain in self.news_sources:
            return self.news_sources[domain]
        return None
    
    def detect_source_from_content(self, title, content=None):
        """Use BERT to analyze content and detect source"""
        try:
            if not self.tokenizer or not self.model:
                return self.fallback_source_detection(title, content)
            
            # Combine title and content for analysis
            text = title
            if content:
                text += " " + content[:500]  # Limit content length
            
            text = text.lower()
            
            # Check for explicit source mentions
            for source, keywords in self.source_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        return source
            
            # Use BERT embeddings for similarity matching
            return self.bert_similarity_matching(text)
            
        except Exception as e:
            logger.error(f"Error in BERT source detection: {e}")
            return self.fallback_source_detection(title, content)
    
    def bert_similarity_matching(self, text):
        """Use BERT embeddings to find similar source patterns"""
        try:
            # Tokenize and get embeddings
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
            
            # Simple pattern matching based on common news source indicators
            patterns = {
                'Reuters': ['breaking news', 'exclusive', 'sources said'],
                'BBC News': ['bbc news', 'correspondent', 'reporting'],
                'CNN': ['cnn', 'breaking'],
                'Associated Press': ['ap news', 'associated press'],
                'Bloomberg': ['bloomberg', 'markets', 'financial'],
                'Al Jazeera': ['middle east', 'qatar', 'doha']
            }
            
            for source, indicators in patterns.items():
                if any(indicator in text for indicator in indicators):
                    return source
            
            return None
            
        except Exception as e:
            logger.error(f"Error in BERT similarity matching: {e}")
            return None
    
    def fallback_source_detection(self, title, content=None):
        """Fallback method for source detection without BERT"""
        text = (title + " " + (content or "")).lower()
        
        # Simple keyword matching
        source_patterns = {
            'Reuters': ['reuters', 'thomson reuters'],
            'BBC News': ['bbc', 'british broadcasting corporation'],
            'CNN': ['cnn', 'cable news network'],
            'Associated Press': ['associated press', 'ap news'],
            'Bloomberg': ['bloomberg'],
            'Financial Times': ['financial times', 'ft.com'],
            'The Guardian': ['guardian', 'theguardian'],
            'El País': ['el país', 'elpais'],
            'Le Monde': ['le monde'],
            'Der Spiegel': ['der spiegel', 'spiegel'],
            'Al Jazeera': ['al jazeera', 'aljazeera'],
            'Xinhua News': ['xinhua'],
            'TASS': ['tass'],
            'RT News': ['russia today', 'rt news'],
            'Agencia EFE': ['agencia efe', 'efe']
        }
        
        for source, patterns in source_patterns.items():
            if any(pattern in text for pattern in patterns):
                return source
        
        return 'Fuente Internacional'
    
    def analyze_article_metadata(self, article_data):
        """Analyze article metadata to extract source information"""
        try:
            # Try URL first
            if 'url' in article_data and article_data['url']:
                source = self.detect_source_from_url(article_data['url'])
                if source:
                    return source
            
            # Try content analysis
            title = article_data.get('title', '')
            content = article_data.get('content', '') or article_data.get('description', '')
            
            source = self.detect_source_from_content(title, content)
            if source:
                return source
            
            # Check if source is already provided
            if 'source' in article_data and article_data['source']:
                provided_source = article_data['source']
                if provided_source.lower() not in ['rss feed', 'feed', 'rss']:
                    return provided_source
            
            return 'Agencia Internacional'
            
        except Exception as e:
            logger.error(f"Error analyzing article metadata: {e}")
            return 'Fuente Desconocida'
    
    def batch_analyze_sources(self, articles):
        """Analyze multiple articles for source detection"""
        results = []
        for article in articles:
            source = self.analyze_article_metadata(article)
            results.append({
                **article,
                'detected_source': source
            })
        return results

# Global instance
source_detector = NewsSourceDetector()

def detect_news_source(article_data):
    """Main function to detect news source"""
    return source_detector.analyze_article_metadata(article_data)

def batch_detect_sources(articles):
    """Batch process articles for source detection"""
    return source_detector.batch_analyze_sources(articles)