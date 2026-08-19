"""Geopolitical / disaster relevance filter (addendum, user request).

The legacy filter summed keyword *substrings* with a low threshold and no
negative signal, so off-topic news leaked in ("war" matched "warehouse", "riot"
matched "patriot", and a sports article mentioning "security"/"defense" passed).

This module fixes that with:
  * word-boundary matching (no substring false positives),
  * an explicit NEGATIVE lexicon (sport/entertainment/business/tech/lifestyle),
  * a decision that needs a genuine strong signal (or a disaster term, or
    several medium terms) AND rejects items the negative lexicon dominates.

Pure stdlib -> unit-testable without the DB.
"""
from __future__ import annotations

import re

# --- Positive lexicon (weight -> terms) -----------------------------------
STRONG = [
    "airstrike", "air strike", "missile", "drone strike", "shelling", "bombing",
    "bombardment", "invasion", "offensive", "insurgency", "militant", "militia",
    "ceasefire", "coup", "war crime", "genocide", "ethnic cleansing",
    "chemical weapon", "nuclear weapon", "terrorist", "terrorism", "hostage",
    "armed conflict", "gunmen", "massacre", "occupation", "annexation",
    "cyberattack", "cyber attack",
]
DISASTER = [
    "earthquake", "aftershock", "tsunami", "hurricane", "typhoon", "cyclone",
    "wildfire", "bushfire", "flood", "flash flood", "landslide", "mudslide",
    "volcano", "volcanic eruption", "drought", "famine", "storm surge",
    "tornado", "heatwave", "humanitarian crisis", "displacement",
    "displaced", "refugee",
]
MEDIUM = [
    "military", "troops", "soldiers", "casualties", "warplane", "artillery",
    "sanctions", "conflict", "escalation", "border clash", "cross-border",
    "sovereignty", "territorial", "rebel", "protest", "unrest", "riot",
    "crackdown", "clashes", "espionage",
    "evacuation", "airspace", "blockade", "embargo", "warzone", "war zone",
    "paramilitary", "airbase", "warhead", "peacekeeper",
    # common conflict/severity terms the lexicon was missing
    "strike", "strikes", "attack", "attacks", "killed", "dead", "death toll",
    "explosion", "blast", "raid", "offensive", "gunfire", "gunmen", "militants",
    "assault", "wounded", "injured", "detained", "hostages", "siege", "curfew",
    "war",
]
WEAK = [
    "diplomatic", "negotiations", "summit", "treaty", "alliance", "geopolitical",
    "ministry of defense", "ministry of defence", "security council", "nato",
    "united nations", "relief effort", "aid convoy",
]

# --- Negative lexicon (off-topic domains) ---------------------------------
# HARD negatives are disqualifying domains (sport / entertainment): a genuine
# conflict or disaster EVENT report almost always carries a STRONG or DISASTER
# term, so if a hard-negative term appears and no strong/disaster signal does,
# the item is off-topic (e.g. a review of a *film* about a war). SOFT negatives
# (business / tech / lifestyle) only veto when they clearly dominate the text.
NEG_HARD = [
    # sport
    "football", "soccer", "basketball", "baseball", "tennis", "golf", "cricket",
    "nba", "nfl", "premier league", "la liga", "champions league", "world cup",
    "olympics", "grand prix", "formula 1", "transfer window", "match day",
    "goalkeeper", "touchdown", "playoff", "quarterback", "midfielder",
    # entertainment / celebrity
    "box office", "movie", "film premiere", "hit film", "blockbuster", "biopic",
    "cinema", "documentary film", "tv series", "trailer", "celebrity", "singer",
    "album", "concert", "grammy", "oscars", "netflix", "tv show", "streaming",
    "actor", "actress", "red carpet", "fashion week", "reality show",
]
NEG_SOFT = [
    # business/markets/tech consumer / lifestyle
    "quarterly earnings", "stock split", "share price", "ipo", "dividend",
    "smartphone", "gadget", "iphone", "android app", "video game", "gaming",
    "esports", "cryptocurrency price", "bitcoin price", "product launch",
    "recipe", "restaurant review", "travel guide", "horoscope", "lottery",
    "wedding", "royal baby", "influencer", "tiktok trend",
]
NEGATIVE = NEG_HARD + NEG_SOFT  # kept for backwards-compatible imports


def _compile(terms):
    # Word-boundary alternation; escape multiword phrases.
    # trailing s? lets singular lexicon entries also match plurals (flood->floods)
    pattern = r"\b(?:" + "|".join(re.escape(t) for t in terms) + r")s?\b"
    return re.compile(pattern, re.IGNORECASE)


_RE_STRONG = _compile(STRONG)
_RE_DISASTER = _compile(DISASTER)
_RE_MEDIUM = _compile(MEDIUM)
_RE_WEAK = _compile(WEAK)
_RE_NEG_HARD = _compile(NEG_HARD)
_RE_NEG_SOFT = _compile(NEG_SOFT)


def _count(rx, text):
    return len({m.group(0).lower() for m in rx.finditer(text)})


def score(text: str) -> tuple[float, bool, str | None]:
    """Return (score 0..1, is_relevant, category_hint).

    Decision requires a real signal and is vetoed when off-topic terms dominate.
    """
    if not text:
        return 0.0, False, None
    t = text

    strong = _count(_RE_STRONG, t)
    disaster = _count(_RE_DISASTER, t)
    medium = _count(_RE_MEDIUM, t)
    weak = _count(_RE_WEAK, t)
    neg_hard = _count(_RE_NEG_HARD, t)
    neg_soft = _count(_RE_NEG_SOFT, t)

    raw = 3 * strong + 3 * disaster + 2 * medium + 1 * weak
    score_val = min(raw / 10.0, 1.0)

    has_strong = (strong + disaster) >= 1
    enough_medium = medium >= 2 or (medium >= 1 and weak >= 1)

    # Hard veto: a sport/entertainment term with NO strong/disaster event term
    # is off-topic no matter how much conflict *vocabulary* it borrows (e.g. a
    # review of a film about a war). Real events carry a strong/disaster word.
    if neg_hard >= 1 and not has_strong:
        return score_val, False, None

    # Soft veto: business/tech/lifestyle terms present and clearly dominant.
    if neg_soft >= 1 and not has_strong and raw < (neg_soft * 3 + 2):
        return score_val, False, None

    is_relevant = has_strong or enough_medium

    category = None
    if is_relevant:
        if disaster >= 1 and disaster >= strong:
            category = "disaster"
        elif strong >= 1 or medium >= 1:
            category = "conflict"
    return round(score_val, 3), bool(is_relevant), category
