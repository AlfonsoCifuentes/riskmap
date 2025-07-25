"""
Image Extractor for News Articles
Extracts the main image from news articles using various methods
"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class NewsImageExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Fallback images by news source
        self.source_fallbacks = {
            'CNN': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
            'BBC': 'https://images.unsplash.com/photo-1495020689067-958852a7e369?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
            'Reuters': 'https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
            'Al Jazeera': 'https://images.unsplash.com/photo-1526666923127-b2bb3ecb763d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
            'default': 'https://images.unsplash.com/photo-1495020689067-958852a7e369?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'}

    def extract_image_from_url(self, url, source=''):
        """
        Extract the main image from a news article URL
        """
        try:
            logger.info(f"Extracting image from: {url}")

            # Get the webpage content
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try different methods to find the main image
            image_url = self._try_extraction_methods(soup, url)

            if image_url:
                logger.info(f"Found image: {image_url}")
                return image_url
            else:
                logger.warning(f"No image found for {url}, using fallback")
                return self._get_fallback_image(source)

        except Exception as e:
            logger.error(f"Error extracting image from {url}: {e}")
            return self._get_fallback_image(source)

    def _try_extraction_methods(self, soup, base_url):
        """
        Try multiple methods to extract the main image
        """
        # Method 1: Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return self._resolve_url(og_image['content'], base_url)

        # Method 2: Twitter Card image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return self._resolve_url(twitter_image['content'], base_url)

        # Method 3: Article main image (various selectors)
        selectors = [
            'article img',
            '.article-image img',
            '.main-image img',
            '.hero-image img',
            '.featured-image img',
            'img[class*="article"]',
            'img[class*="main"]',
            'img[class*="hero"]',
            'figure img'
        ]

        for selector in selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                return self._resolve_url(img['src'], base_url)

        # Method 4: Largest image in article
        article_imgs = soup.find_all('img')
        if article_imgs:
            # Filter out small images (icons, avatars, etc.)
            large_imgs = []
            for img in article_imgs:
                src = img.get('src') or img.get('data-src')
                if src and self._is_valid_image(src):
                    large_imgs.append(src)

            if large_imgs:
                return self._resolve_url(large_imgs[0], base_url)

        return None

    def _is_valid_image(self, src):
        """
        Check if the image source is valid (not icon, avatar, etc.)
        """
        if not src:
            return False

        # Skip common small/icon images
        skip_patterns = [
            'icon', 'logo', 'avatar', 'profile', 'thumb',
            'social', 'share', 'facebook', 'twitter',
            'advertisement', 'ad', 'banner'
        ]

        src_lower = src.lower()
        for pattern in skip_patterns:
            if pattern in src_lower:
                return False

        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        return any(ext in src_lower for ext in valid_extensions)

    def _resolve_url(self, url, base_url):
        """
        Resolve relative URLs to absolute URLs
        """
        if not url:
            return None

        # If already absolute URL, return as is
        if url.startswith('http'):
            return url

        # Resolve relative URL
        return urljoin(base_url, url)

    def _get_fallback_image(self, source):
        """
        Get fallback image based on source
        """
        # Try to find source-specific fallback
        for src_key in self.source_fallbacks:
            if src_key.lower() in source.lower():
                return self.source_fallbacks[src_key]

        return self.source_fallbacks['default']

    def update_article_images(self, db_connection):
        """
        Update all articles in database that don't have images
        """
        cursor = db_connection.cursor()

        # Get articles without images
        cursor.execute("""
            SELECT id, url, source
            FROM articles
            WHERE (image_url IS NULL OR image_url = '')
            AND url IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 20
        """)

        articles = cursor.fetchall()
        logger.info(f"Found {len(articles)} articles without images")

        updated_count = 0
        for article_id, url, source in articles:
            try:
                image_url = self.extract_image_from_url(url, source)
                if image_url:
                    cursor.execute("""
                        UPDATE articles
                        SET image_url = ?
                        WHERE id = ?
                    """, (image_url, article_id))
                    updated_count += 1
                    logger.info(f"Updated image for article {article_id}")
            except Exception as e:
                logger.error(
                    f"Error updating image for article {article_id}: {e}")

        db_connection.commit()
        logger.info(f"Updated {updated_count} articles with images")
        return updated_count

# Convenience function


def extract_article_image(url, source=''):
    """
    Extract image from a single URL
    """
    extractor = NewsImageExtractor()
    return extractor.extract_image_from_url(url, source)
