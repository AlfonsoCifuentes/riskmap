"""Deterministic Replay Mode (spec §39 / §93, addendum).

Runs curated scenario packs through the REAL core pipeline (dedup -> fusion ->
geo -> risk) so the whole system can be demonstrated without any external API,
disaster, or live data. Output is deterministic and unambiguously labelled
REPLAY — never presented as live (spec §8, §93.2).

A scenario pack lives in `scenarios/<id>/`:
    manifest.json   -- id, title, hazard, description, expected outputs
    articles.json   -- list of evidence items (multi-source, spatiotemporal)

The loader is generic: drop in a new folder and it becomes available.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from src.core import events as event_fusion
from src.core import geo, risk

SCENARIOS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "scenarios",
)

# Hazard -> default geo precision + severity prior (kept explicit & auditable).
_HAZARD_DEFAULTS = {
    "wildfire": {"precision": "city", "severity": 0.7},
    "flood": {"precision": "city", "severity": 0.65},
    "earthquake": {"precision": "region", "severity": 0.8},
    "armed_conflict": {"precision": "city", "severity": 0.85},
}


def list_scenarios() -> list[dict]:
    """Return manifest summaries for all available scenario packs."""
    out = []
    if not os.path.isdir(SCENARIOS_DIR):
        return out
    for name in sorted(os.listdir(SCENARIOS_DIR)):
        man = os.path.join(SCENARIOS_DIR, name, "manifest.json")
        if os.path.isfile(man):
            with open(man, encoding="utf-8") as f:
                m = json.load(f)
            out.append({
                "id": m.get("id", name),
                "title": m.get("title"),
                "hazard": m.get("hazard"),
                "description": m.get("description"),
            })
    return out


def _load_pack(scenario_id: str) -> dict:
    folder = os.path.join(SCENARIOS_DIR, scenario_id)
    man_path = os.path.join(folder, "manifest.json")
    art_path = os.path.join(folder, "articles.json")
    if not (os.path.isfile(man_path) and os.path.isfile(art_path)):
        raise FileNotFoundError(f"unknown replay scenario: {scenario_id!r}")
    with open(man_path, encoding="utf-8") as f:
        manifest = json.load(f)
    with open(art_path, encoding="utf-8") as f:
        articles = json.load(f)
    return {"manifest": manifest, "articles": articles}


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def run(scenario_id: str) -> dict:
    """Execute a scenario through the core pipeline and return a deterministic,
    stage-by-stage result. Every payload is flagged replay=True."""
    pack = _load_pack(scenario_id)
    manifest = pack["manifest"]
    hazard = manifest.get("hazard", "")
    defaults = _HAZARD_DEFAULTS.get(hazard, {"precision": "city", "severity": 0.6})

    # Normalise evidence timestamps for fusion.
    articles = []
    for a in pack["articles"]:
        a = dict(a)
        a["published_at"] = _parse_dt(a.get("published_at"))
        articles.append(a)

    # Stage 1: event fusion.
    fused = event_fusion.fuse(articles)

    # Stages 2-3: geolocation + risk per event.
    result_events = []
    for ev in fused:
        rep = ev["representative"]
        lat, lon = rep.get("latitude"), rep.get("longitude")
        precision = rep.get("geo_precision") or defaults["precision"]
        geo_res = geo.resolve(
            precision=precision, latitude=lat, longitude=lon,
            method="replay_fixture",
            source_count=ev["independent_source_count"],
            has_official_source=any(e.get("official") for e in ev["evidence"]),
        )
        severity = rep.get("severity", defaults["severity"])
        assessment = risk.assess(
            severity=severity,
            exposure=rep.get("exposure", 0.5),
            vulnerability=rep.get("vulnerability", 0.5),
            independent_source_count=ev["independent_source_count"],
            has_official_source=any(e.get("official") for e in ev["evidence"]),
            geo_confidence=geo_res.geo_confidence if geo_res else 0.4,
        )
        result_events.append({
            "title": rep.get("title"),
            "category": ev["category"] or hazard,
            "source_count": ev["source_count"],
            "independent_source_count": ev["independent_source_count"],
            "geo": geo_res.as_dict() if geo_res else None,
            "risk": assessment.as_dict(),
            "evidence": [
                {"source": e.get("source"), "url": e.get("url"),
                 "title": e.get("title"), "official": bool(e.get("official"))}
                for e in ev["evidence"]
            ],
        })

    return {
        "replay": True,
        "data_kind": "REPLAY",
        "scenario": {
            "id": manifest.get("id", scenario_id),
            "title": manifest.get("title"),
            "hazard": hazard,
            "description": manifest.get("description"),
        },
        "pipeline": {
            "raw_evidence": len(articles),
            "events": len(result_events),
            "results": result_events,
        },
        "expected": manifest.get("expected", {}),
    }
