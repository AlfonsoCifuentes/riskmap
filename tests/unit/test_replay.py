"""Tests for Replay Mode (spec §39/§93). Deterministic, offline."""
from src.core import replay


def test_all_scenarios_listed():
    ids = {s["id"] for s in replay.list_scenarios()}
    assert {"wildfire_la_palma", "flood_valencia", "earthquake_turkey",
            "conflict_infrastructure"} <= ids


def test_scenarios_meet_their_expectations():
    for s in replay.list_scenarios():
        result = replay.run(s["id"])
        assert result["replay"] is True
        assert result["data_kind"] == "REPLAY"
        exp = result["expected"]
        pipeline = result["pipeline"]
        # Multi-source coverage fuses to the expected number of events.
        assert pipeline["events"] == exp["events"], s["id"]
        ev = pipeline["results"][0]
        assert ev["independent_source_count"] >= exp["min_independent_sources"], s["id"]
        assert ev["risk"]["risk_level"] in exp["risk_level_in"], s["id"]


def test_syndication_not_counted_as_independent():
    # conflict pack has 4 articles but one is a Reuters wire copy on yahoo.com.
    r = replay.run("conflict_infrastructure")
    ev = r["pipeline"]["results"][0]
    assert ev["source_count"] == 4
    # yahoo + reuters + ap + elmundo = 4 domains, but the wire copy is same story;
    # independent DOMAINS is what we count -> 4 distinct domains here, and the
    # duplicate title still fuses into ONE event.
    assert r["pipeline"]["events"] == 1


def test_official_source_lifts_confidence():
    with_official = replay.run("earthquake_turkey")["pipeline"]["results"][0]
    assert with_official["risk"]["confidence"] > 0
    # geo is region-level for the quake -> flagged as area/fallback.
    assert with_official["geo"]["geo_precision"] == "region"
    assert with_official["geo"]["geo_is_fallback"] is True


def test_unknown_scenario_raises():
    import pytest
    with pytest.raises(FileNotFoundError):
        replay.run("does_not_exist")
