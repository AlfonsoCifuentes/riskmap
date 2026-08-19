"""Tests for honest forecasting (spec §16/§113-§116)."""
import math

from src.core import forecasting as fc


def test_baselines():
    assert fc.last_value([1, 2, 3]) == 3
    assert fc.moving_average([2, 4, 6], window=2) == 5
    assert fc.historical_frequency(5, 10) == 0.5
    assert fc.moving_average([]) == 0.0


def test_escalation_probability_bounds_and_baseline():
    quiet = fc.escalation_probability({"recent_event_rate": 0.0})
    hot = fc.escalation_probability({
        "recent_event_rate": 3.0, "risk_slope": 0.5,
        "source_corroboration": 4, "official_alert": True, "nearby_density": 3,
    })
    assert 0 <= quiet["probability"] <= 1
    assert 0 <= hot["probability"] <= 1
    assert hot["probability"] > quiet["probability"]
    assert "baseline" in hot and "uncertainty_note" in hot


def test_brier_score():
    assert fc.brier_score([1.0, 0.0], [1, 0]) == 0.0        # perfect
    assert fc.brier_score([0.5, 0.5], [1, 0]) == 0.25       # coinflip
    assert math.isnan(fc.brier_score([], []))


def test_reliability_bins():
    probs = [0.05, 0.15, 0.85, 0.95]
    outcomes = [0, 0, 1, 1]
    bins = fc.reliability_bins(probs, outcomes, n_bins=10)
    assert all("mean_predicted" in b and "observed_frequency" in b for b in bins)


def test_temporal_split_is_ordered():
    train, test = fc.temporal_split([1, 2, 3, 4, 5], 3)
    assert train == [1, 2, 3] and test == [4, 5]


def test_compare_to_baseline():
    # model closer to truth than baseline -> beats it.
    outcomes = [1, 0, 1, 0]
    model = [0.9, 0.1, 0.8, 0.2]
    baseline = [0.5, 0.5, 0.5, 0.5]
    r = fc.compare_to_baseline(model, baseline, outcomes)
    assert r["model_beats_baseline"] is True
    assert r["model_brier"] < r["baseline_brier"]


def test_steady_high_volume_does_not_saturate():
    """A steady high baseline (rate == ref) must NOT pin the forecast near 1.0 —
    escalation is measured relative to the recent normal (v0.2 fix)."""
    steady = fc.escalation_probability({"recent_event_rate": 20.0, "ref_rate": 20.0})
    # rate==ref -> base_rate 0.5, no slope/corroboration -> well below saturation
    assert steady["baseline"] == 0.5
    assert steady["probability"] < 0.6
    # A genuine surge above the recent normal scores clearly higher.
    surge = fc.escalation_probability({"recent_event_rate": 60.0, "ref_rate": 20.0,
                                       "risk_slope": 0.6})
    assert surge["probability"] > steady["probability"]
    # A calming trend (below the recent normal) scores lower than steady.
    calming = fc.escalation_probability({"recent_event_rate": 5.0, "ref_rate": 20.0})
    assert calming["probability"] < steady["probability"]
