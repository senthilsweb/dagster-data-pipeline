"""
File Name: ocr_decision_processor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: OcrDecisionProcessor — decides whether OCR should be applied
             based on extracted text length vs. a configurable threshold or
             an explicit config flag (FR-009).

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

DEFAULT_MIN_TEXT_LENGTH = 50  # chars — below this OCR is triggered


class OcrDecisionProcessor:
    """Decide whether a document needs OCR.

    Args:
        min_text_length: Minimum extracted text length (chars) below which
                         OCR is triggered. Default is 50.
        ocr_enabled: When True, OCR is always applied regardless of length.

    Returns:
        True if OCR should be applied, False otherwise.
    """

    def __init__(
        self,
        min_text_length: int = DEFAULT_MIN_TEXT_LENGTH,
        ocr_enabled: bool = False,
    ) -> None:
        self.min_text_length = min_text_length
        self.ocr_enabled = ocr_enabled

    def should_run_ocr(self, extracted_text: str, source_uri: str) -> bool:
        """Determine whether OCR should be applied.

        Args:
            extracted_text: Text already extracted by the primary extractor.
            source_uri: Source file path (used for logging).

        Returns:
            True when OCR is required, False otherwise.
        """
        text_len = len(extracted_text.strip())
        needs_ocr = self.ocr_enabled or (text_len < self.min_text_length)
        log.info(
            "ocr_decision",
            source_uri=source_uri,
            text_length=text_len,
            threshold=self.min_text_length,
            ocr_enabled=self.ocr_enabled,
            ocr_required=needs_ocr,
        )
        return needs_ocr
