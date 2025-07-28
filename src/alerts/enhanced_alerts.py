"""
Enhanced Early Warning Alert System
Implements real-time monitoring, multi-criteria threat scoring,
and configurable alert generation with multiple notification channels.
"""

import logging
import json
import smtplib
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
import time
import requests

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types of alerts"""
    CONFLICT_ESCALATION = "conflict_escalation"
    NEW_ACTOR_DETECTED = "new_actor_detected"
    HUMANITARIAN_CRISIS = "humanitarian_crisis"
    ANOMALY_DETECTED = "anomaly_detected"
    SENTIMENT_SHIFT = "sentiment_shift"
    PATTERN_CHANGE = "pattern_change"
    THREAT_LEVEL_CHANGE = "threat_level_change"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    region: str
    country: Optional[str]
    actors: List[str]
    confidence_score: float
    threat_score: float
    timestamp: datetime
    source_data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

class ThreatScorer:
    """
    Multi-criteria threat scoring system using ML models
    and configurable rules
    """
    
    def __init__(self):
        self.scoring_weights = {
            'conflict_intensity': 0.25,
            'humanitarian_impact': 0.20,
            'actor_involvement': 0.15,
            'geographical_spread': 0.10,
            'temporal_urgency': 0.15,
            'sentiment_negativity': 0.10,
            'anomaly_strength': 0.05
        }
        self.threshold_config = {
            AlertSeverity.LOW: 30,
            AlertSeverity.MEDIUM: 50,
            AlertSeverity.HIGH: 70,
            AlertSeverity.CRITICAL: 85
        }
    
    def calculate_threat_score(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive threat score for an event
        
        Args:
            event_data: Event data with various metrics
            
        Returns:
            Threat scoring results
        """
        try:
            scores = {}
            total_score = 0
            
            # Conflict intensity score
            intensity = event_data.get('conflict_intensity', 0)
            scores['conflict_intensity'] = min(intensity * 20, 100)  # Scale to 0-100
            
            # Humanitarian impact score
            casualties = event_data.get('casualties', 0)
            displaced = event_data.get('displaced_people', 0)
            humanitarian_score = min((casualties * 0.1 + displaced * 0.01), 100)
            scores['humanitarian_impact'] = humanitarian_score
            
            # Actor involvement score
            actors = event_data.get('actors', [])
            high_risk_actors = event_data.get('high_risk_actors', [])
            actor_score = len(actors) * 5 + len(high_risk_actors) * 15
            scores['actor_involvement'] = min(actor_score, 100)
            
            # Geographical spread score
            affected_regions = event_data.get('affected_regions', [])
            geo_score = len(affected_regions) * 20
            scores['geographical_spread'] = min(geo_score, 100)
            
            # Temporal urgency score
            event_time = event_data.get('timestamp', datetime.now())
            if isinstance(event_time, str):
                event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
            
            time_diff = (datetime.now() - event_time).total_seconds() / 3600  # Hours
            urgency_score = max(100 - time_diff * 2, 0)  # Decreases over time
            scores['temporal_urgency'] = urgency_score
            
            # Sentiment negativity score
            sentiment = event_data.get('sentiment_score', 0)
            sentiment_score = max(-sentiment * 50, 0) if sentiment < 0 else 0
            scores['sentiment_negativity'] = min(sentiment_score, 100)
            
            # Anomaly strength score
            anomaly_score = event_data.get('anomaly_score', 0)
            scores['anomaly_strength'] = abs(anomaly_score) * 100
            
            # Calculate weighted total
            for factor, weight in self.scoring_weights.items():
                if factor in scores:
                    total_score += scores[factor] * weight
            
            # Determine severity level
            severity = self._determine_severity(total_score)
            
            return {
                'total_threat_score': min(total_score, 100),
                'severity': severity,
                'component_scores': scores,
                'scoring_weights': self.scoring_weights,
                'calculation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating threat score: {e}")
            return {'total_threat_score': 0, 'severity': AlertSeverity.LOW}
    
    def _determine_severity(self, score: float) -> AlertSeverity:
        """Determine alert severity based on threat score"""
        if score >= self.threshold_config[AlertSeverity.CRITICAL]:
            return AlertSeverity.CRITICAL
        elif score >= self.threshold_config[AlertSeverity.HIGH]:
            return AlertSeverity.HIGH
        elif score >= self.threshold_config[AlertSeverity.MEDIUM]:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

class AlertGenerator:
    """
    Intelligent alert generation system that analyzes events
    and generates appropriate alerts
    """
    
    def __init__(self, threat_scorer: ThreatScorer):
        self.threat_scorer = threat_scorer
        self.alert_rules = self._load_alert_rules()
        self.generated_alerts = []
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Load configurable alert generation rules"""
        return {
            'conflict_escalation': {
                'min_intensity_increase': 0.3,
                'time_window_hours': 24,
                'min_threat_score': 50
            },
            'new_actor_detection': {
                'min_confidence': 0.7,
                'actor_types': ['armed_group', 'military', 'government']
            },
            'humanitarian_crisis': {
                'min_casualties': 10,
                'min_displaced': 1000,
                'min_threat_score': 40
            },
            'anomaly_detection': {
                'min_anomaly_score': 0.8,
                'consecutive_anomalies': 3
            },
            'sentiment_shift': {
                'min_sentiment_change': -0.4,
                'time_window_hours': 48
            }
        }
    
    def analyze_and_generate_alerts(self, event_data: Dict[str, Any]) -> List[Alert]:
        """
        Analyze event data and generate appropriate alerts
        
        Args:
            event_data: Event data to analyze
            
        Returns:
            List of generated alerts
        """
        try:
            alerts = []
            
            # Calculate threat score
            threat_analysis = self.threat_scorer.calculate_threat_score(event_data)
            threat_score = threat_analysis['total_threat_score']
            severity = threat_analysis['severity']
            
            # Generate alerts based on different criteria
            
            # Conflict escalation alert
            escalation_alert = self._check_conflict_escalation(event_data, threat_score, severity)
            if escalation_alert:
                alerts.append(escalation_alert)
            
            # New actor detection alert
            actor_alert = self._check_new_actor_detection(event_data, threat_score, severity)
            if actor_alert:
                alerts.append(actor_alert)
            
            # Humanitarian crisis alert
            humanitarian_alert = self._check_humanitarian_crisis(event_data, threat_score, severity)
            if humanitarian_alert:
                alerts.append(humanitarian_alert)
            
            # Anomaly detection alert
            anomaly_alert = self._check_anomaly_detection(event_data, threat_score, severity)
            if anomaly_alert:
                alerts.append(anomaly_alert)
            
            # Sentiment shift alert
            sentiment_alert = self._check_sentiment_shift(event_data, threat_score, severity)
            if sentiment_alert:
                alerts.append(sentiment_alert)
            
            # Store generated alerts
            self.generated_alerts.extend(alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            return []
    
    def _check_conflict_escalation(self, event_data: Dict, threat_score: float, severity: AlertSeverity) -> Optional[Alert]:
        """Check for conflict escalation patterns"""
        try:
            rules = self.alert_rules['conflict_escalation']
            
            intensity = event_data.get('conflict_intensity', 0)
            previous_intensity = event_data.get('previous_intensity', 0)
            
            if (intensity - previous_intensity >= rules['min_intensity_increase'] and
                threat_score >= rules['min_threat_score']):
                
                return Alert(
                    id=f"escalation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type=AlertType.CONFLICT_ESCALATION,
                    severity=severity,
                    title="Conflict Escalation Detected",
                    description=f"Significant escalation detected with intensity increase of {intensity - previous_intensity:.2f}",
                    region=event_data.get('region', 'Unknown'),
                    country=event_data.get('country'),
                    actors=event_data.get('actors', []),
                    confidence_score=event_data.get('confidence', 0.8),
                    threat_score=threat_score,
                    timestamp=datetime.now(),
                    source_data=event_data,
                    metadata={'escalation_factor': intensity - previous_intensity}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking conflict escalation: {e}")
            return None
    
    def _check_new_actor_detection(self, event_data: Dict, threat_score: float, severity: AlertSeverity) -> Optional[Alert]:
        """Check for new actor detection"""
        try:
            rules = self.alert_rules['new_actor_detection']
            
            new_actors = event_data.get('new_actors', [])
            confidence = event_data.get('actor_detection_confidence', 0)
            
            if new_actors and confidence >= rules['min_confidence']:
                return Alert(
                    id=f"new_actor_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type=AlertType.NEW_ACTOR_DETECTED,
                    severity=severity,
                    title="New Actor Detected",
                    description=f"New actors detected: {', '.join(new_actors)}",
                    region=event_data.get('region', 'Unknown'),
                    country=event_data.get('country'),
                    actors=new_actors,
                    confidence_score=confidence,
                    threat_score=threat_score,
                    timestamp=datetime.now(),
                    source_data=event_data,
                    metadata={'new_actors': new_actors}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking new actor detection: {e}")
            return None
    
    def _check_humanitarian_crisis(self, event_data: Dict, threat_score: float, severity: AlertSeverity) -> Optional[Alert]:
        """Check for humanitarian crisis indicators"""
        try:
            rules = self.alert_rules['humanitarian_crisis']
            
            casualties = event_data.get('casualties', 0)
            displaced = event_data.get('displaced_people', 0)
            
            if (casualties >= rules['min_casualties'] or 
                displaced >= rules['min_displaced'] or
                threat_score >= rules['min_threat_score']):
                
                return Alert(
                    id=f"humanitarian_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type=AlertType.HUMANITARIAN_CRISIS,
                    severity=severity,
                    title="Humanitarian Crisis Alert",
                    description=f"Humanitarian impact detected: {casualties} casualties, {displaced} displaced",
                    region=event_data.get('region', 'Unknown'),
                    country=event_data.get('country'),
                    actors=event_data.get('actors', []),
                    confidence_score=event_data.get('confidence', 0.8),
                    threat_score=threat_score,
                    timestamp=datetime.now(),
                    source_data=event_data,
                    metadata={'casualties': casualties, 'displaced': displaced}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking humanitarian crisis: {e}")
            return None
    
    def _check_anomaly_detection(self, event_data: Dict, threat_score: float, severity: AlertSeverity) -> Optional[Alert]:
        """Check for anomaly detection"""
        try:
            rules = self.alert_rules['anomaly_detection']
            
            anomaly_score = event_data.get('anomaly_score', 0)
            
            if abs(anomaly_score) >= rules['min_anomaly_score']:
                return Alert(
                    id=f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type=AlertType.ANOMALY_DETECTED,
                    severity=severity,
                    title="Anomaly Detected",
                    description=f"Unusual pattern detected with anomaly score: {anomaly_score:.3f}",
                    region=event_data.get('region', 'Unknown'),
                    country=event_data.get('country'),
                    actors=event_data.get('actors', []),
                    confidence_score=abs(anomaly_score),
                    threat_score=threat_score,
                    timestamp=datetime.now(),
                    source_data=event_data,
                    metadata={'anomaly_score': anomaly_score}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking anomaly detection: {e}")
            return None
    
    def _check_sentiment_shift(self, event_data: Dict, threat_score: float, severity: AlertSeverity) -> Optional[Alert]:
        """Check for significant sentiment shifts"""
        try:
            rules = self.alert_rules['sentiment_shift']
            
            sentiment_change = event_data.get('sentiment_change', 0)
            
            if sentiment_change <= rules['min_sentiment_change']:
                return Alert(
                    id=f"sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type=AlertType.SENTIMENT_SHIFT,
                    severity=severity,
                    title="Negative Sentiment Shift",
                    description=f"Significant negative sentiment shift detected: {sentiment_change:.3f}",
                    region=event_data.get('region', 'Unknown'),
                    country=event_data.get('country'),
                    actors=event_data.get('actors', []),
                    confidence_score=abs(sentiment_change),
                    threat_score=threat_score,
                    timestamp=datetime.now(),
                    source_data=event_data,
                    metadata={'sentiment_change': sentiment_change}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking sentiment shift: {e}")
            return None

class NotificationManager:
    """
    Multi-channel notification system for alerts
    Supports email, webhooks, and other notification methods
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.notification_channels = {
            'email': self._send_email_notification,
            'webhook': self._send_webhook_notification,
            'sms': self._send_sms_notification
        }
        self.user_preferences = {}
    
    def send_alert_notification(self, alert: Alert, recipients: List[str], channels: List[str]) -> Dict[str, Any]:
        """
        Send alert notification through specified channels
        
        Args:
            alert: Alert to send
            recipients: List of recipient identifiers
            channels: List of notification channels to use
            
        Returns:
            Notification results
        """
        try:
            results = {
                'alert_id': alert.id,
                'sent_at': datetime.now().isoformat(),
                'channels': {},
                'success': True,
                'errors': []
            }
            
            for channel in channels:
                if channel in self.notification_channels:
                    try:
                        channel_result = self.notification_channels[channel](alert, recipients)
                        results['channels'][channel] = channel_result
                    except Exception as e:
                        error_msg = f"Failed to send via {channel}: {str(e)}"
                        results['errors'].append(error_msg)
                        results['success'] = False
                        logger.error(error_msg)
                else:
                    error_msg = f"Unknown notification channel: {channel}"
                    results['errors'].append(error_msg)
                    logger.warning(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_email_notification(self, alert: Alert, recipients: List[str]) -> Dict[str, Any]:
        """Send email notification"""
        try:
            if 'email' not in self.config:
                return {'success': False, 'error': 'Email configuration not found'}
            
            email_config = self.config['email']
            
            # Create email content
            subject = f"[{alert.severity.value.upper()}] {alert.title}"
            
            html_content = f"""
            <html>
            <body>
                <h2 style="color: {'red' if alert.severity == AlertSeverity.CRITICAL else 'orange' if alert.severity == AlertSeverity.HIGH else 'blue'};">
                    {alert.title}
                </h2>
                <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                <p><strong>Region:</strong> {alert.region}</p>
                <p><strong>Country:</strong> {alert.country or 'N/A'}</p>
                <p><strong>Threat Score:</strong> {alert.threat_score:.1f}/100</p>
                <p><strong>Confidence:</strong> {alert.confidence_score:.1%}</p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                <h3>Description</h3>
                <p>{alert.description}</p>
                
                <h3>Involved Actors</h3>
                <ul>
                    {''.join([f'<li>{actor}</li>' for actor in alert.actors])}
                </ul>
                
                <h3>Additional Information</h3>
                <pre>{json.dumps(alert.metadata, indent=2)}</pre>
            </body>
            </html>
            """
            
            # Send email to each recipient
            sent_count = 0
            for recipient in recipients:
                try:
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From'] = email_config['from_address']
                    msg['To'] = recipient
                    
                    html_part = MIMEText(html_content, 'html')
                    msg.attach(html_part)
                    
                    # Send email
                    with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                        if email_config.get('use_tls', True):
                            server.starttls()
                        if email_config.get('username') and email_config.get('password'):
                            server.login(email_config['username'], email_config['password'])
                        server.send_message(msg)
                    
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient}: {e}")
            
            return {
                'success': sent_count > 0,
                'sent_count': sent_count,
                'total_recipients': len(recipients)
            }
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_webhook_notification(self, alert: Alert, recipients: List[str]) -> Dict[str, Any]:
        """Send webhook notification"""
        try:
            if 'webhook' not in self.config:
                return {'success': False, 'error': 'Webhook configuration not found'}
            
            webhook_config = self.config['webhook']
            
            # Prepare webhook payload
            payload = {
                'alert': alert.to_dict(),
                'notification_timestamp': datetime.now().isoformat(),
                'recipients': recipients
            }
            
            # Send to webhook URLs
            sent_count = 0
            for url in webhook_config.get('urls', []):
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        sent_count += 1
                    else:
                        logger.warning(f"Webhook {url} returned status {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Failed to send webhook to {url}: {e}")
            
            return {
                'success': sent_count > 0,
                'sent_count': sent_count,
                'total_urls': len(webhook_config.get('urls', []))
            }
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_sms_notification(self, alert: Alert, recipients: List[str]) -> Dict[str, Any]:
        """Send SMS notification (placeholder implementation)"""
        # This would integrate with SMS services like Twilio, AWS SNS, etc.
        logger.info(f"SMS notification would be sent for alert {alert.id} to {len(recipients)} recipients")
        return {'success': True, 'note': 'SMS implementation placeholder'}

class RealTimeMonitor:
    """
    Real-time monitoring system that continuously watches for
    events and triggers alerts
    """
    
    def __init__(self, alert_generator: AlertGenerator, notification_manager: NotificationManager):
        self.alert_generator = alert_generator
        self.notification_manager = notification_manager
        self.monitoring_active = False
        self.event_queue = asyncio.Queue()
        self.alert_history = []
        
    def start_monitoring(self):
        """Start real-time monitoring"""
        try:
            logger.info("Starting real-time conflict monitoring...")
            self.monitoring_active = True
            
            # Start monitoring loop in separate thread
            monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitoring_thread.start()
            
            logger.info("Real-time monitoring started successfully")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        logger.info("Real-time monitoring stopped")
    
    def add_event(self, event_data: Dict[str, Any]):
        """Add new event to monitoring queue"""
        try:
            asyncio.run_coroutine_threadsafe(
                self.event_queue.put(event_data),
                asyncio.get_event_loop()
            )
        except Exception as e:
            logger.error(f"Error adding event to queue: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        asyncio.run(self._async_monitoring_loop())
    
    async def _async_monitoring_loop(self):
        """Asynchronous monitoring loop"""
        while self.monitoring_active:
            try:
                # Wait for new events with timeout
                try:
                    event_data = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                    
                    # Process event and generate alerts
                    alerts = self.alert_generator.analyze_and_generate_alerts(event_data)
                    
                    # Send notifications for generated alerts
                    for alert in alerts:
                        await self._process_alert(alert)
                        
                except asyncio.TimeoutError:
                    # No events in queue, continue monitoring
                    continue
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_alert(self, alert: Alert):
        """Process and send notifications for an alert"""
        try:
            # Store alert in history
            self.alert_history.append(alert)
            
            # Determine recipients and channels based on alert severity
            recipients, channels = self._get_notification_config(alert)
            
            # Send notifications
            if recipients and channels:
                notification_result = self.notification_manager.send_alert_notification(
                    alert, recipients, channels
                )
                
                logger.info(f"Alert {alert.id} processed: {notification_result}")
            
        except Exception as e:
            logger.error(f"Error processing alert {alert.id}: {e}")
    
    def _get_notification_config(self, alert: Alert) -> Tuple[List[str], List[str]]:
        """Get notification configuration based on alert properties"""
        # This would typically load from user preferences/configuration
        
        if alert.severity == AlertSeverity.CRITICAL:
            recipients = ['admin@example.com', 'emergency@example.com']
            channels = ['email', 'webhook', 'sms']
        elif alert.severity == AlertSeverity.HIGH:
            recipients = ['admin@example.com', 'analyst@example.com']
            channels = ['email', 'webhook']
        elif alert.severity == AlertSeverity.MEDIUM:
            recipients = ['analyst@example.com']
            channels = ['email']
        else:
            recipients = ['analyst@example.com']
            channels = ['email']
        
        return recipients, channels
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated alerts"""
        try:
            if not self.alert_history:
                return {'total_alerts': 0}
            
            # Calculate statistics
            total_alerts = len(self.alert_history)
            severity_counts = {}
            type_counts = {}
            
            for alert in self.alert_history:
                # Count by severity
                severity = alert.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Count by type
                alert_type = alert.alert_type.value
                type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
            
            # Recent alerts (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_alerts = [a for a in self.alert_history if a.timestamp >= recent_cutoff]
            
            return {
                'total_alerts': total_alerts,
                'recent_alerts_24h': len(recent_alerts),
                'severity_distribution': severity_counts,
                'type_distribution': type_counts,
                'average_threat_score': sum(a.threat_score for a in self.alert_history) / total_alerts,
                'last_alert_time': self.alert_history[-1].timestamp.isoformat() if self.alert_history else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating alert statistics: {e}")
            return {'error': str(e)}