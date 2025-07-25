"""
NLP processing package for text analysis and understanding.
"""

from .text_analyzer import TextAnalyzer, TranslationService, TextClassifier, SentimentAnalyzer
from .real_text_analyzer import RealGeopoliticalTextAnalyzer as GeopoliticalTextAnalyzer

# Bulk processing function


def bulk_process_articles(articles_data, analyzer=None):
    """Función de procesamiento masivo de artículos."""
    if analyzer is None:
        analyzer = GeopoliticalTextAnalyzer()

    results = []
    for article in articles_data:
        try:
            result = analyzer.analyze(
                article.get(
                    'content', ''), article.get(
                    'title', ''))
            results.append(result)
        except Exception as e:
            print(f"Error processing article: {e}")
            results.append(None)

    return results


__all__ = ['TextAnalyzer', 'GeopoliticalTextAnalyzer', 'bulk_process_articles']
