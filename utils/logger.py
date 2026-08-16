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


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
        logger.propagate = False
    return logger
