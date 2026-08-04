from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from urlshortener.domain.exceptions import InvalidExpiryError, InvalidUrlError


def _bad_request_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(InvalidUrlError, _bad_request_handler)
    app.add_exception_handler(InvalidExpiryError, _bad_request_handler)
