"""Tests for src.core.dedup — canonical URL, title match, independence."""
from src.core import dedup


def test_canonical_url_strips_trackers_and_normalises():
    a = dedup.canonical_url("https://www.Reuters.com/world/x/?utm_source=t&id=5#frag")
    b = dedup.canonical_url("http://reuters.com/world/x?id=5")
    assert a == b


def test_registrable_domain():
    assert dedup.registrable_domain("https://www.bbc.co.uk/news/x") == "bbc.co.uk"
    assert dedup.registrable_domain("https://edition.cnn.com/x") == "cnn.com"


def test_title_hash_matches_near_identical():
    h1 = dedup.title_hash("Israel strikes Beirut, dozens reported dead")
    h2 = dedup.title_hash("israel strikes beirut dozens reported dead!!!")
    assert h1 == h2 and h1 != ""


def test_jaccard_similar_vs_different():
    hi = dedup.jaccard("Massive earthquake hits Turkey near Gaziantep",
                       "Earthquake strikes Turkey close to Gaziantep")
    lo = dedup.jaccard("Massive earthquake hits Turkey",
                       "Stock markets rally in Tokyo")
    assert hi > 0.35 and lo < 0.15


def test_is_duplicate_by_url_and_title():
    a = {"url": "https://reuters.com/x?utm_source=z", "title": "Flood in Valencia"}
    b = {"url": "https://reuters.com/x", "title": "totally different headline"}
    assert dedup.is_duplicate(a, b)  # same canonical URL
    c = {"url": "https://bbc.com/y", "title": "Flood in Valencia"}
    assert dedup.is_duplicate(a, c)  # same normalised title


def test_independent_source_count_collapses_syndication():
    wire = [
        {"url": "https://reuters.com/a"},
        {"url": "https://reuters.com/b"},   # same domain -> counts once
        {"url": "https://bbc.com/c"},
        {"url": "https://aljazeera.com/d"},
    ]
    assert dedup.independent_source_count(wire) == 3
