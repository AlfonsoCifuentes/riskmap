"""
Server-side og:image extraction for articles without images.
Used by API endpoints to enrich articles on-the-fly.

Multi-strategy approach:
  1. Direct HTML scrape (og:image / twitter:image / JSON-LD)
  2. iFramely oEmbed proxy (WashPost, Politico, Bloomberg)
  3. Microlink API (renders JS — CNN, Axios, Hollywood Reporter, etc.)

Keeps a negative cache to avoid re-trying failed URLs within the
same serverless cold-start window.
"""

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request

_TIMEOUT = 6  # seconds — keep it fast for serverless

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Encoding': 'identity',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'close',
}

# Negative cache — skip URLs that already failed in this cold-start
_FAILED_URLS: set[str] = set()

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
              'default-share', 'og-default', '/social-share', 'sprite',
              'avatar', 'transparent', 'tracking', 'counter', 'beacon']
    return not any(r in low for r in reject)


def extract_og_image(article_url: str) -> str | None:
    """
    Multi-strategy og:image extraction:
      1. Direct HTML scrape (fast, works for ~80% of sites)
      2. iFramely oEmbed proxy (handles WashPost, Politico, Bloomberg)
      3. Microlink API fallback (renders JS, handles CNN, Axios, etc.)

    Returns None if all strategies fail.
    """
    if not article_url:
        return None
    if article_url in _FAILED_URLS:
        return None

    url = _CLEAN_PARAMS.sub('', article_url).rstrip('?&')

    # --- Strategy 1: Direct HTML scrape ---
    img = _extract_direct(url)
    if img:
        return img

    # --- Strategy 2: iFramely oEmbed proxy (best for WashPost/Politico) ---
    img = _extract_iframely(url)
    if img:
        return img

    # --- Strategy 3: Microlink API (renders JS, handles blocked sites) ---
    img = _extract_microlink(url)
    if img:
        return img

    # All strategies failed — cache this URL to avoid retrying
    _FAILED_URLS.add(article_url)
    return None


def _extract_direct(url: str) -> str | None:
    """Extract og:image via direct HTML fetch."""
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_ssl_ctx) as resp:
            html = resp.read(80_000).decode('utf-8', errors='ignore')

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

    except Exception:
        pass
    return None


def _extract_iframely(url: str) -> str | None:
    """
    Use iFramely's free oEmbed proxy to extract og:image.
    Excellent for WashPost, Politico, Bloomberg — sites with strict bot blocking.
    """
    try:
        encoded = urllib.parse.quote(url, safe='')
        api_url = f'https://open.iframe.ly/api/oembed?url={encoded}&origin=riskmap'
        req = urllib.request.Request(api_url, headers={
            'User-Agent': _HEADERS['User-Agent'],
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=8, context=_ssl_ctx) as resp:
            data = json.loads(resp.read(20_000).decode())

        img = data.get('thumbnail_url') or data.get('url')
        if isinstance(img, str) and _is_valid(img):
            return img
    except Exception:
        pass
    return None


def _extract_microlink(url: str) -> str | None:
    """
    Use Microlink API to extract metadata from JS-rendered pages.
    Free tier: ~50 req/day — used only as fallback when direct fails.
    Handles: CNN, WashPost, Axios, Politico, Hollywood Reporter, etc.
    """
    try:
        encoded = urllib.parse.quote(url, safe='')
        api_url = f'https://api.microlink.io?url={encoded}'
        req = urllib.request.Request(api_url, headers={
            'User-Agent': _HEADERS['User-Agent'],
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=12, context=_ssl_ctx) as resp:
            data = json.loads(resp.read(50_000).decode())

        if data.get('status') == 'success':
            img_data = data.get('data', {}).get('image', {})
            img = img_data.get('url') if isinstance(img_data, dict) else img_data
            if isinstance(img, str) and _is_valid(img):
                return img
    except Exception:
        pass
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
