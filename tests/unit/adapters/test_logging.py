import json
import logging
from logging.handlers import RotatingFileHandler

from urlshortener.adapters.logging import configure_logging, get_logger


def test_configure_logging_attaches_a_rotating_file_handler(tmp_path):
    logger = configure_logging(str(tmp_path / "app.log"))

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], RotatingFileHandler)
    assert logger.level == logging.INFO


def test_configure_logging_replaces_handlers_on_repeated_calls(tmp_path):
    configure_logging(str(tmp_path / "first.log"))
    logger = configure_logging(str(tmp_path / "second.log"))

    assert len(logger.handlers) == 1
    assert logger.handlers[0].baseFilename.endswith("second.log")


def test_get_logger_returns_the_same_configured_logger(tmp_path):
    configured = configure_logging(str(tmp_path / "app.log"))
    fetched = get_logger()

    assert fetched is configured


def test_log_output_is_valid_json_with_extra_fields(tmp_path):
    log_path = tmp_path / "app.log"
    logger = configure_logging(str(log_path))

    logger.info("request completed", extra={"method": "GET", "status_code": 200})
    for handler in logger.handlers:
        handler.flush()

    line = log_path.read_text().strip().splitlines()[-1]
    record = json.loads(line)

    assert record["message"] == "request completed"
    assert record["method"] == "GET"
    assert record["status_code"] == 200
    assert record["levelname"] == "INFO"
