from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from urlshortener.adapters.db.connection import create_connection
from urlshortener.adapters.sqlite_url_repository import SqliteUrlRepository
from urlshortener.api.dependencies import get_url_repository
from urlshortener.domain.entities import ShortUrl
from urlshortener.main import app

NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


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


def test_redirect_happy_path(client):
    created = client.post("/urls", json={"long_url": "https://example.com/page"}).json()

    response = client.get(f"/{created['code']}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/page"


def test_redirect_records_a_click(client, repository):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()

    client.get(f"/{created['code']}", follow_redirects=False)

    stats = repository.get_stats(created["code"])
    assert stats.total_clicks == 1


def test_redirect_records_referrer_header(client, repository):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()

    client.get(
        f"/{created['code']}",
        follow_redirects=False,
        headers={"Referer": "https://google.com"},
    )

    stats = repository.get_stats(created["code"])
    assert stats.referrer_breakdown["https://google.com"] == 1


def test_redirect_with_no_referrer_header(client, repository):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()

    client.get(f"/{created['code']}", follow_redirects=False)

    stats = repository.get_stats(created["code"])
    assert stats.referrer_breakdown["(none)"] == 1


def test_redirect_unknown_code_returns_404(client):
    response = client.get("/doesnotexist", follow_redirects=False)

    assert response.status_code == 404


def test_redirect_expired_code_returns_410(client, repository):
    """Can't create an already-expired URL via the API (Phase 2 validates
    expires_at must be in the future) - seed directly through the repository
    to test the redirect path's own expiry check independent of creation."""
    repository.save(
        ShortUrl(
            code="exp1234",
            long_url="https://example.com",
            created_at=NOW - timedelta(days=2),
            expires_at=NOW - timedelta(days=1),
        )
    )

    response = client.get("/exp1234", follow_redirects=False)

    assert response.status_code == 410


def test_redirect_deleted_code_returns_410(client, repository):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()
    repository.delete(created["code"], deleted_at=datetime.now(UTC))

    response = client.get(f"/{created['code']}", follow_redirects=False)

    assert response.status_code == 410
