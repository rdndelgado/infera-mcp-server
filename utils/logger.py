"""Terminal logging that never leaks credentials (PRD_V2 §11 utils/logger.py)."""

import logging
import re

from helpers.constants import LOG_LEVEL

_REDACT_PATTERNS = [
    re.compile(r"(postgresql://[^:]+:)[^@]+(@)"),          # conn string password
    re.compile(r"(SUPABASE_KEY\s*=\s*)\S+", re.IGNORECASE),
    re.compile(r"(MCP_API_KEY\s*=\s*)\S+", re.IGNORECASE),
    re.compile(r"(Authorization:\s*Bearer\s+)\S+", re.IGNORECASE),
]


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in _REDACT_PATTERNS:
            message = pattern.sub(r"\1***REDACTED***", message)
        record.msg = message
        record.args = ()
        return True


_LEVEL_COLORS = {
    logging.DEBUG: "\033[36m",     # cyan
    logging.INFO: "\033[32m",      # green
    logging.WARNING: "\033[33m",   # yellow
    logging.ERROR: "\033[31m",     # red
    logging.CRITICAL: "\033[41m",  # red bg
}
_RESET = "\033[0m"
_DIM = "\033[2m"


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, "")
        timestamp = self.formatTime(record)
        return f"{_DIM}{timestamp}{_RESET} {color}{record.levelname:<8}{_RESET} [{record.name}] {record.getMessage()}"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = ColorFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        handler.setFormatter(formatter)
        handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
        logger.propagate = False
    return logger
