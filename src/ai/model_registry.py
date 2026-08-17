"""Central AI model registry (addendum B6, spec §4.3 / §95).

Single source of truth for which model each pipeline task uses. Business logic
must NOT hardcode provider model IDs — it calls ``get_model(task)`` here, which
resolves an environment override (``RISKMAP_MODEL_*``) or a currently-valid
default.

Why this exists: every Groq model ID previously hardcoded in the pipeline was
deprecated or decommissioned (``llama-3.1-70b-versatile`` decommissioned,
``llama-3.1-8b-instant`` deprecated 2026-06-17, ``llama-3.2-11b-vision-preview``
retired). A registry lets us swap models via env when the next deprecation lands
— no code change, no dead model shipped.

Defaults verified against Groq's supported-models list (2026-08): the only
production text models are ``openai/gpt-oss-20b`` and ``openai/gpt-oss-120b``.
Groq currently exposes **no** production vision LLM, so the optional CV vision
fallback is DISABLED by default (empty default) and only activates if the
operator sets ``RISKMAP_MODEL_VISION`` to a model they know works.

Stdlib-only so it is safe to import from any context (serverless, jobs, tests).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

# Task -> environment variable that overrides the default model.
_ENV_VAR = {
    "classification": "RISKMAP_MODEL_CLASSIFIER",
    "translation": "RISKMAP_MODEL_TRANSLATOR",
    "summarization": "RISKMAP_MODEL_SUMMARIZER",
    "geocoding_assist": "RISKMAP_MODEL_GEO",
    "vision": "RISKMAP_MODEL_VISION",
}

# Currently-valid defaults (Groq production models, 2026-08).
# Empty string = capability disabled unless the operator opts in via env.
_DEFAULT = {
    "classification": "openai/gpt-oss-20b",
    "translation": "openai/gpt-oss-20b",
    "summarization": "openai/gpt-oss-20b",
    "geocoding_assist": "openai/gpt-oss-20b",
    "vision": "",  # no production Groq vision model at present -> disabled
}

# Known-dead IDs. Used by the doctor/validator to fail loudly if any config or
# leftover code still points at a decommissioned model.
RETIRED_MODEL_IDS = frozenset({
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "llama-3.2-11b-vision-preview",
    "llama-3.2-11b-text-preview",
    "llama-3.2-3b-preview",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma-7b-it",
})

GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"


def get_model(task: str) -> str:
    """Return the model ID for ``task`` (env override or default).

    Returns an empty string for a deliberately-disabled task (e.g. vision).
    Raises KeyError for an unknown task name (programming error)."""
    if task not in _ENV_VAR:
        raise KeyError(f"unknown AI task: {task!r}")
    return os.getenv(_ENV_VAR[task], "").strip() or _DEFAULT[task]


def is_enabled(task: str) -> bool:
    """True if the task has a non-empty model configured."""
    return bool(get_model(task))


def configured() -> dict[str, str]:
    """Snapshot of task -> resolved model (for /api/status, doctor, tests)."""
    return {task: get_model(task) for task in _ENV_VAR}


def fetch_groq_model_ids(api_key: str | None = None, timeout: int = 8) -> set[str]:
    """Fetch the set of model IDs the Groq account can currently use.

    Returns an empty set if no key is available or the call fails — callers
    treat that as 'cannot validate', not 'invalid'."""
    api_key = api_key or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return set()
    req = urllib.request.Request(
        GROQ_MODELS_URL, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        return {m.get("id") for m in data.get("data", []) if m.get("id")}
    except (urllib.error.URLError, ValueError, KeyError):
        return set()


def validate(available: set[str] | None = None) -> dict[str, dict]:
    """Validate configured models against what the provider actually offers.

    Each entry: {model, retired, available, status}. ``status`` is one of
    ``ok`` / ``disabled`` / ``retired`` / ``unknown`` / ``unavailable``.
    When ``available`` is empty (no key), provider availability is 'unknown'
    but retired-ID detection still works offline."""
    if available is None:
        available = fetch_groq_model_ids()
    report: dict[str, dict] = {}
    for task, model in configured().items():
        if not model:
            report[task] = {"model": "", "retired": False,
                            "available": None, "status": "disabled"}
            continue
        retired = model in RETIRED_MODEL_IDS
        if retired:
            status = "retired"
        elif not available:
            status = "unknown"
        elif model in available:
            status = "ok"
        else:
            status = "unavailable"
        report[task] = {
            "model": model,
            "retired": retired,
            "available": (model in available) if available else None,
            "status": status,
        }
    return report
