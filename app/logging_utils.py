"""Application logging configuration and helpers."""

from collections import deque
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configure root logging once for API and scraper diagnostics."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_path = Path(settings.log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    _CONFIGURED = True


def tail_log_lines(limit: int) -> list[str]:
    """Return the last N lines from the configured log file."""
    if limit < 1:
        return []

    log_path = Path(settings.log_file_path)
    if not log_path.exists():
        return []

    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        return list(deque((line.rstrip("\n") for line in f), maxlen=limit))
