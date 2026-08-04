from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status

from urlshortener import config
from urlshortener.api.dependencies import get_create_short_url_service
from urlshortener.api.schemas import CreateUrlRequest, CreateUrlResponse
from urlshortener.application.create_short_url_service import CreateShortUrlService

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
