"""
Real-Time Alert System for OSINT Platform
Provides immediate notification and dashboard integration for critical news events
"""

import asyncio
import json
import logging
import sqlite3
import smtplib
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
import hashlib
import aiohttp
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """Configuration for alert triggers."""
    rule_id: str
    name: str
    conditions: Dict[str, Any]
    severity_threshold: str
    regions: List[str]
    keywords: List[str]
    notification_channels: List[str]
    cooldown_minutes: int = 30
    active: bool = True


@dataclass
class AlertNotification:
    """Alert notification to be sent."""
    alert_id: str
    rule_id: str
    title: str
    message: str
    severity: str
    region: str
    source_articles: List[str]
    channels: List[str]
    timestamp: datetime
    metadata: Dict[str, Any]


class RealTimeAlertSystem:
    """Real-time alerting system for critical news events."""

    def __init__(
            self,
            config_path: str = "config/alert_config.json",
            db_path: str = "data/alerts.db"):
        self.config_path = Path(config_path)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, datetime] = {}  # Cooldown tracking
        self.notification_queue = asyncio.Queue()
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()

        self.init_database()
        self.load_alert_rules()

        # Email configuration
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': '',  # To be configured
            'password': '',  # To be configured
            'from_email': ''
        }

        # Webhook configurations
        self.webhook_urls = {
            'slack': '',
            'teams': '',
            'discord': '',
            'telegram': ''
        }

        # Statistics tracking
        self.alert_stats = {
            'total_alerts': 0,
            'alerts_by_severity': defaultdict(int),
            'alerts_by_region': defaultdict(int),
            'recent_alerts': deque(maxlen=100)
        }

    def init_database(self):
        """Initialize alerts database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    severity_threshold TEXT,
                    regions TEXT,
                    keywords TEXT,
                    notification_channels TEXT,
                    cooldown_minutes INTEGER DEFAULT 30,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS alert_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE,
                    rule_id TEXT,
                    title TEXT,
                    message TEXT,
                    severity TEXT,
                    region TEXT,
                    source_articles TEXT,
                    channels TEXT,
                    metadata TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    FOREIGN KEY (rule_id) REFERENCES alert_rules (rule_id)
                );

                CREATE TABLE IF NOT EXISTS alert_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_alert_severity ON alert_notifications(severity);
                CREATE INDEX IF NOT EXISTS idx_alert_region ON alert_notifications(region);
                CREATE INDEX IF NOT EXISTS idx_alert_timestamp ON alert_notifications(created_at);
            """)

    def load_alert_rules(self):
        """Load alert rules from configuration."""
        # Load from database first
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT rule_id, name, conditions, severity_threshold, regions,
                       keywords, notification_channels, cooldown_minutes, active
                FROM alert_rules WHERE active = 1
            """)

            for row in cursor.fetchall():
                rule = AlertRule(
                    rule_id=row[0],
                    name=row[1],
                    conditions=json.loads(row[2]),
                    severity_threshold=row[3],
                    regions=json.loads(row[4]),
                    keywords=json.loads(row[5]),
                    notification_channels=json.loads(row[6]),
                    cooldown_minutes=row[7],
                    active=bool(row[8])
                )
                self.alert_rules[rule.rule_id] = rule

        # If no rules in database, create default ones
        if not self.alert_rules:
            self._create_default_alert_rules()

    def _create_default_alert_rules(self):
        """Create default alert rules."""
        default_rules = [
            AlertRule(
                rule_id="critical_conflict_ukraine",
                name="Critical Ukraine Conflict Updates",
                conditions={
                    "threat_level": ["critical"],
                    "credibility_score": {"min": 0.7},
                    "keywords_required": 2
                },
                severity_threshold="critical",
                regions=["ukraine"],
                keywords=[
                    "military",
                    "attack",
                    "invasion",
                    "missile",
                    "bombing"],
                notification_channels=["email", "websocket", "slack"],
                cooldown_minutes=15
            ),
            AlertRule(
                rule_id="high_middle_east",
                name="High Priority Middle East Events",
                conditions={
                    "threat_level": ["critical", "high"],
                    "credibility_score": {"min": 0.6}
                },
                severity_threshold="high",
                regions=["middle_east"],
                keywords=["israel", "palestine", "gaza", "syria", "iran"],
                notification_channels=["email", "websocket"],
                cooldown_minutes=30
            ),
            AlertRule(
                rule_id="cyber_threats_global",
                name="Global Cyber Threats",
                conditions={
                    "threat_level": ["critical", "high"],
                    "topics": ["security"]
                },
                severity_threshold="high",
                regions=["*"],  # All regions
                keywords=[
                    "cyber",
                    "hacking",
                    "malware",
                    "breach",
                    "espionage"],
                notification_channels=["email", "websocket", "teams"],
                cooldown_minutes=60
            ),
            AlertRule(
                rule_id="humanitarian_crisis",
                name="Humanitarian Crisis Alerts",
                conditions={
                    "threat_level": ["critical"],
                    "topics": ["humanitarian"]
                },
                severity_threshold="critical",
                regions=["*"],
                keywords=[
                    "refugee",
                    "disaster",
                    "famine",
                    "epidemic",
                    "evacuation"],
                notification_channels=["email", "websocket"],
                cooldown_minutes=45
            )
        ]

        for rule in default_rules:
            self.add_alert_rule(rule)

    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO alert_rules
                (rule_id, name, conditions, severity_threshold, regions, keywords,
                 notification_channels, cooldown_minutes, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.rule_id,
                rule.name,
                json.dumps(rule.conditions),
                rule.severity_threshold,
                json.dumps(rule.regions),
                json.dumps(rule.keywords),
                json.dumps(rule.notification_channels),
                rule.cooldown_minutes,
                rule.active
            ))

        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.name}")

    async def check_intelligence_report(
            self, report: Dict[str, Any], article: Dict[str, Any]):
        """Check if intelligence report triggers any alerts."""
        triggered_rules = []

        for rule_id, rule in self.alert_rules.items():
            if not rule.active:
                continue

            # Check cooldown
            if self._is_in_cooldown(rule_id):
                continue

            # Check if conditions match
            if self._evaluate_rule_conditions(rule, report, article):
                triggered_rules.append(rule)

        # Generate alerts for triggered rules
        for rule in triggered_rules:
            await self._generate_alert(rule, report, article)

    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if alert rule is in cooldown period."""
        if rule_id not in self.active_alerts:
            return False

        rule = self.alert_rules[rule_id]
        last_alert_time = self.active_alerts[rule_id]
        cooldown_end = last_alert_time + \
            timedelta(minutes=rule.cooldown_minutes)

        return datetime.now() < cooldown_end

    def _evaluate_rule_conditions(
            self, rule: AlertRule, report: Dict[str, Any], article: Dict[str, Any]) -> bool:
        """Evaluate if rule conditions are met."""
        conditions = rule.conditions

        # Check threat level
        if "threat_level" in conditions:
            if report.get("threat_level") not in conditions["threat_level"]:
                return False

        # Check credibility score
        if "credibility_score" in conditions:
            cred_conditions = conditions["credibility_score"]
            cred_score = report.get("credibility_score", 0)

            if "min" in cred_conditions and cred_score < cred_conditions["min"]:
                return False
            if "max" in cred_conditions and cred_score > cred_conditions["max"]:
                return False

        # Check topics
        if "topics" in conditions:
            required_topics = conditions["topics"]
            article_topics = report.get("topics", [])
            if not any(topic in article_topics for topic in required_topics):
                return False

        # Check regions
        if rule.regions and "*" not in rule.regions:
            article_regions = [
                geo.split(':')[0] for geo in report.get(
                    "geographic_entities", [])]
            if not any(region in article_regions for region in rule.regions):
                return False

        # Check keywords
        if rule.keywords:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower(
            )
            keyword_matches = sum(
                1 for keyword in rule.keywords if keyword.lower() in text)

            required_keywords = conditions.get("keywords_required", 1)
            if keyword_matches < required_keywords:
                return False

        return True

    async def _generate_alert(self, rule: AlertRule,
                              report: Dict[str, Any], article: Dict[str, Any]):
        """Generate and queue alert notification."""
        alert_id = hashlib.md5(
            f"{rule.rule_id}{article.get('content_hash', '')}{datetime.now()}".encode()).hexdigest()[
            :16]

        # Determine region
        regions = [geo.split(':')[0]
                   for geo in report.get("geographic_entities", [])]
        primary_region = regions[0] if regions else "global"

        # Create notification
        notification = AlertNotification(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            title=f"🚨 {rule.name}",
            message=self._format_alert_message(rule, report, article),
            severity=report.get("threat_level", "medium"),
            region=primary_region,
            source_articles=[article.get("content_hash", "")],
            channels=rule.notification_channels,
            timestamp=datetime.now(),
            metadata={
                "rule_name": rule.name,
                "credibility_score": report.get("credibility_score", 0),
                "conflict_indicators": report.get("conflict_indicators", []),
                "source": article.get("source", ""),
                "country": article.get("country", "")
            }
        )

        # Store in database
        await self._store_alert_notification(notification)

        # Queue for processing
        await self.notification_queue.put(notification)

        # Update cooldown tracking
        self.active_alerts[rule.rule_id] = datetime.now()

        # Update statistics
        self._update_alert_stats(notification)

        logger.info(f"Generated alert: {alert_id} for rule {rule.name}")

    def _format_alert_message(
            self, rule: AlertRule, report: Dict[str, Any], article: Dict[str, Any]) -> str:
        """Format alert message for notification."""
        title = article.get("title", "No title")
        source = article.get("source", "Unknown source")
        threat_level = report.get("threat_level", "unknown")
        credibility = report.get("credibility_score", 0)

        message = f"""
📰 **{title}**

🔍 **Source**: {source}
⚠️ **Threat Level**: {threat_level.upper()}
📊 **Credibility**: {credibility:.2f}
🌍 **Region**: {report.get('geographic_entities', ['Unknown'])[0] if report.get('geographic_entities') else 'Unknown'}

**Indicators**: {', '.join(report.get('conflict_indicators', [])[:3])}

**Article URL**: {article.get('url', 'N/A')}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """.strip()

        return message

    async def _store_alert_notification(self, notification: AlertNotification):
        """Store alert notification in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alert_notifications
                (alert_id, rule_id, title, message, severity, region,
                 source_articles, channels, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notification.alert_id,
                notification.rule_id,
                notification.title,
                notification.message,
                notification.severity,
                notification.region,
                json.dumps(notification.source_articles),
                json.dumps(notification.channels),
                json.dumps(notification.metadata)
            ))

    def _update_alert_stats(self, notification: AlertNotification):
        """Update alert statistics."""
        self.alert_stats['total_alerts'] += 1
        self.alert_stats['alerts_by_severity'][notification.severity] += 1
        self.alert_stats['alerts_by_region'][notification.region] += 1
        self.alert_stats['recent_alerts'].append({
            'alert_id': notification.alert_id,
            'title': notification.title,
            'severity': notification.severity,
            'region': notification.region,
            'timestamp': notification.timestamp.isoformat()
        })

    async def process_notifications(self):
        """Process queued notifications."""
        while True:
            try:
                notification = await self.notification_queue.get()
                await self._send_notification(notification)
                self.notification_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing notification: {e}")

    async def _send_notification(self, notification: AlertNotification):
        """Send notification through configured channels."""
        for channel in notification.channels:
            try:
                if channel == "email":
                    await self._send_email_notification(notification)
                elif channel == "websocket":
                    await self._send_websocket_notification(notification)
                elif channel == "slack":
                    await self._send_slack_notification(notification)
                elif channel == "teams":
                    await self._send_teams_notification(notification)
                elif channel == "discord":
                    await self._send_discord_notification(notification)
                elif channel == "telegram":
                    await self._send_telegram_notification(notification)

                logger.info(
                    f"Sent notification {notification.alert_id} via {channel}")
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")

        # Mark as sent
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE alert_notifications
                SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                WHERE alert_id = ?
            """, (notification.alert_id,))

    async def _send_email_notification(self, notification: AlertNotification):
        """Send email notification."""
        if not self.email_config.get('username'):
            logger.warning("Email not configured, skipping email notification")
            return

        msg = MimeMultipart()
        msg['From'] = self.email_config['from_email']
        msg['To'] = self.email_config.get('to_email', '')
        msg['Subject'] = f"[{notification.severity.upper()}] {notification.title}"

        body = notification.message
        msg.attach(MimeText(body, 'plain'))

        # Send email (implementation would go here)
        logger.info(f"Email notification prepared for {notification.alert_id}")

    async def _send_websocket_notification(
            self, notification: AlertNotification):
        """Send WebSocket notification to connected clients."""
        if not self.websocket_clients:
            return

        message = {
            "type": "alert",
            "data": asdict(notification)
        }

        # Send to all connected clients
        disconnected = set()
        for client in self.websocket_clients:
            try:
                await client.send(json.dumps(message, default=str))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)

        # Remove disconnected clients
        self.websocket_clients -= disconnected

    async def _send_slack_notification(self, notification: AlertNotification):
        """Send Slack notification."""
        if not self.webhook_urls.get('slack'):
            return

        payload = {
            "text": notification.title,
            "attachments": [
                {
                    "color": "danger" if notification.severity == "critical" else "warning",
                    "fields": [
                        {
                            "title": "Severity",
                            "value": notification.severity.upper(),
                            "short": True
                        },
                        {
                            "title": "Region",
                            "value": notification.region,
                            "short": True
                        }
                    ],
                    "text": notification.message,
                    "ts": int(notification.timestamp.timestamp())
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            await session.post(self.webhook_urls['slack'], json=payload)

    async def _send_teams_notification(self, notification: AlertNotification):
        """Send Microsoft Teams notification."""
        # Teams webhook implementation would go here
        pass

    async def _send_discord_notification(
            self, notification: AlertNotification):
        """Send Discord notification."""
        # Discord webhook implementation would go here
        pass

    async def _send_telegram_notification(
            self, notification: AlertNotification):
        """Send Telegram notification."""
        # Telegram bot implementation would go here
        pass

    async def start_websocket_server(
            self,
            host: str = "localhost",
            port: int = 8765):
        """Start WebSocket server for real-time notifications."""
        async def handle_client(websocket, path):
            logger.info(
                f"New WebSocket client connected: {websocket.remote_address}")
            self.websocket_clients.add(websocket)

            try:
                # Send current statistics on connection
                stats_message = {
                    "type": "stats",
                    "data": self.alert_stats
                }
                await websocket.send(json.dumps(stats_message, default=str))

                # Keep connection alive
                await websocket.wait_closed()
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.websocket_clients.discard(websocket)
                logger.info(
                    f"WebSocket client disconnected: {websocket.remote_address}")

        server = await websockets.serve(handle_client, host, port)
        logger.info(f"WebSocket server started on ws://{host}:{port}")
        return server

    async def get_alert_dashboard_data(self) -> Dict[str, Any]:
        """Get data for alert dashboard."""
        with sqlite3.connect(self.db_path) as conn:
            # Recent alerts
            recent_alerts = conn.execute("""
                SELECT alert_id, title, severity, region, created_at
                FROM alert_notifications
                ORDER BY created_at DESC
                LIMIT 20
            """).fetchall()

            # Statistics
            severity_stats = conn.execute("""
                SELECT severity, COUNT(*)
                FROM alert_notifications
                WHERE created_at > datetime('now', '-24 hours')
                GROUP BY severity
            """).fetchall()

            region_stats = conn.execute("""
                SELECT region, COUNT(*)
                FROM alert_notifications
                WHERE created_at > datetime('now', '-24 hours')
                GROUP BY region
            """).fetchall()

        return {
            "recent_alerts": [
                {
                    "alert_id": row[0],
                    "title": row[1],
                    "severity": row[2],
                    "region": row[3],
                    "timestamp": row[4]
                }
                for row in recent_alerts
            ],
            "severity_distribution": dict(severity_stats),
            "region_distribution": dict(region_stats),
            "active_rules": len([r for r in self.alert_rules.values() if r.active]),
            "total_alerts_24h": sum(dict(severity_stats).values()),
            "current_stats": dict(self.alert_stats)
        }


# Example usage
if __name__ == "__main__":
    async def main():
        alert_system = RealTimeAlertSystem()

        # Start WebSocket server
        await alert_system.start_websocket_server()

        # Start notification processor
        await alert_system.process_notifications()

    asyncio.run(main())
