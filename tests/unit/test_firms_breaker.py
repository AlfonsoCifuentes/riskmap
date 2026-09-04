"""FIRMS connectivity breaker + image expiry (imagery pipeline cost controls).

Both guards exist because of observed production behaviour, so they are worth
pinning: an unroutable FIRMS host used to cost ~12 min of every 15 min imagery
run, and images stored without `expires_at` grew the table ~150 rows/day until
the database transfer quota was exhausted.
"""
import pytest
import requests

from src.pipeline import acquire_images as ai


@pytest.fixture(autouse=True)
def _reset_breaker(monkeypatch):
    """Each test starts with a closed breaker and a usable MAP_KEY."""
    monkeypatch.setenv('NASA_FIRMS_MAP_KEY', 'test-key')
    ai._firms_conn_failures = 0
    yield
    ai._firms_conn_failures = 0


def _always_fail(exc):
    calls = []

    def _get(*args, **kwargs):
        calls.append(kwargs.get('timeout'))
        raise exc

    return calls, _get


def test_breaker_stops_retrying_unreachable_host(monkeypatch):
    calls, get = _always_fail(requests.exceptions.ConnectionError('unreachable'))
    monkeypatch.setattr(ai.requests, 'get', get)

    for _ in range(20):
        assert ai.fetch_firms_hotspots(10.0, 20.0) == []

    # 20 AOIs must not mean 20 dead connection attempts.
    assert len(calls) == ai._FIRMS_MAX_CONN_FAILURES
    assert ai._firms_unreachable()


def test_breaker_counts_timeouts_too(monkeypatch):
    calls, get = _always_fail(requests.exceptions.Timeout('timed out'))
    monkeypatch.setattr(ai.requests, 'get', get)

    for _ in range(10):
        ai.fetch_firms_hotspots(10.0, 20.0)

    assert len(calls) == ai._FIRMS_MAX_CONN_FAILURES


def test_connect_timeout_is_short():
    """A host that cannot be routed to should fail fast, not after 30s."""
    connect, _read = ai._FIRMS_TIMEOUT
    assert connect <= 10


def test_parse_errors_do_not_trip_the_breaker(monkeypatch):
    """Only connectivity disables the source; a bad payload is not that."""
    calls, get = _always_fail(ValueError('malformed csv'))
    monkeypatch.setattr(ai.requests, 'get', get)

    for _ in range(5):
        ai.fetch_firms_hotspots(10.0, 20.0)

    assert len(calls) == 5
    assert not ai._firms_unreachable()


def test_missing_key_short_circuits_before_any_request(monkeypatch):
    monkeypatch.delenv('NASA_FIRMS_MAP_KEY', raising=False)
    calls, get = _always_fail(AssertionError('must not be called'))
    monkeypatch.setattr(ai.requests, 'get', get)

    assert ai.fetch_firms_hotspots(10.0, 20.0) == []
    assert calls == []


def test_stored_images_get_an_expiry(monkeypatch):
    monkeypatch.setenv('IMAGE_RETENTION_DAYS', '30')
    assert ai._expiry_timestamp() is not None


def test_expiry_can_be_disabled(monkeypatch):
    """0 keeps frames forever — retention then matches no rows, by choice."""
    monkeypatch.setenv('IMAGE_RETENTION_DAYS', '0')
    assert ai._expiry_timestamp() is None


def test_invalid_retention_falls_back_to_default(monkeypatch):
    monkeypatch.setenv('IMAGE_RETENTION_DAYS', 'not-a-number')
    assert ai._retention_days() == 30
    assert ai._expiry_timestamp() is not None


def test_expiry_is_in_the_future(monkeypatch):
    from datetime import datetime

    monkeypatch.setenv('IMAGE_RETENTION_DAYS', '7')
    assert datetime.fromisoformat(ai._expiry_timestamp()) > datetime.utcnow()
