import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from urlshortener.adapters.logging import get_logger
from urlshortener.adapters.metrics import get_counters

SUMMARY_LOG_INTERVAL = 10


def _is_redirect_route(request: Request) -> bool:
    """Matches on the route's path *pattern* (e.g. "/{code}"), not the
    resolved request path (which contains the actual code value) - reliable
    regardless of what code was requested, and distinct from other routes
    like /urls/{code}/stats that also start with a similar shape.
    """
    route = request.scope.get("route")
    return getattr(route, "path", None) == "/{code}"


async def logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Logs one structured line per request: method, path, status, duration,
    referrer - deliberately never the request or response body. Domain-level
    4xx (bad input, not found, gone) log at WARNING as expected outcomes, not
    bugs; a genuinely unhandled exception logs at ERROR with a stack trace
    and is then re-raised so Starlette's normal 500 handling still applies.

    Also updates in-memory request counters (NFR5) and periodically logs a
    summary line - counters are never exposed via an endpoint, only logged.
    """
    logger = get_logger()
    counters = get_counters()
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
        counters.record(status_code=500, duration_ms=duration_ms, is_redirect=False)
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

    counters.record(
        status_code=response.status_code,
        duration_ms=duration_ms,
        is_redirect=_is_redirect_route(request),
    )
    if counters.total_requests % SUMMARY_LOG_INTERVAL == 0:
        logger.info("periodic_summary", extra=counters.summary())

    return response
