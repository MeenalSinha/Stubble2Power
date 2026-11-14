"""
Structured logging module for Stubble2Power.
Ensures sensitive tokens (e.g. NASA MAP_KEY, database passwords) are never emitted in logs.
"""

import logging
import os
import re
import sys


class SensitiveDataFilter(logging.Filter):
    """Redacts sensitive tokens and secret keys from logs."""
    SENSITIVE_PATTERNS = [
        (re.compile(r'MAP_KEY[=:][a-zA-Z0-9_\-]+', re.IGNORECASE), 'MAP_KEY=[REDACTED]'),
        (re.compile(r'password[=:][^& \n]+', re.IGNORECASE), 'password=[REDACTED]'),
        (re.compile(r'key[=:][a-zA-Z0-9_\-]{20,}', re.IGNORECASE), 'key=[REDACTED]'),
        (re.compile(r'postgres://[^:]+:([^@]+)@', re.IGNORECASE), 'postgres://user:[REDACTED]@'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, repl in self.SENSITIVE_PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        return True


def get_logger(name: str = "stubble2power") -> logging.Logger:
    """Returns a configured logger with secret redaction."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, log_level_str, logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())

        logger.addHandler(handler)
        logger.propagate = False

    return logger
