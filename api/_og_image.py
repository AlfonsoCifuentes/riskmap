"""
Server-side og:image extraction for articles without images.
Used by API endpoints to enrich articles on-the-fly.
Lightweight: only reads first 60KB of HTML, uses stdlib only.
"""

import re
import ssl
import json
import urllib.request
import urllib.error

_TIMEOUT = 6  # seconds — keep it fast for serverless

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; RiskMapBot/1.0)',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Encoding': 'identity',
    'Connection': 'close',
}

_META_PATTERNS = [
    re.compile(r'<meta\s+(?:property|name)\s*=\s*["\']og:image["\']\s+content\s*=\s*["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta\s+content\s*=\s*["\']([^"\']+)["\']\s+(?:property|name)\s*=\s*["\']og:image["\']', re.I),
    re.compile(r'<meta\s+(?:property|name)\s*=\s*["\']twitter:image(?::src)?["\']\s+content\s*=\s*["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta\s+content\s*=\s*["\']([^"\']+)["\']\s+(?:property|name)\s*=\s*["\']twitter:image(?::src)?["\']', re.I),
]

_CLEAN_PARAMS = re.compile(r'[?&]at_(?:medium|campaign)=[^&]*')


def _is_valid(url: str) -> bool:
    if not url or len(url) < 10:
        return False
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    low = url.lower()
    reject = ['placeholder', 'logo', 'favicon', 'icon', 'unsplash.com',
              'picsum.photos', '1x1.', 'blank.', 'spacer', 'pixel.',
              'default-share', 'og-default', '/social-share']
    return not any(r in low for r in reject)


def extract_og_image(article_url: str) -> str | None:
    """
    Fetch article page and extract og:image URL.
    Returns None if extraction fails (timeout, 403, no meta tag, etc.).
    Designed to be fast and safe for serverless use.
    """
    if not article_url:
        return None

    url = _CLEAN_PARAMS.sub('', article_url).rstrip('?&')

    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_ssl_ctx) as resp:
            html = resp.read(60_000).decode('utf-8', errors='ignore')

            # Try meta tags
            for pattern in _META_PATTERNS:
                m = pattern.search(html)
                if m:
                    img = m.group(1).strip()
                    if _is_valid(img):
                        return img

            # Try JSON-LD
            for block in re.findall(
                r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                html, re.DOTALL | re.I
            ):
                try:
                    data = json.loads(block)
                    img = _ld_image(data)
                    if img:
                        return img
                except (json.JSONDecodeError, ValueError):
                    pass

            return None

    except Exception:
        return None


def _ld_image(data) -> str | None:
    """Extract image from JSON-LD structured data."""
    if isinstance(data, list):
        for item in data:
            r = _ld_image(item)
            if r:
                return r
        return None
    if not isinstance(data, dict):
        return None

    img = data.get('image')
    if isinstance(img, str) and _is_valid(img):
        return img
    if isinstance(img, dict):
        u = img.get('url') or img.get('contentUrl')
        if u and _is_valid(u):
            return u
    if isinstance(img, list) and img:
        first = img[0]
        if isinstance(first, str) and _is_valid(first):
            return first
        if isinstance(first, dict):
            u = first.get('url') or first.get('contentUrl')
            if u and _is_valid(u):
                return u

    thumb = data.get('thumbnailUrl')
    if isinstance(thumb, str) and _is_valid(thumb):
        return thumb

    graph = data.get('@graph')
    if isinstance(graph, list):
        for item in graph:
            r = _ld_image(item)
            if r:
                return r

    return None


def enrich_articles_with_images(articles: list) -> list:
    """
    For each article missing an image, attempt to extract og:image
    from the article URL. Updates the article dict in-place and
    also writes back to the database if successful.
    
    Limits extraction to max 5 articles per request to stay fast.
    """
    enriched = 0
    max_enrich = 5  # Don't slow down API too much

    for article in articles:
        if enriched >= max_enrich:
            break

        # Skip if article already has a valid image
        img = article.get('original_image_url') or article.get('image_url') or ''
        if img and img.startswith('http'):
            continue

        # Skip if no URL to scrape
        url = article.get('url')
        if not url:
            continue

        og_img = extract_og_image(url)
        if og_img:
            article['original_image_url'] = og_img
            article['image_url'] = og_img
            article['has_image'] = 1
            enriched += 1

            # Write back to DB (best-effort, don't fail the request)
            _save_image_to_db(article.get('id'), og_img)

    return articles


def _save_image_to_db(article_id, og_image: str):
    """Save extracted og:image back to database (best-effort)."""
    if not article_id:
        return
    try:
        import os
        dsn = os.getenv('DATABASE_URL', '')
        if not dsn:
            return
        import psycopg2
        conn = psycopg2.connect(dsn, sslmode='require')
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE unified_articles "
                "SET original_image_url = %s, image_url = %s, has_image = 1 "
                "WHERE id = %s AND (image_url IS NULL OR image_url = '')",
                (og_image, og_image, article_id),
            )
            conn.commit()
            cur.close()
        finally:
            conn.close()
    except Exception:
        pass  # Best-effort — don't fail the API request
