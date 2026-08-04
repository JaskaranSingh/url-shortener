from fastapi import FastAPI

from urlshortener.api.error_handlers import register_error_handlers
from urlshortener.api.urls_router import router as urls_router

app = FastAPI(title="URL Shortener", version="0.1.0")
register_error_handlers(app)
app.include_router(urls_router)
