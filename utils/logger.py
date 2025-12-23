"""
Logging configuration module.
Provides structured logging with file-based handlers and configurable levels.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: str = "logs",
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    log_format: Optional[str] = None
) -> None:
    """
    Configure application-wide logging.
    
    Args:
        log_dir: Directory for log files
        console_level: Minimum log level for console output (INFO, WARNING, ERROR, etc.)
        file_level: Minimum log level for file output (typically DEBUG for full logs)
        log_format: Custom log format string. If None, uses default structured format.
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    date_format = "%Y-%m-%d %H:%M:%S"
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper(), logging.INFO))
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    app_file_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    app_file_handler.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))
    file_formatter = logging.Formatter(log_format, date_format)
    app_file_handler.setFormatter(file_formatter)
    root_logger.addHandler(app_file_handler)
    
    error_file_handler = RotatingFileHandler(
        log_path / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_file_handler)
    
    _suppress_third_party_logs()


def _suppress_third_party_logs() -> None:
    """Suppress verbose logging from third-party libraries."""
    third_party_loggers = [
        'httpx',
        'httpcore',
        'openai',
        'openai._base_client',
        'urllib3',
        'requests',
    ]
    
    for logger_name in third_party_loggers:
        lib_logger = logging.getLogger(logger_name)
        lib_logger.setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def configure_from_env() -> None:
    """Configure logging from environment variables."""
    log_dir = os.getenv("LOG_DIR", "logs")
    console_level = os.getenv("LOG_CONSOLE_LEVEL", "INFO")
    file_level = os.getenv("LOG_FILE_LEVEL", "DEBUG")
    
    setup_logging(
        log_dir=log_dir,
        console_level=console_level,
        file_level=file_level
    )
