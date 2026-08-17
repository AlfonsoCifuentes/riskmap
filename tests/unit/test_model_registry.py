"""Tests for the AI model registry (addendum B6).

Loaded directly by file path so the suite stays dependency-light: importing
`src.ai.model_registry` normally would trigger the legacy `src/__init__.py`
eager imports (dotenv, collectors, ...). The registry itself is stdlib-only.
"""
import importlib.util
import pathlib

import pytest

_PATH = pathlib.Path(__file__).resolve().parents[2] / "src" / "ai" / "model_registry.py"


def _load():
    spec = importlib.util.spec_from_file_location("model_registry", _PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reg = _load()


def test_no_default_is_a_retired_model():
    """The single most important invariant: we never ship a dead model ID."""
    for task, model in reg.configured().items():
        if model:  # empty == deliberately disabled
            assert model not in reg.RETIRED_MODEL_IDS, f"{task} -> retired {model}"


def test_defaults_are_current_groq_ids():
    cfg = reg.configured()
    assert cfg["classification"] == "openai/gpt-oss-20b"
    assert cfg["vision"] == ""  # no production Groq vision model -> disabled


def test_env_override(monkeypatch):
    monkeypatch.setenv("RISKMAP_MODEL_CLASSIFIER", "openai/gpt-oss-120b")
    assert reg.get_model("classification") == "openai/gpt-oss-120b"


def test_unknown_task_raises():
    with pytest.raises(KeyError):
        reg.get_model("does_not_exist")


def test_validate_flags_retired(monkeypatch):
    monkeypatch.setenv("RISKMAP_MODEL_CLASSIFIER", "llama-3.1-8b-instant")
    rep = reg.validate(available={"openai/gpt-oss-20b"})
    assert rep["classification"]["status"] == "retired"


def test_validate_unknown_without_key():
    rep = reg.validate(available=set())
    assert rep["classification"]["status"] == "unknown"
    assert rep["vision"]["status"] == "disabled"


def test_fetch_returns_empty_without_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert reg.fetch_groq_model_ids() == set()
