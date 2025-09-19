#!/usr/bin/env python3
"""
Test script to verify news deduplication import
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print(f"Project root: {project_root}")
print(f"Python path: {sys.path}")

try:
    from src.ai.news_deduplication import NewsDeduplicator
    print("✅ NewsDeduplicator import successful")
    NEWS_DEDUPLICATION_AVAILABLE = True

    # Test instantiation
    deduplicator = NewsDeduplicator("./data/geopolitical_intel.db")
    print("✅ NewsDeduplicator instantiation successful")

    # Test method call
    result = deduplicator.process_articles_for_display(hours=24)
    print(f"✅ process_articles_for_display successful: {type(result)}")

except ImportError as e:
    print(f"❌ Import error: {e}")
    NEWS_DEDUPLICATION_AVAILABLE = False
except Exception as e:
    print(f"❌ Other error: {e}")
    NEWS_DEDUPLICATION_AVAILABLE = False

print(f"NEWS_DEDUPLICATION_AVAILABLE: {NEWS_DEDUPLICATION_AVAILABLE}")