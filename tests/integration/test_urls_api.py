from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from urlshortener import config
from urlshortener.adapters.db.connection import create_connection
from urlshortener.adapters.sqlite_url_repository import SqliteUrlRepository
from urlshortener.api.dependencies import get_url_repository
from urlshortener.main import app

NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = create_connection(db_path)
    repository = SqliteUrlRepository(conn)

    app.dependency_overrides[get_url_repository] = lambda: repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    conn.close()


def test_create_url_happy_path(client):
    response = client.post("/urls", json={"long_url": "https://example.com/page"})

    assert response.status_code == 201
    body = response.json()
    assert len(body["code"]) == 7
    assert body["short_url"].endswith(f"/{body['code']}")
    assert body["long_url"] == "https://example.com/page"
    assert body["expires_at"] is None
    assert "created_at" in body


def test_create_url_with_future_expiry(client):
    expires_at = NOW + timedelta(days=7)

    response = client.post(
        "/urls", json={"long_url": "https://example.com", "expires_at": expires_at.isoformat()}
    )

    assert response.status_code == 201
    # compare parsed datetimes, not raw strings - Pydantic v2 serializes UTC
    # as a "Z" suffix, which is a different (equally valid) ISO 8601 spelling
    assert datetime.fromisoformat(response.json()["expires_at"]) == expires_at


def test_two_consecutive_creates_return_different_codes(client):
    first = client.post("/urls", json={"long_url": "https://example.com/one"})
    second = client.post("/urls", json={"long_url": "https://example.com/two"})

    assert first.json()["code"] != second.json()["code"]


@pytest.mark.parametrize(
    "long_url",
    [
        "javascript:alert(1)",
        "not-a-url",
        "ftp://example.com/file",
        "http://",
    ],
)
def test_create_url_rejects_malformed_url(client, long_url):
    response = client.post("/urls", json={"long_url": long_url})

    assert response.status_code == 400
    assert "detail" in response.json()


def test_create_url_rejects_expiry_in_the_past(client):
    past = (NOW - timedelta(days=1)).isoformat()

    response = client.post("/urls", json={"long_url": "https://example.com", "expires_at": past})

    assert response.status_code == 400


def test_create_url_rejects_naive_expiry_datetime(client):
    """No timezone offset - request-shape validation, so FastAPI's standard 422,
    not our domain-level 400 (that's reserved for business-rule violations)."""
    response = client.post(
        "/urls",
        json={"long_url": "https://example.com", "expires_at": "2027-01-01T00:00:00"},
    )

    assert response.status_code == 422


def test_create_url_missing_long_url_field(client):
    response = client.post("/urls", json={})

    assert response.status_code == 422


def test_create_url_through_the_real_dependency_chain(tmp_path, monkeypatch):
    """Every other test overrides get_url_repository directly, bypassing the
    real per-request get_db_connection -> get_url_repository chain entirely.
    That chain is exactly where a real cross-thread SQLite bug was caught
    during this phase (see connection.py's check_same_thread note) - so it
    needs its own test that exercises it for real, unmocked.
    """
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "real_chain.db"))

    with TestClient(app) as test_client:
        response = test_client.post("/urls", json={"long_url": "https://example.com"})

    assert response.status_code == 201
    assert len(response.json()["code"]) == 7
