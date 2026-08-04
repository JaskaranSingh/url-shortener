import sqlite3
from collections.abc import Iterator

from fastapi import Depends

from urlshortener import config
from urlshortener.adapters.db.connection import create_connection
from urlshortener.adapters.sqlite_url_repository import SqliteUrlRepository
from urlshortener.application.create_short_url_service import CreateShortUrlService
from urlshortener.application.redirect_service import RedirectService
from urlshortener.application.short_code_generator import ShortCodeGenerator
from urlshortener.domain.repository import UrlRepository


def get_db_connection() -> Iterator[sqlite3.Connection]:
    conn = create_connection(config.DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()


def get_url_repository(
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> UrlRepository:
    return SqliteUrlRepository(conn)


def get_code_generator() -> ShortCodeGenerator:
    return ShortCodeGenerator()


def get_create_short_url_service(
    repository: UrlRepository = Depends(get_url_repository),
    code_generator: ShortCodeGenerator = Depends(get_code_generator),
) -> CreateShortUrlService:
    return CreateShortUrlService(repository=repository, code_generator=code_generator)


def get_redirect_service(
    repository: UrlRepository = Depends(get_url_repository),
) -> RedirectService:
    return RedirectService(repository=repository)
