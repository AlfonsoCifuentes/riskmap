"""Security regression tests for the api._db query builder.

Reproduces the audit-addendum finding B1 (SQL injection via query params) and
locks in the fix: identifiers are validated, values are bound as parameters,
and malicious input raises BadRequest (-> HTTP 400) instead of being
concatenated into SQL.

These tests do NOT touch a real database. `_pg_query` is monkeypatched to
capture the SQL string + bound parameters the builder produces.
"""
import pytest

import api._db as db


@pytest.fixture
def captured(monkeypatch):
    """Capture (sql, params) passed to _pg_query; return canned rows."""
    calls = []

    def fake_pg_query(sql, params=None):
        calls.append((sql, params))
        return []

    monkeypatch.setattr(db, "_pg_query", fake_pg_query)
    # Force the direct-SQL path (not PostgREST).
    monkeypatch.setattr(db, "_USE_POSTGREST", False)
    return calls


def test_value_is_bound_not_interpolated(captured):
    db.neon_get("unified_articles", params={"country": "eq.France"},
                select="id,title", limit=5)
    sql, params = captured[-1]
    # The value must be a bound parameter, never inlined into the SQL text.
    assert "%s" in sql
    assert "France" not in sql
    assert "France" in (params or ())


def test_injection_payload_is_bound_and_inert(captured):
    """The exact payload that broke production must now be a harmless bound value."""
    payload = "Israel'||'1'='1"
    db.neon_get("unified_articles", params={"country": f"eq.{payload}"},
                select="id", limit=1)
    sql, params = captured[-1]
    # No fragment of the payload leaks into the SQL string.
    assert "||" not in sql
    assert "'1'='1" not in sql
    assert payload in (params or ())


def test_invalid_filter_column_rejected(captured):
    with pytest.raises(db.BadRequest):
        db.neon_get("unified_articles",
                    params={"country; DROP TABLE unified_articles": "eq.x"})


def test_invalid_table_rejected(captured):
    with pytest.raises(db.BadRequest):
        db.neon_get("unified_articles; DROP TABLE x")


def test_invalid_select_column_rejected(captured):
    with pytest.raises(db.BadRequest):
        db.neon_get("unified_articles", select="id, (SELECT password FROM users)")


def test_invalid_operator_rejected(captured):
    with pytest.raises(db.BadRequest):
        db.neon_get("unified_articles", params={"risk_score": "evil.1"})


def test_invalid_order_column_rejected(captured):
    with pytest.raises(db.BadRequest):
        db.neon_get("unified_articles", order="published_at; DROP TABLE x")


def test_order_direction_bound_from_fixed_set(captured):
    db.neon_get("unified_articles", select="id",
                order="published_at.desc.nullslast", limit=3)
    sql, _ = captured[-1]
    assert "ORDER BY published_at DESC NULLS LAST" in sql


def test_null_operators_still_work(captured):
    db.neon_get("unified_articles",
                params={"latitude": "not.is.null", "longitude": "is.null"},
                select="latitude,longitude")
    sql, params = captured[-1]
    assert "latitude IS NOT NULL" in sql
    assert "longitude IS NULL" in sql


def test_error_from_exc_hides_internals():
    """A DB/driver error must not leak its message to the client."""
    resp = db.error_from_exc(RuntimeError("syntax error at or near ... FROM unified_articles"))
    assert resp["statusCode"] == 500
    assert "unified_articles" not in resp["body"]
    assert "internal server error" in resp["body"]


def test_error_from_exc_bad_request_is_400():
    resp = db.error_from_exc(db.BadRequest("invalid identifier: 'x; DROP'"))
    assert resp["statusCode"] == 400
    assert "DROP" not in resp["body"]
