"""Logging configuration for Job Matcher Application."""

import logging
import sys

def setup_logging(debug: bool = True) -> logging.Logger:
    """Configures structured logging across the application."""
    log_level = logging.DEBUG if debug else logging.INFO

    # Root logger format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Suppress excessive external library noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger("job_matcher")
    logger.setLevel(log_level)
    return logger

logger = setup_logging()
