from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse

from urlshortener import config
from urlshortener.api.dependencies import (
    get_create_short_url_service,
    get_delete_url_service,
    get_redirect_service,
    get_stats_service,
)
from urlshortener.api.schemas import CreateUrlRequest, CreateUrlResponse, StatsResponse
from urlshortener.application.create_short_url_service import CreateShortUrlService
from urlshortener.application.delete_url_service import DeleteUrlService
from urlshortener.application.redirect_service import RedirectService
from urlshortener.application.stats_service import StatsService

router = APIRouter()


@router.post("/urls", response_model=CreateUrlResponse, status_code=status.HTTP_201_CREATED)
def create_url(
    request: CreateUrlRequest,
    service: CreateShortUrlService = Depends(get_create_short_url_service),
) -> CreateUrlResponse:
    now = datetime.now(UTC)
    short_url = service.execute(request.long_url, now=now, expires_at=request.expires_at)
    return CreateUrlResponse(
        code=short_url.code,
        short_url=f"{config.BASE_URL}/{short_url.code}",
        long_url=short_url.long_url,
        created_at=short_url.created_at,
        expires_at=short_url.expires_at,
    )


@router.get("/{code}")
def redirect(
    code: str,
    request: Request,
    service: RedirectService = Depends(get_redirect_service),
) -> RedirectResponse:
    now = datetime.now(UTC)
    # HTTP's header is spelled "Referer" (a long-standing historical typo in
    # the spec itself); header lookup is case-insensitive but not
    # spelling-insensitive - our domain/schema use the correct "referrer".
    referrer = request.headers.get("referer")
    long_url = service.execute(code, now=now, referrer=referrer)
    return RedirectResponse(url=long_url, status_code=status.HTTP_302_FOUND)


@router.delete("/urls/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url(
    code: str,
    service: DeleteUrlService = Depends(get_delete_url_service),
) -> None:
    now = datetime.now(UTC)
    service.execute(code, now=now)


@router.get("/urls/{code}/stats", response_model=StatsResponse)
def get_stats(
    code: str,
    service: StatsService = Depends(get_stats_service),
) -> StatsResponse:
    stats = service.execute(code)
    return StatsResponse(
        code=stats.code,
        total_clicks=stats.total_clicks,
        last_accessed=stats.last_accessed,
        referrer_breakdown=stats.referrer_breakdown,
    )
