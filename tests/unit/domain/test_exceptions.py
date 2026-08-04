import pytest

from urlshortener.domain.exceptions import (
    CollisionError,
    DomainError,
    InvalidUrlError,
    UrlDeletedError,
    UrlExpiredError,
    UrlNotFoundError,
)


@pytest.mark.parametrize(
    "exc_type, args",
    [
        (UrlNotFoundError, ("abc1234",)),
        (UrlExpiredError, ("abc1234",)),
        (UrlDeletedError, ("abc1234",)),
        (CollisionError, ("abc1234",)),
    ],
)
def test_code_carrying_exceptions_expose_code_and_message(exc_type, args):
    exc = exc_type(*args)
    assert isinstance(exc, DomainError)
    assert exc.code == "abc1234"
    assert "abc1234" in str(exc)


def test_invalid_url_error_exposes_url_and_reason():
    exc = InvalidUrlError("javascript:alert(1)", "disallowed scheme")
    assert isinstance(exc, DomainError)
    assert exc.url == "javascript:alert(1)"
    assert exc.reason == "disallowed scheme"
    assert "disallowed scheme" in str(exc)


def test_domain_error_is_an_exception():
    assert issubclass(DomainError, Exception)
