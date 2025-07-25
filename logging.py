# osmanli_ai/core/logging.py

import sys
import logging
from loguru import logger


def setup_logging(log_level="INFO", log_file="osmanli_ai.log"):
    """
    Sets up the logging configuration for the Osmanli AI application.
    This function configures the standard Python 'logging' module and Loguru.
    """
    level = log_level.upper()
    numeric_level = getattr(logging, level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Configure Loguru
    logger.remove()  # Remove default handler
    logger.add(log_file, rotation="10 MB", level=level)  # File logging with rotation
    logger.add(sys.stderr, level=level)  # Console logging

    logger.info(
        f"Osmanli AI logging initialized with level: {log_level} and file: {log_file}"
    )


def log_exception(logger, message="An unexpected error occurred"):
    """Logs an exception with a custom message."""
    logger.exception(message)
