import os

DATABASE_PATH = os.environ.get("URLSHORTENER_DB_PATH", "urlshortener.db")
BASE_URL = os.environ.get("URLSHORTENER_BASE_URL", "http://localhost:8000")
