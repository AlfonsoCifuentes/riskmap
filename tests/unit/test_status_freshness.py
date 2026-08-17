"""Freshness SLA logic for /api/status (addendum B4, spec §1.2)."""
import importlib

status = importlib.import_module("api.status")


def test_freshness_levels():
    f = status._freshness
    assert f(None) == "offline"
    assert f(0) == "healthy"
    assert f(2 * 3600) == "healthy"        # < 3h
    assert f(5 * 3600) == "warning"        # 3-8h
    assert f(12 * 3600) == "degraded"      # 8-24h
    assert f(48 * 3600) == "stale"         # > 24h


def test_boundaries():
    f = status._freshness
    assert f(3 * 3600) == "warning"        # exactly 3h -> not healthy
    assert f(8 * 3600) == "degraded"       # exactly 8h -> not warning
    assert f(24 * 3600) == "stale"         # exactly 24h -> stale
