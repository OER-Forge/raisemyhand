"""
Centralized logging configuration for RaiseMyHand
Provides structured logging with different handlers for development and production
"""
import logging
import logging.handlers
import sys
import os
from pathlib import Path
from config import settings


def setup_logging():
    """
    Configure centralized logging system.

    Development:
      - Console output with colors
      - INFO level
      - Simple format

    Production:
      - Console output (for Docker logs)
      - File rotation (logs/app.log)
      - WARNING level by default
      - Detailed format with timestamps
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Determine log level
    if settings.is_development:
        log_level = logging.DEBUG if settings.debug else logging.INFO
    else:
        log_level = logging.WARNING

    # Allow environment variable override
    log_level_env = os.getenv("LOG_LEVEL", "").upper()
    if log_level_env in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        log_level = getattr(logging, log_level_env)

    # Create formatters
    if settings.is_development:
        # Simpler format for development
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    else:
        # Detailed format for production
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console Handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler with rotation (production only)
    if settings.is_production:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Environment: {settings.env}, Level: {logging.getLevelName(log_level)}")

    if settings.is_production:
        logger.info(f"Log files: {log_dir.absolute()}/app.log")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Usage:
        from logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Message")

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Context managers for temporary log level changes
class LogLevelContext:
    """
    Temporarily change log level for a block of code.

    Usage:
        with LogLevelContext(logging.DEBUG):
            # This code runs with DEBUG level
            logger.debug("Detailed info")
        # Original level restored
    """

    def __init__(self, level: int, logger_name: str = None):
        self.level = level
        self.logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        self.original_level = None

    def __enter__(self):
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)


# Utility function for structured logging
def log_request(logger: logging.Logger, method: str, endpoint: str, status_code: int, duration_ms: float, user_id: str = None):
    """
    Log HTTP request in a structured format.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user identifier
    """
    extra_info = f" [user={user_id}]" if user_id else ""

    if status_code >= 500:
        logger.error(f"{method} {endpoint} - {status_code} - {duration_ms:.2f}ms{extra_info}")
    elif status_code >= 400:
        logger.warning(f"{method} {endpoint} - {status_code} - {duration_ms:.2f}ms{extra_info}")
    else:
        logger.info(f"{method} {endpoint} - {status_code} - {duration_ms:.2f}ms{extra_info}")


def log_database_operation(logger: logging.Logger, operation: str, table: str, record_id: int = None, success: bool = True, error: Exception = None):
    """
    Log database operations in a structured format.

    Args:
        logger: Logger instance
        operation: Operation type (CREATE, READ, UPDATE, DELETE)
        table: Database table name
        record_id: Optional record ID
        success: Whether operation succeeded
        error: Optional exception if operation failed
    """
    record_info = f" [id={record_id}]" if record_id else ""

    if success:
        logger.info(f"DB {operation}: {table}{record_info}")
    else:
        error_msg = f": {str(error)}" if error else ""
        logger.error(f"DB {operation} FAILED: {table}{record_info}{error_msg}")


def log_websocket_event(logger: logging.Logger, event: str, session_code: str, details: str = None):
    """
    Log WebSocket events in a structured format.

    Args:
        logger: Logger instance
        event: Event type (CONNECT, DISCONNECT, MESSAGE, ERROR)
        session_code: Session code
        details: Optional additional details
    """
    details_info = f": {details}" if details else ""
    logger.info(f"WS {event} [session={session_code}]{details_info}")


def log_security_event(logger: logging.Logger, event: str, details: str, severity: str = "warning"):
    """
    Log security-related events.

    Args:
        logger: Logger instance
        event: Event type (AUTH_FAILED, RATE_LIMIT, INVALID_TOKEN, etc.)
        details: Event details
        severity: Log level (info, warning, error, critical)
    """
    log_func = getattr(logger, severity.lower(), logger.warning)
    log_func(f"SECURITY {event}: {details}")
