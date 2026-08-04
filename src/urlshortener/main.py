from fastapi import FastAPI

from urlshortener import config
from urlshortener.adapters.logging import configure_logging
from urlshortener.api.error_handlers import register_error_handlers
from urlshortener.api.logging_middleware import logging_middleware
from urlshortener.api.urls_router import router as urls_router

configure_logging(config.LOG_FILE_PATH)

app = FastAPI(title="URL Shortener", version="0.1.0")
app.middleware("http")(logging_middleware)
register_error_handlers(app)
app.include_router(urls_router)
