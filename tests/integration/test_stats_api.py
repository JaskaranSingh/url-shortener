from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from urlshortener.adapters.db.connection import create_connection
from urlshortener.adapters.sqlite_url_repository import SqliteUrlRepository
from urlshortener.api.dependencies import get_url_repository
from urlshortener.domain.entities import ShortUrl
from urlshortener.main import app

NOW = datetime(2026, 8, 5, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def repository(tmp_path):
    conn = create_connection(str(tmp_path / "test.db"))
    repo = SqliteUrlRepository(conn)
    yield repo
    conn.close()


@pytest.fixture
def client(repository):
    app.dependency_overrides[get_url_repository] = lambda: repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_stats_happy_path(client):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()
    code = created["code"]

    client.get(f"/{code}", follow_redirects=False, headers={"Referer": "https://google.com"})
    client.get(f"/{code}", follow_redirects=False, headers={"Referer": "https://google.com"})
    client.get(f"/{code}", follow_redirects=False)

    response = client.get(f"/urls/{code}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == code
    assert body["total_clicks"] == 3
    assert body["referrer_breakdown"]["https://google.com"] == 2
    assert body["referrer_breakdown"]["(none)"] == 1
    assert body["last_accessed"] is not None


def test_stats_for_code_with_no_clicks_yet(client):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()

    response = client.get(f"/urls/{created['code']}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_clicks"] == 0
    assert body["last_accessed"] is None
    assert body["referrer_breakdown"] == {}


def test_stats_unknown_code_returns_404(client):
    response = client.get("/urls/doesnotexist/stats")

    assert response.status_code == 404


def test_stats_deleted_code_returns_410(client):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()
    client.delete(f"/urls/{created['code']}")

    response = client.get(f"/urls/{created['code']}/stats")

    assert response.status_code == 410


def test_stats_still_available_for_expired_code(client, repository):
    """Can't create an already-expired URL via the API - seed directly,
    same technique as the Phase 5 expired-redirect test."""
    repository.save(
        ShortUrl(
            code="exp1234",
            long_url="https://example.com",
            created_at=NOW - timedelta(days=2),
            expires_at=NOW - timedelta(days=1),
        )
    )
    repository.record_click(
        "exp1234", clicked_at=NOW - timedelta(days=1, minutes=-30), referrer=None
    )

    response = client.get("/urls/exp1234/stats")

    assert response.status_code == 200
    assert response.json()["total_clicks"] == 1
