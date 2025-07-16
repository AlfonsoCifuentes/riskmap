"""
Source Reliability and Credibility Scoring System
Evaluates news sources based on multiple reliability factors
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict, Counter
import re
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class SourceReliabilityMetrics:
    """Metrics for evaluating source reliability."""
    source_id: str
    source_name: str
    country: str
    language: str
    domain: str
    
    # Quality metrics
    content_quality_score: float = 0.0
    factual_accuracy_score: float = 0.0
    editorial_standards_score: float = 0.0
    transparency_score: float = 0.0
    
    # Performance metrics
    uptime_percentage: float = 0.0
    response_time_avg: float = 0.0
    update_frequency: float = 0.0
    content_freshness: float = 0.0
    
    # Bias and credibility
    political_bias_score: float = 0.0  # -1 (left) to 1 (right), 0 neutral
    sensationalism_score: float = 0.0  # 0-1, higher is more sensational
    fact_check_rating: float = 0.0  # Based on external fact-checkers
    
    # Volume and consistency
    articles_per_day: float = 0.0
    consistency_score: float = 0.0
    duplicate_content_ratio: float = 0.0
    
    # External validation
    citation_count: int = 0
    social_media_engagement: float = 0.0
    expert_endorsements: int = 0
    
    # Overall scores
    reliability_score: float = 0.0
    confidence_interval: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    
    # Metadata
    last_evaluated: datetime = field(default_factory=datetime.now)
    evaluation_count: int = 0
    active_since: Optional[datetime] = None

@dataclass
class SourceValidationResult:
    """Result of source validation check."""
    source_id: str
    is_valid: bool
    issues: List[str]
    recommendations: List[str]
    risk_level: str
    last_check: datetime = field(default_factory=datetime.now)

class SourceReliabilityScorer:
    """System for scoring and evaluating news source reliability."""
    
    def __init__(self, db_path: str = "data/source_reliability.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
        
        # Known high-quality sources (baseline)
        self.trusted_sources = {
            'bbc.com': 0.95,
            'reuters.com': 0.95,
            'ap.org': 0.94,
            'cnn.com': 0.85,
            'theguardian.com': 0.88,
            'ft.com': 0.92,
            'economist.com': 0.93,
            'washingtonpost.com': 0.87,
            'nytimes.com': 0.89,
            'wsj.com': 0.91,
            'dw.com': 0.90,
            'france24.com': 0.87,
            'aljazeera.com': 0.83
        }
        
        # Known problematic source indicators
        self.risk_indicators = {
            'domain_patterns': [
                r'\.tk$', r'\.ml$', r'\.ga$',  # Free domains
                r'news[0-9]+\.', r'breaking.*news',  # Suspicious patterns
                r'realtruth', r'patriot', r'freedom'  # Bias indicators
            ],
            'content_patterns': [
                r'BREAKING:.*!{2,}',  # Excessive punctuation
                r'SHOCKING.*TRUTH',  # Sensational language
                r'MUST READ.*NOW',  # Urgency manipulation
                r'[A-Z]{10,}',  # Excessive capitalization
            ],
            'suspicious_keywords': [
                'fake news', 'mainstream media lies', 'they don\'t want you to know',
                'hidden truth', 'establishment cover-up', 'wake up sheeple'
            ]
        }
        
        # Factual accuracy databases (simulated)
        self.fact_check_sources = {
            'snopes.com': 0.95,
            'factcheck.org': 0.93,
            'politifact.com': 0.91,
            'factcheckeu.info': 0.89,
            'fullfact.org': 0.92
        }
    
    def init_database(self):
        """Initialize source reliability database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS source_metrics (
                    source_id TEXT PRIMARY KEY,
                    source_name TEXT,
                    country TEXT,
                    language TEXT,
                    domain TEXT,
                    content_quality_score REAL DEFAULT 0.0,
                    factual_accuracy_score REAL DEFAULT 0.0,
                    editorial_standards_score REAL DEFAULT 0.0,
                    transparency_score REAL DEFAULT 0.0,
                    uptime_percentage REAL DEFAULT 0.0,
                    response_time_avg REAL DEFAULT 0.0,
                    update_frequency REAL DEFAULT 0.0,
                    content_freshness REAL DEFAULT 0.0,
                    political_bias_score REAL DEFAULT 0.0,
                    sensationalism_score REAL DEFAULT 0.0,
                    fact_check_rating REAL DEFAULT 0.0,
                    articles_per_day REAL DEFAULT 0.0,
                    consistency_score REAL DEFAULT 0.0,
                    duplicate_content_ratio REAL DEFAULT 0.0,
                    citation_count INTEGER DEFAULT 0,
                    social_media_engagement REAL DEFAULT 0.0,
                    expert_endorsements INTEGER DEFAULT 0,
                    reliability_score REAL DEFAULT 0.0,
                    confidence_min REAL DEFAULT 0.0,
                    confidence_max REAL DEFAULT 0.0,
                    last_evaluated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    evaluation_count INTEGER DEFAULT 0,
                    active_since TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS source_validations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT,
                    is_valid BOOLEAN,
                    issues TEXT,
                    recommendations TEXT,
                    risk_level TEXT,
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES source_metrics (source_id)
                );
                
                CREATE TABLE IF NOT EXISTS reliability_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT,
                    reliability_score REAL,
                    evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    evaluation_reason TEXT,
                    FOREIGN KEY (source_id) REFERENCES source_metrics (source_id)
                );
                
                CREATE TABLE IF NOT EXISTS content_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT,
                    article_hash TEXT,
                    sentiment_score REAL,
                    readability_score REAL,
                    bias_indicators TEXT,
                    quality_flags TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_reliability_score ON source_metrics(reliability_score);
                CREATE INDEX IF NOT EXISTS idx_source_domain ON source_metrics(domain);
                CREATE INDEX IF NOT EXISTS idx_evaluation_date ON reliability_history(evaluation_date);
            """)
    
    def evaluate_source(self, source_info: Dict[str, Any], article_samples: List[Dict[str, Any]] = None) -> SourceReliabilityMetrics:
        """Evaluate the reliability of a news source."""
        source_id = self._generate_source_id(source_info)
        domain = self._extract_domain(source_info.get('rss', '') or source_info.get('url', ''))
        
        # Initialize metrics
        metrics = SourceReliabilityMetrics(
            source_id=source_id,
            source_name=source_info.get('name', ''),
            country=source_info.get('country', ''),
            language=source_info.get('language', 'unknown'),
            domain=domain
        )
        
        # Evaluate different aspects
        metrics.content_quality_score = self._evaluate_content_quality(source_info, article_samples)
        metrics.factual_accuracy_score = self._evaluate_factual_accuracy(source_info, domain)
        metrics.editorial_standards_score = self._evaluate_editorial_standards(source_info, domain)
        metrics.transparency_score = self._evaluate_transparency(source_info, domain)
        
        metrics.political_bias_score = self._assess_political_bias(source_info, article_samples)
        metrics.sensationalism_score = self._assess_sensationalism(source_info, article_samples)
        
        # Performance metrics (would require historical data)
        metrics.uptime_percentage = self._estimate_uptime(source_info)
        metrics.update_frequency = self._estimate_update_frequency(source_info)
        
        # Calculate overall reliability score
        metrics.reliability_score = self._calculate_overall_reliability(metrics)
        metrics.confidence_interval = self._calculate_confidence_interval(metrics)
        
        # Store in database
        self._store_source_metrics(metrics)
        
        return metrics
    
    def _generate_source_id(self, source_info: Dict[str, Any]) -> str:
        """Generate unique source identifier."""
        name = source_info.get('name', '')
        domain = self._extract_domain(source_info.get('rss', '') or source_info.get('url', ''))
        country = source_info.get('country', '')
        
        unique_string = f"{name}_{domain}_{country}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        import urllib.parse
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc.lower()
        except:
            return 'unknown'
    
    def _evaluate_content_quality(self, source_info: Dict[str, Any], article_samples: List[Dict[str, Any]]) -> float:
        """Evaluate content quality based on various factors."""
        score = 0.5  # Base score
        
        # Check if it's a known high-quality source
        domain = self._extract_domain(source_info.get('rss', '') or source_info.get('url', ''))
        if domain in self.trusted_sources:
            score = self.trusted_sources[domain] * 0.8  # 80% weight for known sources
        
        # Analyze article samples if available
        if article_samples:
            content_scores = []
            for article in article_samples:
                article_score = self._analyze_article_quality(article)
                content_scores.append(article_score)
            
            if content_scores:
                avg_content_score = sum(content_scores) / len(content_scores)
                score = (score + avg_content_score) / 2  # Average with base score
        
        # Priority bonus (from our enhanced collector)
        priority = source_info.get('priority', 'low')
        if priority == 'critical':
            score += 0.1
        elif priority == 'high':
            score += 0.05
        
        return min(1.0, max(0.0, score))
    
    def _analyze_article_quality(self, article: Dict[str, Any]) -> float:
        """Analyze quality of individual article."""
        score = 0.5
        
        title = article.get('title', '')
        content = article.get('description', '') or article.get('summary', '')
        
        # Length indicators
        if len(content) > 500:
            score += 0.1
        if len(content) > 1000:
            score += 0.1
        
        # Check for sensational patterns
        sensational_patterns = [
            r'BREAKING:.*!{2,}',
            r'SHOCKING.*TRUTH',
            r'YOU WON\'T BELIEVE',
            r'[A-Z]{10,}'  # Excessive caps
        ]
        
        text = f"{title} {content}".upper()
        for pattern in sensational_patterns:
            if re.search(pattern, text):
                score -= 0.1
        
        # Grammar and readability (simplified)
        sentences = content.split('.')
        if len(sentences) > 3:  # Multiple sentences indicate structure
            score += 0.05
        
        # Check for citations or quotes
        if '"' in content or 'according to' in content.lower():
            score += 0.05
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_factual_accuracy(self, source_info: Dict[str, Any], domain: str) -> float:
        """Evaluate factual accuracy based on external ratings."""
        # Check against known fact-checkers (simulated)
        if domain in self.trusted_sources:
            return self.trusted_sources[domain]
        
        # Check for risk indicators
        score = 0.7  # Default score
        
        for pattern in self.risk_indicators['domain_patterns']:
            if re.search(pattern, domain):
                score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_editorial_standards(self, source_info: Dict[str, Any], domain: str) -> float:
        """Evaluate editorial standards."""
        score = 0.6  # Base score
        
        # International sources often have higher standards
        if source_info.get('country') in ['GB', 'US', 'DE', 'FR', 'CA', 'AU']:
            score += 0.1
        
        # Check source name for quality indicators
        name = source_info.get('name', '').lower()
        quality_indicators = ['times', 'post', 'guardian', 'herald', 'tribune', 'journal']
        if any(indicator in name for indicator in quality_indicators):
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_transparency(self, source_info: Dict[str, Any], domain: str) -> float:
        """Evaluate transparency and disclosure."""
        score = 0.5
        
        # Well-known domains are generally more transparent
        if domain in self.trusted_sources:
            score = 0.8
        
        # Check for government or official sources
        if '.gov' in domain or 'official' in source_info.get('name', '').lower():
            score += 0.2
        
        return min(1.0, max(0.0, score))
    
    def _assess_political_bias(self, source_info: Dict[str, Any], article_samples: List[Dict[str, Any]]) -> float:
        """Assess political bias (0 = neutral, -1 = left, +1 = right)."""
        # This would require sophisticated analysis
        # For now, return neutral for most sources
        return 0.0
    
    def _assess_sensationalism(self, source_info: Dict[str, Any], article_samples: List[Dict[str, Any]]) -> float:
        """Assess sensationalism level."""
        if not article_samples:
            return 0.3  # Default low sensationalism
        
        sensational_count = 0
        total_articles = len(article_samples)
        
        for article in article_samples:
            title = article.get('title', '').upper()
            
            # Check for sensational patterns
            for pattern in self.risk_indicators['content_patterns']:
                if re.search(pattern, title):
                    sensational_count += 1
                    break
        
        return sensational_count / total_articles if total_articles > 0 else 0.0
    
    def _estimate_uptime(self, source_info: Dict[str, Any]) -> float:
        """Estimate source uptime (simplified)."""
        # Known reliable sources
        domain = self._extract_domain(source_info.get('rss', '') or source_info.get('url', ''))
        if domain in self.trusted_sources:
            return 0.99
        
        return 0.95  # Default assumption
    
    def _estimate_update_frequency(self, source_info: Dict[str, Any]) -> float:
        """Estimate how frequently source updates."""
        # International news sources update more frequently
        if source_info.get('country') in ['US', 'GB', 'DE', 'FR']:
            return 0.8
        
        return 0.6  # Default
    
    def _calculate_overall_reliability(self, metrics: SourceReliabilityMetrics) -> float:
        """Calculate overall reliability score."""
        # Weighted average of different factors
        weights = {
            'content_quality': 0.25,
            'factual_accuracy': 0.25,
            'editorial_standards': 0.15,
            'transparency': 0.15,
            'sensationalism': -0.1,  # Negative weight
            'uptime': 0.1,
            'update_frequency': 0.1
        }
        
        score = (
            weights['content_quality'] * metrics.content_quality_score +
            weights['factual_accuracy'] * metrics.factual_accuracy_score +
            weights['editorial_standards'] * metrics.editorial_standards_score +
            weights['transparency'] * metrics.transparency_score +
            weights['sensationalism'] * (1 - metrics.sensationalism_score) +  # Invert sensationalism
            weights['uptime'] * metrics.uptime_percentage +
            weights['update_frequency'] * metrics.update_frequency
        )
        
        return min(1.0, max(0.0, score))
    
    def _calculate_confidence_interval(self, metrics: SourceReliabilityMetrics) -> Tuple[float, float]:
        """Calculate confidence interval for reliability score."""
        # Simplified confidence calculation
        base_score = metrics.reliability_score
        
        # Confidence depends on available data
        confidence_width = 0.1  # Default uncertainty
        
        if metrics.evaluation_count > 10:
            confidence_width = 0.05  # Higher confidence with more data
        
        return (
            max(0.0, base_score - confidence_width),
            min(1.0, base_score + confidence_width)
        )
    
    def _store_source_metrics(self, metrics: SourceReliabilityMetrics):
        """Store source metrics in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO source_metrics 
                (source_id, source_name, country, language, domain,
                 content_quality_score, factual_accuracy_score, editorial_standards_score,
                 transparency_score, uptime_percentage, response_time_avg, update_frequency,
                 content_freshness, political_bias_score, sensationalism_score,
                 fact_check_rating, articles_per_day, consistency_score,
                 duplicate_content_ratio, citation_count, social_media_engagement,
                 expert_endorsements, reliability_score, confidence_min, confidence_max,
                 last_evaluated, evaluation_count, active_since)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.source_id, metrics.source_name, metrics.country, metrics.language,
                metrics.domain, metrics.content_quality_score, metrics.factual_accuracy_score,
                metrics.editorial_standards_score, metrics.transparency_score,
                metrics.uptime_percentage, metrics.response_time_avg, metrics.update_frequency,
                metrics.content_freshness, metrics.political_bias_score, metrics.sensationalism_score,
                metrics.fact_check_rating, metrics.articles_per_day, metrics.consistency_score,
                metrics.duplicate_content_ratio, metrics.citation_count, metrics.social_media_engagement,
                metrics.expert_endorsements, metrics.reliability_score,
                metrics.confidence_interval[0], metrics.confidence_interval[1],
                metrics.last_evaluated, metrics.evaluation_count, metrics.active_since
            ))
            
            # Store in history
            conn.execute("""
                INSERT INTO reliability_history 
                (source_id, reliability_score, evaluation_reason)
                VALUES (?, ?, ?)
            """, (metrics.source_id, metrics.reliability_score, 'full_evaluation'))
    
    def validate_source(self, source_info: Dict[str, Any]) -> SourceValidationResult:
        """Validate source for potential issues."""
        source_id = self._generate_source_id(source_info)
        issues = []
        recommendations = []
        
        # Check domain
        domain = self._extract_domain(source_info.get('rss', '') or source_info.get('url', ''))
        
        # Domain validation
        for pattern in self.risk_indicators['domain_patterns']:
            if re.search(pattern, domain):
                issues.append(f"Suspicious domain pattern: {domain}")
                recommendations.append("Verify domain legitimacy")
        
        # Content validation
        name = source_info.get('name', '')
        for keyword in self.risk_indicators['suspicious_keywords']:
            if keyword.lower() in name.lower():
                issues.append(f"Suspicious content indicator: {keyword}")
                recommendations.append("Review content for bias or misinformation")
        
        # RSS feed validation
        rss_url = source_info.get('rss', '')
        if not rss_url:
            issues.append("No RSS feed provided")
            recommendations.append("Add RSS feed for automated collection")
        elif not rss_url.startswith(('http://', 'https://')):
            issues.append("Invalid RSS URL format")
            recommendations.append("Ensure RSS URL is properly formatted")
        
        # Determine risk level
        if len(issues) == 0:
            risk_level = "low"
        elif len(issues) <= 2:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        is_valid = risk_level != "high"
        
        result = SourceValidationResult(
            source_id=source_id,
            is_valid=is_valid,
            issues=issues,
            recommendations=recommendations,
            risk_level=risk_level
        )
        
        # Store validation result
        self._store_validation_result(result)
        
        return result
    
    def _store_validation_result(self, result: SourceValidationResult):
        """Store validation result in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO source_validations 
                (source_id, is_valid, issues, recommendations, risk_level)
                VALUES (?, ?, ?, ?, ?)
            """, (
                result.source_id,
                result.is_valid,
                json.dumps(result.issues),
                json.dumps(result.recommendations),
                result.risk_level
            ))
    
    def get_source_rankings(self, limit: int = 50, min_reliability: float = 0.5) -> List[Dict[str, Any]]:
        """Get ranked list of sources by reliability."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT source_id, source_name, domain, country, language,
                       reliability_score, confidence_min, confidence_max,
                       last_evaluated, evaluation_count
                FROM source_metrics 
                WHERE reliability_score >= ?
                ORDER BY reliability_score DESC, evaluation_count DESC
                LIMIT ?
            """, (min_reliability, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'source_id': row[0],
                    'name': row[1],
                    'domain': row[2],
                    'country': row[3],
                    'language': row[4],
                    'reliability_score': row[5],
                    'confidence_interval': (row[6], row[7]),
                    'last_evaluated': row[8],
                    'evaluation_count': row[9]
                })
            
            return results
    
    def get_reliability_report(self) -> Dict[str, Any]:
        """Generate comprehensive reliability report."""
        with sqlite3.connect(self.db_path) as conn:
            # Overall statistics
            total_sources = conn.execute("SELECT COUNT(*) FROM source_metrics").fetchone()[0]
            
            # Reliability distribution
            reliability_dist = conn.execute("""
                SELECT 
                    CASE 
                        WHEN reliability_score >= 0.8 THEN 'high'
                        WHEN reliability_score >= 0.6 THEN 'medium'
                        ELSE 'low'
                    END as category,
                    COUNT(*) as count
                FROM source_metrics
                GROUP BY category
            """).fetchall()
            
            # Top sources
            top_sources = conn.execute("""
                SELECT source_name, domain, reliability_score, country
                FROM source_metrics
                ORDER BY reliability_score DESC
                LIMIT 10
            """).fetchall()
            
            # Risk summary
            risk_summary = conn.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM source_validations
                GROUP BY risk_level
            """).fetchall()
            
            return {
                'total_sources_evaluated': total_sources,
                'reliability_distribution': dict(reliability_dist),
                'top_sources': [
                    {
                        'name': row[0],
                        'domain': row[1],
                        'score': row[2],
                        'country': row[3]
                    }
                    for row in top_sources
                ],
                'risk_distribution': dict(risk_summary),
                'generated_at': datetime.now().isoformat()
            }

# Example usage
if __name__ == "__main__":
    scorer = SourceReliabilityScorer()
    
    # Test source evaluation
    test_source = {
        'name': 'BBC World',
        'rss': 'http://feeds.bbci.co.uk/news/world/rss.xml',
        'country': 'GB',
        'language': 'en',
        'priority': 'critical'
    }
    
    metrics = scorer.evaluate_source(test_source)
    print(f"Reliability score for {test_source['name']}: {metrics.reliability_score:.3f}")
    
    validation = scorer.validate_source(test_source)
    print(f"Validation result: {validation.is_valid}, Risk: {validation.risk_level}")
    
    report = scorer.get_reliability_report()
    print(f"Reliability report: {json.dumps(report, indent=2)}")
