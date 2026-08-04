import logging
from logging.handlers import RotatingFileHandler

from pythonjsonlogger.json import JsonFormatter

LOGGER_NAME = "urlshortener"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


def configure_logging(log_file: str) -> logging.Logger:
    """Configure the app's structured (JSON) file logger.

    Replaces any existing handlers on this logger rather than early-returning
    if already configured - keeps this safe to call repeatedly with a
    different log_file (e.g. once per test with a fresh tmp_path), rather
    than silently keeping stale handlers from a prior call.
    """
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_file, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)
