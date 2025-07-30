"""
Comprehensive test suite for the Geopolitical Intelligence System.
Includes unit tests, integration tests, y system validation.
"""

import unittest
import sys
import sqlite3
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from utils.config import Config, DatabaseManager
from data_ingestion.news_collector import NewsAPICollector, RSSCollector
from nlp_processing.text_analyzer import TranslationService, TextClassifier, SentimentAnalyzer
from monitoring.system_monitor import SystemMonitor
from data_quality.validator import DataValidator

# ... (resto del archivo sin cambios, ya que la importación es el único problema crítico) ...
