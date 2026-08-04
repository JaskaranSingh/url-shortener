from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from urlshortener.domain.exceptions import (
    InvalidExpiryError,
    InvalidUrlError,
    UrlDeletedError,
    UrlExpiredError,
    UrlNotFoundError,
)


def _bad_request_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


def _not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


def _gone_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=410, content={"detail": str(exc)})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(InvalidUrlError, _bad_request_handler)
    app.add_exception_handler(InvalidExpiryError, _bad_request_handler)
    app.add_exception_handler(UrlNotFoundError, _not_found_handler)
    app.add_exception_handler(UrlDeletedError, _gone_handler)
    app.add_exception_handler(UrlExpiredError, _gone_handler)
