"""Escalation forecasting done honestly (spec §16 / §113-§116, addendum).

Rules the audit insists on:
  * baselines BEFORE any ML (last-value, moving average, historical frequency);
  * TEMPORAL splits, never random, when there is time dependence;
  * report CALIBRATION (Brier score, reliability bins), not just a number;
  * present a probability with its baseline and an explicit uncertainty caveat —
    never "war probability 87%" with no context.

Pure stdlib. The 'model' here is a transparent logistic combination of
observable features; it only earns the name once it beats the baseline in
backtesting (compare_to_baseline()).
"""
from __future__ import annotations

import math

FORECAST_MODEL_VERSION = "0.2.0-baseline"


# --- Baselines -------------------------------------------------------------

def last_value(series: list[float]) -> float:
    return float(series[-1]) if series else 0.0


def moving_average(series: list[float], window: int = 7) -> float:
    if not series:
        return 0.0
    w = series[-window:]
    return sum(w) / len(w)


def historical_frequency(events: int, periods: int) -> float:
    """Base rate = events per period (a probability if periods counts trials)."""
    return events / periods if periods else 0.0


# --- Transparent escalation "model" (baseline+) ----------------------------

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def escalation_probability(features: dict) -> dict:
    """Return a calibrated-ish escalation probability with its baseline.

    features (all optional, sensible defaults):
      recent_event_rate   events/day over last 7d (activity signal)
      ref_rate            reference events/day to normalise against (typically
                          the PRIOR week's rate) — escalation is measured
                          relative to the recent normal, not absolute volume
      risk_slope          change in mean risk over the window (-1..1)
      source_corroboration mean independent-source count (0..N)
      official_alert      bool
      nearby_density      events within radius over window
    """
    # Smooth, non-saturating normalisation: base_rate = rate / (rate + ref).
    # =0 when quiet, =0.5 when activity equals the reference (steady), and
    # trends toward 1 only when activity clearly exceeds the recent normal — so
    # a steady high baseline no longer pins the forecast at 1.0 (v0.1 bug).
    rate = max(0.0, features.get("recent_event_rate", 0.0))
    ref = max(0.001, features.get("ref_rate", 3.0))
    base_rate = rate / (rate + ref)

    # Transparent, documented weights (not a black box).
    z = (
        -1.2
        + 2.0 * base_rate
        + 1.5 * max(0.0, features.get("risk_slope", 0.0))
        + 0.15 * features.get("source_corroboration", 0.0)
        + (0.8 if features.get("official_alert") else 0.0)
        + 0.1 * features.get("nearby_density", 0.0)
    )
    prob = round(_sigmoid(z), 3)
    return {
        "probability": prob,
        "baseline": round(base_rate, 3),
        "model_version": FORECAST_MODEL_VERSION,
        "horizon_hours": features.get("horizon_hours", 168),
        "uncertainty_note": ("Statistical early-warning estimate, not a "
                             "certainty. Compare against the baseline."),
        "drivers": {
            "recent_event_rate": features.get("recent_event_rate", 0.0),
            "risk_slope": features.get("risk_slope", 0.0),
            "source_corroboration": features.get("source_corroboration", 0.0),
            "official_alert": bool(features.get("official_alert")),
        },
    }


# --- Calibration -----------------------------------------------------------

def brier_score(probs: list[float], outcomes: list[int]) -> float:
    """Mean squared error of probabilistic forecasts (0=perfect, 0.25=coinflip)."""
    if not probs or len(probs) != len(outcomes):
        return float("nan")
    return round(sum((p - o) ** 2 for p, o in zip(probs, outcomes, strict=False)) / len(probs), 4)


def reliability_bins(probs: list[float], outcomes: list[int],
                     n_bins: int = 10) -> list[dict]:
    """Reliability diagram data: predicted vs observed frequency per bin."""
    bins = [{"lo": i / n_bins, "hi": (i + 1) / n_bins,
             "count": 0, "sum_pred": 0.0, "sum_obs": 0} for i in range(n_bins)]
    for p, o in zip(probs, outcomes, strict=False):
        idx = min(n_bins - 1, int(p * n_bins))
        bins[idx]["count"] += 1
        bins[idx]["sum_pred"] += p
        bins[idx]["sum_obs"] += o
    out = []
    for b in bins:
        if b["count"]:
            out.append({
                "range": [round(b["lo"], 2), round(b["hi"], 2)],
                "count": b["count"],
                "mean_predicted": round(b["sum_pred"] / b["count"], 3),
                "observed_frequency": round(b["sum_obs"] / b["count"], 3),
            })
    return out


# --- Backtesting -----------------------------------------------------------

def temporal_split(items: list, at_index: int) -> tuple[list, list]:
    """Split a time-ordered list into (train, test) at an index — never random."""
    return items[:at_index], items[at_index:]


def compare_to_baseline(model_probs: list[float], baseline_probs: list[float],
                        outcomes: list[int]) -> dict:
    """A model is only 'better' if it beats the baseline's Brier score."""
    bm = brier_score(model_probs, outcomes)
    bb = brier_score(baseline_probs, outcomes)
    return {
        "model_brier": bm,
        "baseline_brier": bb,
        "model_beats_baseline": bool(bm < bb),
        "improvement": round(bb - bm, 4) if not math.isnan(bm) and not math.isnan(bb) else None,
    }
