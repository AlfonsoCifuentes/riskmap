"""Evaluation harness: pin the relevance filter's precision/recall on a small
hand-labelled gold set (spec §167). This is a *quality gate*, not a unit test of
one case — if a lexicon change quietly wrecks precision or recall, CI fails.

The gold set (tests/data/relevance_gold.jsonl) is synthetic, representative
copy (no copyrighted source text), balanced across conflict/disaster (relevant)
and sport/entertainment/business/lifestyle (off-topic).
"""
import json
import pathlib

from src.core import relevance

GOLD = pathlib.Path(__file__).parent.parent / "data" / "relevance_gold.jsonl"


def _load():
    rows = []
    with open(GOLD, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _metrics():
    rows = _load()
    tp = fp = tn = fn = 0
    for r in rows:
        pred = relevance.score(r["text"])[1]
        gold = bool(r["relevant"])
        if pred and gold:
            tp += 1
        elif pred and not gold:
            fp += 1
        elif not pred and not gold:
            tn += 1
        else:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1, (tp, fp, tn, fn)


def test_gold_set_is_balanced_and_nonempty():
    rows = _load()
    assert len(rows) >= 20
    pos = sum(1 for r in rows if r["relevant"])
    assert 0 < pos < len(rows)  # both classes present


def test_relevance_precision_recall_thresholds():
    precision, recall, f1, (tp, fp, tn, fn) = _metrics()
    # A conflict/disaster monitor must keep precision high (few off-topic leaks)
    # while retaining strong recall on genuine events.
    assert precision >= 0.90, f"precision {precision:.2f} (fp={fp})"
    assert recall >= 0.90, f"recall {recall:.2f} (fn={fn})"
    assert f1 >= 0.90, f"F1 {f1:.2f}"
