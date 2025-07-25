"""Simple alert engine for Riskmap.

Loads YAML rules from alerts/rules.yaml, evaluates latest events from DB and
prints alert messages (placeholder for email/Telegram/Slack).
"""

import yaml
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from utils.config import config, logger
from alerts.notify import send_notification

RULES_PATH = Path(__file__).parent / "rules.yaml"
DB_PATH = config.database.path


def load_rules():
    if not RULES_PATH.exists():
        logger.warning("No alert rules found.")
        return []
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def evaluate_rules():
    rules = load_rules()
    if not rules:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for rule in rules:
        try:
            if rule.get("type") == "fatality_threshold":
                threshold = int(rule.get("threshold", 100))
                lookback_h = int(rule.get("lookback_hours", 24))
                cur.execute(
                    """
                    SELECT title, fatalities, published_at FROM historical_events
                    WHERE published_at >= datetime('now', ?)
                      AND fatalities >= ?
                    ORDER BY fatalities DESC
                    LIMIT 5
                    """, (f'-{lookback_h} hours', threshold)
                )
                matches = cur.fetchall()
                for m in matches:
                    message=f"{rule['description']}: {m[0]} ({m[1]} fatalities) {m[2]}"
                    logger.warning(message)
                    send_notification(title="Riskmap Alert", body=message)
        except Exception as exc:
            logger.error(f"Error evaluating rule {rule}: {exc}")
    conn.close()


if __name__ == "__main__":
    evaluate_rules()
