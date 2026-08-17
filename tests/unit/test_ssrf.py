"""SSRF-guard tests for api/_og_image (addendum B9/B10).

Uses IP literals so getaddrinfo resolves offline (no network in CI). Also a
regression guard that the API request path performs no outbound image fetch.
"""
import pathlib

import api._og_image as og

_API_DIR = pathlib.Path(__file__).resolve().parents[2] / "api"


def test_rejects_non_http_schemes():
    assert not og.is_safe_url("file:///etc/passwd")
    assert not og.is_safe_url("ftp://example.com/x")
    assert not og.is_safe_url("gopher://example.com")


def test_rejects_cloud_metadata_host():
    assert not og.is_safe_url("http://169.254.169.254/latest/meta-data/")
    assert not og.is_safe_url("http://metadata.google.internal/")


def test_rejects_private_and_loopback_ips():
    for url in (
        "http://127.0.0.1/",
        "http://10.0.0.5/x",
        "http://192.168.1.1/",
        "http://172.16.0.1/",
        "http://[::1]/",
        "http://169.254.10.10/",  # link-local
        "http://0.0.0.0/",
    ):
        assert not og.is_safe_url(url), url


def test_allows_public_ip_literal():
    # 93.184.216.34 (public) — getaddrinfo on a literal does not hit network.
    assert og.is_safe_url("http://93.184.216.34/")
    assert og.is_safe_url("https://8.8.8.8/")


def test_tls_context_is_verified():
    import ssl
    assert og._ssl_ctx.verify_mode == ssl.CERT_REQUIRED
    assert og._ssl_ctx.check_hostname is True


def test_api_request_path_has_no_outbound_fetch():
    """articles/deduplicated/hero handlers must not call the image extractor."""
    for name in ("articles.py", "articles/deduplicated.py", "hero-article.py"):
        src = (_API_DIR / name).read_text(encoding="utf-8")
        assert "enrich_articles_with_images(" not in src, name
