import logging

import pytest
from fastapi.testclient import TestClient

from urlshortener.adapters.db.connection import create_connection
from urlshortener.adapters.logging import configure_logging
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
def client(repository, tmp_path):
    configure_logging(str(tmp_path / "test.log"))
    app.dependency_overrides[get_url_repository] = lambda: repository
    # raise_server_exceptions=False: an unhandled exception should surface to
    # a real caller as an actual 500 response, not blow up the test process -
    # matches how the middleware's re-raise is meant to be handled downstream
    # by Starlette's default error handling, not by the test client itself.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _urlshortener_records(caplog):
    return [r for r in caplog.records if r.name == "urlshortener"]


def test_successful_create_is_logged_at_info_with_no_body(client, caplog):
    with caplog.at_level(logging.INFO, logger="urlshortener"):
        client.post("/urls", json={"long_url": "https://example.com"})

    records = _urlshortener_records(caplog)
    assert len(records) == 1
    record = records[0]
    assert record.levelname == "INFO"
    assert record.method == "POST"
    assert record.path == "/urls"
    assert record.status_code == 201
    assert isinstance(record.duration_ms, float)
    assert not hasattr(record, "long_url")
    assert not hasattr(record, "body")


def test_successful_redirect_is_logged_at_info(client, caplog):
    created = client.post("/urls", json={"long_url": "https://example.com"}).json()
    caplog.clear()  # the setup POST above also logs - isolate the GET under test

    with caplog.at_level(logging.INFO, logger="urlshortener"):
        client.get(f"/{created['code']}", follow_redirects=False)

    records = _urlshortener_records(caplog)
    assert len(records) == 1
    assert records[0].status_code == 302
    assert records[0].path == f"/{created['code']}"


def test_unknown_code_is_logged_at_warning_not_error(client, caplog):
    with caplog.at_level(logging.INFO, logger="urlshortener"):
        client.get("/doesnotexist", follow_redirects=False)

    records = _urlshortener_records(caplog)
    assert len(records) == 1
    assert records[0].levelname == "WARNING"
    assert records[0].status_code == 404


def test_malformed_url_is_logged_at_warning(client, caplog):
    with caplog.at_level(logging.INFO, logger="urlshortener"):
        client.post("/urls", json={"long_url": "javascript:alert(1)"})

    records = _urlshortener_records(caplog)
    assert len(records) == 1
    assert records[0].levelname == "WARNING"
    assert records[0].status_code == 400


def test_unhandled_exception_is_logged_at_error_with_traceback_and_still_returns_500(
    client, repository, monkeypatch, caplog
):
    def _boom(code):
        raise RuntimeError("simulated bug")

    monkeypatch.setattr(repository, "get_by_code", _boom)

    with caplog.at_level(logging.INFO, logger="urlshortener"):
        response = client.get("/whatever", follow_redirects=False)

    assert response.status_code == 500
    records = _urlshortener_records(caplog)
    assert len(records) == 1
    assert records[0].levelname == "ERROR"
    assert records[0].exc_info is not None
