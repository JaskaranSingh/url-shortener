import pytest
from fastapi.testclient import TestClient

from urlshortener.adapters.db.connection import create_connection
from urlshortener.adapters.sqlite_url_repository import SqliteUrlRepository
from urlshortener.api.dependencies import get_url_repository
from urlshortener.main import app


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


def test_delete_happy_path_returns_204(client):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()

    response = client.delete(f"/urls/{created['code']}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_unknown_code_returns_404(client):
    response = client.delete("/urls/doesnotexist")

    assert response.status_code == 404


def test_delete_already_deleted_code_returns_410(client):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()
    client.delete(f"/urls/{created['code']}")

    response = client.delete(f"/urls/{created['code']}")

    assert response.status_code == 410


def test_deleted_code_then_redirect_returns_410(client):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()

    client.delete(f"/urls/{created['code']}")
    response = client.get(f"/{created['code']}", follow_redirects=False)

    assert response.status_code == 410


def test_delete_does_not_physically_remove_the_row_or_its_clicks(client, repository):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()
    client.get(f"/{created['code']}", follow_redirects=False)  # record a click first

    client.delete(f"/urls/{created['code']}")

    stored = repository.get_by_code(created["code"])
    assert stored is not None
    assert stored.is_deleted is True
    assert repository.get_stats(created["code"]).total_clicks == 1
