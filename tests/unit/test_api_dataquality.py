"""Pure-logic test for the data-quality endpoint helper (hyphenated module
name -> loaded by file path)."""
import importlib.util
import pathlib


def _load():
    p = pathlib.Path(__file__).resolve().parents[2] / "api" / "data-quality.py"
    spec = importlib.util.spec_from_file_location("data_quality", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pct_helper():
    mod = _load()
    assert mod._pct(50, 100) == 50.0
    assert mod._pct(1, 3) == 33.3
    assert mod._pct(0, 0) is None
    assert mod._pct(None, 10) == 0.0
