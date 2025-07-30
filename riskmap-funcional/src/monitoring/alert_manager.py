import sqlite3
import smtplib
from email.mime.text import MIMEText
import requests
from datetime import datetime, timedelta
from src.utils.config import config, logger


def fetch_high_risk_events(window_hours: int = 1):
    """Retrieve articles with risk_level CRITICAL or HIGH in the last window_hours."""
    db_path = config.database.path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    since = datetime.utcnow() - timedelta(hours=window_hours)
    cursor.execute(
        """
        SELECT title, url, risk_level, created_at
        FROM articles
        WHERE (risk_level='CRITICAL' OR risk_level='HIGH')
          AND created_at >= ?
        ORDER BY created_at DESC
        """, (since.isoformat(),)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def send_email_alert(events, recipients=None):
    """Send email alert with the list of events."""
    if not events:
        return
    smtp_server = config.get('alerts.smtp.server')
    smtp_port = config.get('alerts.smtp.port', 587)
    smtp_user = config.get('alerts.smtp.user')
    smtp_password = config.get('alerts.smtp.password')
    recipients = recipients or config.get('alerts.recipients', [])
    if not smtp_server or not smtp_user or not smtp_password or not recipients:
        logger.error("SMTP or recipients not configured for alerts.")
        return

    subject = f"RiskMap Alert: {len(events)} high-risk events"
    body_lines = []
    for title, url, risk, created_at in events:
        body_lines.append(f"- [{risk}] {title} ({created_at})\n  {url}")
    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipients, msg.as_string())
        logger.info(f"Sent alert email to {recipients}")
    except Exception as e:
        logger.error(f"Error sending alert email: {e}")

def send_telegram_alert(events, bot_token=None, chat_id=None):
    """Send alerts via Telegram Bot."""
    if not events:
        return
    bot_token = bot_token or config.get('alerts.telegram.bot_token')
    chat_id = chat_id or config.get('alerts.telegram.chat_id')
    if not bot_token or not chat_id:
        logger.error('Telegram bot_token or chat_id not configured.')
        return
    # Build message
    lines = [f"[{e[2]}] {e[0]} - {e[3]}" for e in events]
    text = "*High-risk events*\n" + "\n".join(lines)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(url, data={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'})
        if resp.status_code != 200:
            logger.error(f"Telegram alert failed: {resp.text}")
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")

def send_slack_alert(events, webhook_url=None):
    """Send alerts via Slack Incoming Webhook."""
    if not events:
        return
    webhook_url = webhook_url or config.get('alerts.slack.webhook_url')
    if not webhook_url:
        logger.error('Slack webhook_url not configured.')
        return
    lines = [f"[{e[2]}] {e[0]} - {e[3]}" for e in events]
    payload = {'text': '*High-risk events*\n' + "\n".join(lines)}
    try:
        resp = requests.post(webhook_url, json=payload)
        if resp.status_code != 200:
            logger.error(f"Slack alert failed: {resp.text}")
    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")


def run_alerts():
    """Fetches recent high-risk events and sends alerts."""
    window = config.get('alerts.window_hours', 1)
    events = fetch_high_risk_events(window)
    # Send alerts via configured channels
    send_email_alert(events)
    send_telegram_alert(events)
    send_slack_alert(events)


if __name__ == '__main__':
    run_alerts()
