"""
Data ingestion package for collecting news from multiple sources.
"""

from .news_collector import NewsAPICollector, RSSCollector, GeopoliticalNewsCollector

__all__ = ['NewsAPICollector', 'RSSCollector', 'GeopoliticalNewsCollector']
