"""
File Name: text_normalizer.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: TextNormalizer — deterministic text normalization: lowercase,
             Unicode NFC, whitespace cleanup, punctuation stripping, and optional
             stopword removal (FR-010, ADR-004).

Requirements:
- Python 3.12+
"""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from datetime import datetime

import structlog

from docfp.interfaces.normalizer import Normalizer
from docfp.models.normalized_text import NormalizedText

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

NORMALIZATION_VERSION = "v1"

# Minimal English stopword set (used only when remove_stopwords=True)
_STOPWORDS: frozenset[str] = frozenset(
    "a an the is was are were be been being have has had do does did "
    "will would could should may might shall can of in on at to for "
    "with by from as and or but not".split()
)


class TextNormalizer(Normalizer):
    """Deterministic text normalizer (FR-010, ADR-004).

    Rules applied in order:
      1. Unicode NFC normalization
      2. Lowercase
      3. Strip punctuation (keep spaces and alphanumerics)
      4. Collapse whitespace

    Args:
        remove_stopwords: When True, removes tokens in the stopword set.

    Returns:
        NormalizedText instance.
    """

    def __init__(self, remove_stopwords: bool = False) -> None:
        self.remove_stopwords = remove_stopwords

    def normalize(self, document_id: str, source_uri: str, text: str) -> NormalizedText:
        """Normalize raw extracted text deterministically.

        Args:
            document_id: SHA-256 identifier for the source document.
            source_uri: Absolute path or URI of the source document.
            text: Raw extracted text string.

        Returns:
            NormalizedText with cleaned, lowercase, unicode-normalized text.
        """
        normalized = unicodedata.normalize("NFC", text)
        normalized = normalized.lower()
        normalized = re.sub(r"[^\w\s]", " ", normalized)  # strip punctuation
        normalized = re.sub(r"\s+", " ", normalized).strip()  # collapse whitespace

        if self.remove_stopwords:
            tokens = [t for t in normalized.split() if t not in _STOPWORDS]
            normalized = " ".join(tokens)

        token_count = len(normalized.split()) if normalized else 0

        log.info(
            "text_normalized",
            document_id=document_id,
            token_count=token_count,
            normalization_version=NORMALIZATION_VERSION,
            remove_stopwords=self.remove_stopwords,
        )

        return NormalizedText(
            document_id=document_id,
            source_uri=source_uri,
            text=normalized,
            normalization_version=NORMALIZATION_VERSION,
            token_count=token_count,
        )
