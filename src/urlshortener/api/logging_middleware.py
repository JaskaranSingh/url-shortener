import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from urlshortener.adapters.logging import get_logger


async def logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Logs one structured line per request: method, path, status, duration,
    referrer - deliberately never the request or response body. Domain-level
    4xx (bad input, not found, gone) log at WARNING as expected outcomes, not
    bugs; a genuinely unhandled exception logs at ERROR with a stack trace
    and is then re-raised so Starlette's normal 500 handling still applies.
    """
    logger = get_logger()
    start = time.perf_counter()
    referrer = request.headers.get("referer")

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error(
            "unhandled exception",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "referrer": referrer,
            },
            exc_info=True,
        )
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    fields = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "referrer": referrer,
    }
    if response.status_code >= 500:
        logger.error("request completed", extra=fields)
    elif response.status_code >= 400:
        logger.warning("request completed", extra=fields)
    else:
        logger.info("request completed", extra=fields)

    return response
