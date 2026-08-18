"""Tests for CV benchmark metrics + registry (spec §10)."""
from src.core import cv_benchmark as cv


def test_precision_recall_f1():
    assert cv.precision(80, 20) == 0.8
    assert cv.recall(80, 20) == 0.8
    assert cv.f1(80, 20, 20) == 0.8
    assert cv.precision(0, 0) == 0.0


def test_metrics_from_confusion():
    m = cv.metrics_from_confusion(90, 10, 30)
    assert m["precision"] == 0.9
    assert m["recall"] == 0.75
    assert 0 < m["f1"] < 1


def test_registry_loads_and_is_labelled_benchmark():
    reg = cv.load_registry()
    assert reg["data_kind"] == "BENCHMARK"
    assert reg["models"], "expected benchmark models"
    for m in reg["models"]:
        assert m["provenance"] == "published_baseline"  # honest attribution
        assert "macro_f1" in m
        for c in m["classes"]:
            # derived metrics recomputed from confusion counts
            assert 0 <= c["f1"] <= 1
