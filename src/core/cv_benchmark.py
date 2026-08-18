"""CV model registry + benchmark metrics (spec §9-§11 / §95, addendum B).

RiskMap does NOT claim live high-resolution detection from coarse satellites.
Computer-vision capability is demonstrated honestly as REPLAY/BENCHMARK against
public datasets (xView / xBD / SpaceNet), with real evaluation metrics and model
cards. This module holds the metric math (pure) and the model registry loader.

metrics fixture lives in `models/cv_benchmarks.json` (data, not code) so it can
be regenerated when a model is retrained.
"""
from __future__ import annotations

import json
import os

BENCHMARKS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "benchmarks", "cv_benchmarks.json",
)


def precision(tp: int, fp: int) -> float:
    return round(tp / (tp + fp), 4) if (tp + fp) else 0.0


def recall(tp: int, fn: int) -> float:
    return round(tp / (tp + fn), 4) if (tp + fn) else 0.0


def f1(tp: int, fp: int, fn: int) -> float:
    p, r = precision(tp, fp), recall(tp, fn)
    return round(2 * p * r / (p + r), 4) if (p + r) else 0.0


def metrics_from_confusion(tp: int, fp: int, fn: int) -> dict:
    return {"precision": precision(tp, fp), "recall": recall(tp, fn),
            "f1": f1(tp, fp, fn), "tp": tp, "fp": fp, "fn": fn}


def load_registry() -> dict:
    """Return the CV model registry + benchmark metrics (marked BENCHMARK).

    Degrades to an empty registry if the fixture is absent, so callers never
    crash — they show 'no benchmarks yet'."""
    if not os.path.isfile(BENCHMARKS_PATH):
        return {"data_kind": "BENCHMARK", "models": []}
    with open(BENCHMARKS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # Recompute derived metrics from confusion counts so the file can store
    # raw counts and the API always shows consistent precision/recall/F1.
    for m in data.get("models", []):
        for cls in m.get("classes", []):
            if all(k in cls for k in ("tp", "fp", "fn")):
                cls.update(metrics_from_confusion(cls["tp"], cls["fp"], cls["fn"]))
        classes = m.get("classes", [])
        if classes:
            m["macro_f1"] = round(
                sum(c.get("f1", 0) for c in classes) / len(classes), 4)
    data["data_kind"] = "BENCHMARK"
    return data
