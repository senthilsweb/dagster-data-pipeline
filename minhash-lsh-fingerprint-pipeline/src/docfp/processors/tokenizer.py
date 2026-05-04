"""
File Name: tokenizer.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: TokenizerProcessor — splits normalized text into tokens using
             simple whitespace splitting (no external NLP library required).

Requirements:
- Python 3.12+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime

import structlog

script_name = os.path.splitext(os.path.basename(__file__))[0]
log_filename = f"{script_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(filename=log_filename, level=logging.INFO, format="%(message)s")
structlog.configure(
    logger_factory=structlog.stdlib.LoggerFactory(),
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger()


class TokenizerProcessor:
    """Split normalized text into a flat list of word tokens.

    Args:
        text: Normalized text string (output of TextNormalizer).
        document_id: SHA-256 document identifier (used for logging).

    Returns:
        List of string tokens.
    """

    def tokenize(self, text: str, document_id: str = "") -> list[str]:
        """Split text on whitespace and return token list.

        Args:
            text: Normalized text to tokenize.
            document_id: SHA-256 identifier for logging context.

        Returns:
            List of non-empty token strings.
        """
        tokens = text.split() if text else []
        log.info("tokenized", document_id=document_id, token_count=len(tokens))
        return tokens
