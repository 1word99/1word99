import logging
import os
import sys
from datetime import datetime

from loguru import logger


def setup_logging(log_level="INFO"):
    """
    Sets up the global logging configuration for the Osmanli AI application using Loguru.
    Logs messages to a file and to the console.

    Args:
        log_level: The minimum logging level as a string (e.g., "INFO", "DEBUG").
    """
    # Remove default handler to prevent duplicate logs
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time}</green> <level>{level}</level> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Define log file name with current date and time
    log_file_name = datetime.now().strftime("osmanli_ai_%Y-%m-%d_%H-%M-%S.log")
    log_file_path = os.path.join(log_dir, log_file_name)

    # Add file handler
    logger.add(
        log_file_path,
        level=log_level,
        rotation="10 MB",
        compression="zip",
        format="{time} {level} {name}:{function}:{line} - {message}",
    )

    # Redirect standard logging to Loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            logger.opt(depth=6, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logger.info("Logging setup complete with Loguru.")
