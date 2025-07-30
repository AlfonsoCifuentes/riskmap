"""
Enhanced Geopolitical Intelligence Orchestrator
Integrates all AI components for comprehensive conflict monitoring,
analysis, and reporting with real-time capabilities.
"""

import logging
import asyncio
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path

# Import enhanced AI components
from src.ai.enhanced_models import (
    MultilingualNERProcessor, ConflictClassifier, ActorRelationshipMapper
)
from src.cv.vision_analyzer import ConflictVisionAnalyzer
from src.analytics.advanced_analytics import (
    ConflictTrendPredictor, AnomalyDetector, PatternAnalyzer, SentimentTrendAnalyzer
)
from src.alerts.enhanced_alerts import (
    ThreatScorer, AlertGenerator, NotificationManager, RealTimeMonitor,
    Alert, AlertSeverity, AlertType
)
from src.reporting.executive_reports import ExecutiveReportGenerator

# Import existing components
from src.utils.config import logger
from src.data_ingestion.rss_collector import RSSCollector
from src.nlp_processing.text_analyzer import TextAnalyzer

class EnhancedGeopoliticalOrchestrator:
    """
    Enhanced orchestrator that coordinates all AI-powered conflict monitoring
    and analysis components for professional geopolitical intelligence
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize AI components
        self.ner_processor = None
        self.conflict_classifier = None
        self.actor_mapper = None
        self.vision_analyzer = None
        self.trend_predictor = None
        self.anomaly_detector = None
        self.pattern_analyzer = None
        self.sentiment_analyzer = None
        
        # Initialize alert system
        self.threat_scorer = None
        self.alert_generator = None
        self.notification_manager = None
        self.real_time_monitor = None
        
        # Initialize reporting
        self.report_generator = None
        
        # Initialize existing components
        self.rss_collector = None
        self.text_analyzer = None
        
        # Database connection
        self.db_path = "src/data/geopolitical_intelligence.db"
        
        # Initialize all components
        self._initialize_components()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _initialize_components(self):
        """Initialize all AI and analysis components"""
        try:
            logger.info("Initializing enhanced geopolitical intelligence system...")
            
            # Initialize AI models
            self.ner_processor = MultilingualNERProcessor()
            self.conflict_classifier = ConflictClassifier()
            self.actor_mapper = ActorRelationshipMapper()
            self.vision_analyzer = ConflictVisionAnalyzer()
            
            # Initialize analytics
            self.trend_predictor = ConflictTrendPredictor()
            self.anomaly_detector = AnomalyDetector()
            self.pattern_analyzer = PatternAnalyzer()
            self.sentiment_analyzer = SentimentTrendAnalyzer()
            
            # Initialize alert system
            self.threat_scorer = ThreatScorer()
            self.alert_generator = AlertGenerator(self.threat_scorer)
            
            # Initialize notification manager
            notification_config = self.config.get('notifications', {})
            self.notification_manager = NotificationManager(notification_config)
            
            # Initialize real-time monitor
            self.real_time_monitor = RealTimeMonitor(
                self.alert_generator, 
                self.notification_manager
            )
            
            # Initialize report generator
            self.report_generator = ExecutiveReportGenerator()
            
            # Initialize existing components
            self.rss_collector = RSSCollector()
            self.text_analyzer = TextAnalyzer()
            
            logger.info("Enhanced geopolitical intelligence system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def run_comprehensive_analysis(self, 
                                 include_data_collection: bool = True,
                                 include_vision_analysis: bool = False,
                                 generate_reports: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive geopolitical intelligence analysis
        
        Args:
            include_data_collection: Whether to collect new data
            include_vision_analysis: Whether to analyze visual content
            generate_reports: Whether to generate executive reports
            
        Returns:
            Comprehensive analysis results
        """
        try:
            logger.info("Starting comprehensive geopolitical intelligence analysis...")
            
            analysis_results = {
                'analysis_timestamp': datetime.now().isoformat(),
                'data_collection': {},
                'nlp_analysis': {},
                'vision_analysis': {},
                'trend_analysis': {},
                'anomaly_detection': {},
                'pattern_analysis': {},
                'sentiment_analysis': {},
                'alerts_generated': [],
                'reports_generated': {},
                'summary': {}
            }
            
            # Step 1: Data Collection
            if include_data_collection:
                logger.info("Collecting latest conflict data...")
                collection_results = self._collect_conflict_data()
                analysis_results['data_collection'] = collection_results
            
            # Step 2: Load recent data for analysis
            recent_data = self._load_recent_data(days=7)
            
            # Step 3: NLP Analysis
            logger.info("Performing advanced NLP analysis...")
            nlp_results = self._perform_nlp_analysis(recent_data)
            analysis_results['nlp_analysis'] = nlp_results
            
            # Step 4: Vision Analysis (if enabled)
            if include_vision_analysis:
                logger.info("Performing computer vision analysis...")
                vision_results = self._perform_vision_analysis(recent_data)
                analysis_results['vision_analysis'] = vision_results
            
            # Step 5: Trend Prediction
            logger.info("Analyzing trends and predicting future developments...")
            trend_results = self._perform_trend_analysis(recent_data)
            analysis_results['trend_analysis'] = trend_results
            
            # Step 6: Anomaly Detection
            logger.info("Detecting anomalies and unusual patterns...")
            anomaly_results = self._perform_anomaly_detection(recent_data)
            analysis_results['anomaly_detection'] = anomaly_results
            
            # Step 7: Pattern Analysis
            logger.info("Analyzing conflict patterns...")
            pattern_results = self._perform_pattern_analysis(recent_data)
            analysis_results['pattern_analysis'] = pattern_results
            
            # Step 8: Sentiment Analysis
            logger.info("Analyzing sentiment trends...")
            sentiment_results = self._perform_sentiment_analysis(recent_data)
            analysis_results['sentiment_analysis'] = sentiment_results
            
            # Step 9: Alert Generation
            logger.info("Generating alerts based on analysis...")
            alerts = self._generate_alerts(analysis_results)
            analysis_results['alerts_generated'] = alerts
            
            # Step 10: Report Generation
            if generate_reports:
                logger.info("Generating executive reports...")
                reports = self._generate_executive_reports(analysis_results)
                analysis_results['reports_generated'] = reports
            
            # Step 11: Generate Summary
            analysis_results['summary'] = self._generate_analysis_summary(analysis_results)
            
            logger.info("Comprehensive analysis completed successfully")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': str(e)}
    
    def _collect_conflict_data(self) -> Dict[str, Any]:
        """Collect latest conflict data from multiple sources"""
        try:
            collection_results = {
                'sources_processed': 0,
                'articles_collected': 0,
                'errors': []
            }
            
            # Use existing RSS collector
            if self.rss_collector:
                try:
                    rss_results = self.rss_collector.collect_all_sources()
                    collection_results['articles_collected'] += rss_results.get('total_articles', 0)
                    collection_results['sources_processed'] += rss_results.get('sources_processed', 0)
                except Exception as e:
                    collection_results['errors'].append(f"RSS collection error: {str(e)}")
            
            return collection_results
            
        except Exception as e:
            logger.error(f"Error collecting conflict data: {e}")
            return {'error': str(e)}
    
    def _load_recent_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """Load recent conflict data from database"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                SELECT * FROM articles 
                WHERE timestamp >= ? 
                AND processed = 1
                ORDER BY timestamp DESC
                """
                
                cursor.execute(query, (cutoff_date.isoformat(),))
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error loading recent data: {e}")
            return []
    
    def _perform_nlp_analysis(self, data: List[Dict]) -> Dict[str, Any]:
        """Perform comprehensive NLP analysis on conflict data"""
        try:
            nlp_results = {
                'total_articles_analyzed': len(data),
                'entities_extracted': {},
                'conflict_classifications': {},
                'actor_relationships': [],
                'processing_errors': 0
            }
            
            all_entities = []
            all_classifications = []
            all_relationships = []
            
            for article in data:
                try:
                    text = article.get('content', '') or article.get('title', '')
                    if not text:
                        continue
                    
                    # Extract entities
                    entities = self.ner_processor.extract_entities(text)
                    all_entities.append(entities)
                    
                    # Classify conflict
                    conflict_type = self.conflict_classifier.classify_conflict_type(text)
                    intensity = self.conflict_classifier.analyze_intensity(text)
                    humanitarian = self.conflict_classifier.analyze_humanitarian_impact(text)
                    sentiment = self.conflict_classifier.analyze_sentiment(text)
                    
                    classification = {
                        'article_id': article.get('id'),
                        'conflict_type': conflict_type,
                        'intensity': intensity,
                        'humanitarian_impact': humanitarian,
                        'sentiment': sentiment
                    }
                    all_classifications.append(classification)
                    
                    # Extract actor relationships
                    relationships = self.actor_mapper.extract_relationships(text, entities)
                    all_relationships.extend(relationships)
                    
                except Exception as e:
                    nlp_results['processing_errors'] += 1
                    logger.warning(f"Error processing article {article.get('id', 'unknown')}: {e}")
            
            # Aggregate results
            nlp_results['entities_extracted'] = self._aggregate_entities(all_entities)
            nlp_results['conflict_classifications'] = self._aggregate_classifications(all_classifications)
            nlp_results['actor_relationships'] = all_relationships
            
            return nlp_results
            
        except Exception as e:
            logger.error(f"Error in NLP analysis: {e}")
            return {'error': str(e)}
    
    def _perform_vision_analysis(self, data: List[Dict]) -> Dict[str, Any]:
        """Perform computer vision analysis on available imagery"""
        try:
            vision_results = {
                'images_analyzed': 0,
                'damage_assessments': [],
                'military_detections': [],
                'crowd_analyses': [],
                'satellite_analyses': []
            }
            
            # Look for image URLs or paths in the data
            for article in data:
                image_urls = article.get('image_urls', [])
                
                for image_url in image_urls:
                    try:
                        # Analyze image
                        analysis = self.vision_analyzer.analyze_image(image_url, 'comprehensive')
                        
                        if 'error' not in analysis:
                            vision_results['images_analyzed'] += 1
                            
                            # Categorize results
                            if analysis.get('detections', {}).get('damage'):
                                vision_results['damage_assessments'].append({
                                    'article_id': article.get('id'),
                                    'image_url': image_url,
                                    'analysis': analysis['detections']['damage']
                                })
                            
                            if analysis.get('detections', {}).get('military'):
                                vision_results['military_detections'].append({
                                    'article_id': article.get('id'),
                                    'image_url': image_url,
                                    'analysis': analysis['detections']['military']
                                })
                            
                            if analysis.get('detections', {}).get('crowd'):
                                vision_results['crowd_analyses'].append({
                                    'article_id': article.get('id'),
                                    'image_url': image_url,
                                    'analysis': analysis['detections']['crowd']
                                })
                    
                    except Exception as e:
                        logger.warning(f"Error analyzing image {image_url}: {e}")
            
            return vision_results
            
        except Exception as e:
            logger.error(f"Error in vision analysis: {e}")
            return {'error': str(e)}
    
    def _perform_trend_analysis(self, data: List[Dict]) -> Dict[str, Any]:
        """Perform trend analysis and prediction"""
        try:
            # Convert data to DataFrame for analysis
            import pandas as pd
            
            df_data = []
            for article in data:
                df_data.append({
                    'timestamp': article.get('timestamp'),
                    'risk_score': article.get('risk_score', 0),
                    'conflict_intensity': article.get('conflict_intensity', 0),
                    'humanitarian_impact': article.get('humanitarian_impact', 0),
                    'region': article.get('region', 'Unknown')
                })
            
            df = pd.DataFrame(df_data)
            
            if len(df) < 10:
                return {'error': 'Insufficient data for trend analysis'}
            
            # Prepare time series data
            ts_data = self.trend_predictor.prepare_time_series_data(df)
            
            trend_results = {}
            
            # Train models if enough data
            if len(ts_data) >= 30:
                # Train LSTM model
                lstm_results = self.trend_predictor.train_lstm_model(ts_data)
                trend_results['lstm_training'] = lstm_results
                
                # Train Prophet model
                prophet_results = self.trend_predictor.train_prophet_model(ts_data)
                trend_results['prophet_training'] = prophet_results
                
                # Generate predictions
                predictions = self.trend_predictor.predict_future_trends(periods=30)
                trend_results['predictions'] = predictions
            else:
                trend_results['note'] = 'Insufficient data for model training'
            
            return trend_results
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return {'error': str(e)}
    
    def _perform_anomaly_detection(self, data: List[Dict]) -> Dict[str, Any]:
        """Perform anomaly detection on conflict data"""
        try:
            import pandas as pd
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            if len(df) < 10:
                return {'error': 'Insufficient data for anomaly detection'}
            
            anomaly_results = {}
            
            # Isolation Forest detection
            isolation_results = self.anomaly_detector.detect_anomalies(df, 'isolation_forest')
            anomaly_results['isolation_forest'] = isolation_results
            
            # Clustering-based detection
            clustering_results = self.anomaly_detector.detect_anomalies(df, 'clustering')
            anomaly_results['clustering'] = clustering_results
            
            # Statistical detection
            statistical_results = self.anomaly_detector.detect_anomalies(df, 'statistical')
            anomaly_results['statistical'] = statistical_results
            
            return anomaly_results
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {'error': str(e)}
    
    def _perform_pattern_analysis(self, data: List[Dict]) -> Dict[str, Any]:
        """Perform pattern analysis on conflict data"""
        try:
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            if len(df) < 5:
                return {'error': 'Insufficient data for pattern analysis'}
            
            pattern_results = {}
            
            # Temporal patterns
            temporal_patterns = self.pattern_analyzer.identify_patterns(df, 'temporal')
            pattern_results['temporal'] = temporal_patterns
            
            # Spatial patterns (if coordinates available)
            if 'latitude' in df.columns and 'longitude' in df.columns:
                spatial_patterns = self.pattern_analyzer.identify_patterns(df, 'spatial')
                pattern_results['spatial'] = spatial_patterns
            
            # Actor patterns
            if 'actors' in df.columns:
                actor_patterns = self.pattern_analyzer.identify_patterns(df, 'actor')
                pattern_results['actor'] = actor_patterns
            
            return pattern_results
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
            return {'error': str(e)}
    
    def _perform_sentiment_analysis(self, data: List[Dict]) -> Dict[str, Any]:
        """Perform sentiment trend analysis"""
        try:
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            if 'sentiment_score' not in df.columns:
                # Calculate sentiment scores if not available
                for i, row in df.iterrows():
                    text = row.get('content', '') or row.get('title', '')
                    if text and self.conflict_classifier:
                        sentiment = self.conflict_classifier.analyze_sentiment(text)
                        df.at[i, 'sentiment_score'] = sentiment.get('confidence', 0) * (1 if sentiment.get('sentiment') == 'positive' else -1)
            
            sentiment_results = {}
            
            # Regional sentiment trends
            if 'region' in df.columns:
                regional_sentiment = self.sentiment_analyzer.analyze_sentiment_trends(df, 'region')
                sentiment_results['regional'] = regional_sentiment
            
            # Country sentiment trends
            if 'country' in df.columns:
                country_sentiment = self.sentiment_analyzer.analyze_sentiment_trends(df, 'country')
                sentiment_results['country'] = country_sentiment
            
            return sentiment_results
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {'error': str(e)}
    
    def _generate_alerts(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on analysis results"""
        try:
            alerts = []
            
            # Check for anomalies
            anomaly_data = analysis_results.get('anomaly_detection', {})
            for method, results in anomaly_data.items():
                if isinstance(results, dict) and results.get('anomalies'):
                    for anomaly in results['anomalies']:
                        event_data = {
                            'anomaly_score': anomaly.get('anomaly_score', 0),
                            'region': anomaly.get('data', {}).get('region', 'Unknown'),
                            'country': anomaly.get('data', {}).get('country'),
                            'timestamp': anomaly.get('timestamp', datetime.now().isoformat()),
                            'confidence': 0.8
                        }
                        
                        generated_alerts = self.alert_generator.analyze_and_generate_alerts(event_data)
                        alerts.extend([alert.to_dict() for alert in generated_alerts])
            
            # Check trend predictions
            trend_data = analysis_results.get('trend_analysis', {})
            predictions = trend_data.get('predictions', {})
            if predictions:
                trend_analysis = predictions.get('trend_analysis', {})
                if trend_analysis.get('direction') == 'escalating':
                    event_data = {
                        'conflict_intensity': 0.8,
                        'region': 'Multiple',
                        'timestamp': datetime.now().isoformat(),
                        'confidence': 0.9,
                        'trend_direction': 'escalating'
                    }
                    
                    generated_alerts = self.alert_generator.analyze_and_generate_alerts(event_data)
                    alerts.extend([alert.to_dict() for alert in generated_alerts])
            
            # Check sentiment shifts
            sentiment_data = analysis_results.get('sentiment_analysis', {})
            for region_type, sentiment_results in sentiment_data.items():
                if isinstance(sentiment_results, dict):
                    alerts_list = sentiment_results.get('alerts', [])
                    for alert_info in alerts_list:
                        if alert_info.get('type') == 'negative_sentiment_spike':
                            event_data = {
                                'sentiment_change': alert_info.get('change', 0),
                                'region': alert_info.get('group', 'Unknown'),
                                'timestamp': datetime.now().isoformat(),
                                'confidence': 0.7
                            }
                            
                            generated_alerts = self.alert_generator.analyze_and_generate_alerts(event_data)
                            alerts.extend([alert.to_dict() for alert in generated_alerts])
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            return []
    
    def _generate_executive_reports(self, analysis_results: Dict[str, Any]) -> Dict[str, str]:
        """Generate executive reports based on analysis"""
        try:
            # Prepare report data
            report_data = {
                'period_start': datetime.now() - timedelta(days=7),
                'period_end': datetime.now(),
                'conflicts': analysis_results.get('nlp_analysis', {}).get('conflict_classifications', []),
                'alerts': analysis_results.get('alerts_generated', []),
                'trends': analysis_results.get('trend_analysis', {}),
                'anomalies': analysis_results.get('anomaly_detection', {}),
                'sentiment': analysis_results.get('sentiment_analysis', {})
            }
            
            # Generate reports
            reports = self.report_generator.generate_executive_report(
                data=report_data,
                report_type='comprehensive',
                format_types=['html', 'json']
            )
            
            return reports
            
        except Exception as e:
            logger.error(f"Error generating executive reports: {e}")
            return {}
    
    def _generate_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of the comprehensive analysis"""
        try:
            summary = {
                'analysis_completion_time': datetime.now().isoformat(),
                'data_processed': {
                    'articles_collected': analysis_results.get('data_collection', {}).get('articles_collected', 0),
                    'articles_analyzed': analysis_results.get('nlp_analysis', {}).get('total_articles_analyzed', 0),
                    'images_analyzed': analysis_results.get('vision_analysis', {}).get('images_analyzed', 0)
                },
                'key_findings': [],
                'threat_level': 'unknown',
                'alerts_generated': len(analysis_results.get('alerts_generated', [])),
                'reports_generated': len(analysis_results.get('reports_generated', {})),
                'recommendations': []
            }
            
            # Extract key findings
            nlp_data = analysis_results.get('nlp_analysis', {})
            if nlp_data.get('entities_extracted'):
                entities = nlp_data['entities_extracted']
                total_entities = sum(len(entity_list) for entity_list in entities.values())
                summary['key_findings'].append(f"Extracted {total_entities} entities from conflict reports")
            
            # Anomaly findings
            anomaly_data = analysis_results.get('anomaly_detection', {})
            total_anomalies = 0
            for method_results in anomaly_data.values():
                if isinstance(method_results, dict):
                    total_anomalies += len(method_results.get('anomalies', []))
            
            if total_anomalies > 0:
                summary['key_findings'].append(f"Detected {total_anomalies} anomalous patterns requiring attention")
            
            # Trend findings
            trend_data = analysis_results.get('trend_analysis', {})
            predictions = trend_data.get('predictions', {})
            if predictions:
                trend_direction = predictions.get('trend_analysis', {}).get('direction', 'stable')
                summary['key_findings'].append(f"Conflict trends are {trend_direction}")
            
            # Determine overall threat level
            alerts = analysis_results.get('alerts_generated', [])
            critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
            high_alerts = [a for a in alerts if a.get('severity') == 'high']
            
            if critical_alerts:
                summary['threat_level'] = 'critical'
            elif high_alerts:
                summary['threat_level'] = 'high'
            elif alerts:
                summary['threat_level'] = 'medium'
            else:
                summary['threat_level'] = 'low'
            
            # Generate recommendations
            if summary['threat_level'] in ['critical', 'high']:
                summary['recommendations'].append("Increase monitoring frequency and prepare response protocols")
            
            if total_anomalies > 5:
                summary['recommendations'].append("Investigate detected anomalies for potential emerging threats")
            
            if trend_direction == 'escalating':
                summary['recommendations'].append("Implement de-escalation measures and diplomatic interventions")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
            return {'error': str(e)}
    
    def start_real_time_monitoring(self):
        """Start real-time monitoring system"""
        try:
            logger.info("Starting real-time geopolitical monitoring...")
            self.real_time_monitor.start_monitoring()
            return {'status': 'monitoring_started', 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Error starting real-time monitoring: {e}")
            return {'error': str(e)}
    
    def stop_real_time_monitoring(self):
        """Stop real-time monitoring system"""
        try:
            self.real_time_monitor.stop_monitoring()
            return {'status': 'monitoring_stopped', 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Error stopping real-time monitoring: {e}")
            return {'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'ner_processor': self.ner_processor is not None,
                    'conflict_classifier': self.conflict_classifier is not None,
                    'vision_analyzer': self.vision_analyzer is not None,
                    'trend_predictor': self.trend_predictor is not None,
                    'anomaly_detector': self.anomaly_detector is not None,
                    'alert_system': self.alert_generator is not None,
                    'real_time_monitor': self.real_time_monitor is not None,
                    'report_generator': self.report_generator is not None
                },
                'monitoring_active': self.real_time_monitor.monitoring_active if self.real_time_monitor else False,
                'database_status': self._check_database_status(),
                'recent_activity': self._get_recent_activity()
            }
            
            # Get alert statistics
            if self.real_time_monitor:
                alert_stats = self.real_time_monitor.get_alert_statistics()
                status['alert_statistics'] = alert_stats
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def _check_database_status(self) -> Dict[str, Any]:
        """Check database connectivity and basic statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get article count
                if 'articles' in tables:
                    cursor.execute("SELECT COUNT(*) FROM articles")
                    article_count = cursor.fetchone()[0]
                else:
                    article_count = 0
                
                return {
                    'connected': True,
                    'tables': tables,
                    'article_count': article_count
                }
                
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    def _get_recent_activity(self) -> Dict[str, Any]:
        """Get recent system activity"""
        try:
            recent_data = self._load_recent_data(days=1)
            
            return {
                'articles_last_24h': len(recent_data),
                'last_article_time': recent_data[0].get('timestamp') if recent_data else None
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _aggregate_entities(self, entity_lists: List[Dict]) -> Dict[str, List]:
        """Aggregate entities from multiple extractions"""
        aggregated = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'countries': [],
            'armed_groups': []
        }
        
        for entities in entity_lists:
            for category, entity_list in entities.items():
                if category in aggregated:
                    aggregated[category].extend(entity_list)
        
        # Remove duplicates while preserving order
        for category in aggregated:
            seen = set()
            unique_entities = []
            for entity in aggregated[category]:
                entity_text = entity.get('text', '').lower()
                if entity_text not in seen:
                    seen.add(entity_text)
                    unique_entities.append(entity)
            aggregated[category] = unique_entities
        
        return aggregated
    
    def _aggregate_classifications(self, classifications: List[Dict]) -> Dict[str, Any]:
        """Aggregate conflict classifications"""
        if not classifications:
            return {}
        
        # Count conflict types
        conflict_types = {}
        intensity_levels = {}
        humanitarian_impacts = {}
        
        for classification in classifications:
            # Conflict type
            conflict_type = classification.get('conflict_type', {}).get('primary_type', 'unknown')
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
            
            # Intensity level
            intensity = classification.get('intensity', {}).get('intensity_level', 'unknown')
            intensity_levels[intensity] = intensity_levels.get(intensity, 0) + 1
            
            # Humanitarian impact
            impact = classification.get('humanitarian_impact', {}).get('primary_impact', 'unknown')
            humanitarian_impacts[impact] = humanitarian_impacts.get(impact, 0) + 1
        
        return {
            'total_classifications': len(classifications),
            'conflict_type_distribution': conflict_types,
            'intensity_distribution': intensity_levels,
            'humanitarian_impact_distribution': humanitarian_impacts
        }