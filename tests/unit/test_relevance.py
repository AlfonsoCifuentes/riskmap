"""Tests for the improved relevance filter (user request: stop off-topic leaks)."""
from src.core import relevance


def _rel(text):
    return relevance.score(text)[1]


def test_conflict_news_passes():
    assert _rel("Airstrike hits Beirut suburb, dozens of casualties reported")
    assert _rel("Russian troops launch new offensive near Kharkiv")
    assert _rel("UN Security Council debates sanctions amid escalation")


def test_disaster_news_passes():
    assert _rel("Magnitude 6.8 earthquake strikes southern Turkey")
    assert _rel("Flash flood forces evacuations across Valencia region")
    assert _rel("Wildfire spreads across northern La Palma")


def test_sports_rejected():
    assert not _rel("Premier League: late goal wins the match for the home side")
    assert not _rel("World Cup final ends in dramatic penalty shootout")


def test_entertainment_rejected():
    assert not _rel("New Netflix film tops the box office this weekend")
    assert not _rel("Pop singer announces world tour and new album")


def test_business_tech_rejected():
    assert not _rel("Company reports record quarterly earnings and stock split")
    assert not _rel("New smartphone launch: bigger screen and better camera")


def test_substring_false_positives_avoided():
    # 'war' in 'warehouse', 'riot' in 'patriot', 'aid' in 'maiden' must NOT match.
    assert not _rel("Amazon opens a huge new warehouse creating local jobs")
    assert not _rel("The patriot supporters celebrated the maiden voyage")


def test_negative_veto_but_strong_signal_still_passes():
    # A strong term present -> passes even if a sport word appears.
    assert _rel("Missile strike near the football stadium kills several people")


def test_category_hint():
    assert relevance.score("Major earthquake devastates the region")[2] == "disaster"
    assert relevance.score("Airstrike and shelling reported near the border")[2] == "conflict"


def test_war_film_rejected_but_real_conflict_kept():
    # A review of a *film* about a war is off-topic even though it borrows war
    # vocabulary; a real strike report is kept (regression: user-reported leak).
    assert not _rel("What does a hit film about the Iraq war say about viewers")
    assert not _rel("New blockbuster movie about wartime heroes tops box office")
    assert _rel("Israeli airstrikes kill dozens in Gaza as offensive escalates")


def test_medium_only_unrest_still_passes():
    # No strong term, but enough conflict signal -> stays relevant.
    assert _rel("Protesters clash with police, dozens injured in unrest")
