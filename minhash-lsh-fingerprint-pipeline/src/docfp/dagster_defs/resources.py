"""
File Name: resources.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: Dagster ConfigurableResource definitions — extractor, normalizer,
             and hasher are wired here so they can be swapped via dagster.yaml
             without touching asset code (ADR-003).

Requirements:
- dagster>=1.9
- Python 3.12+
"""

from __future__ import annotations

from dagster import ConfigurableResource

from docfp.extractors.tika_extractor import TikaDocumentTextExtractor
from docfp.interfaces.document_text_extractor import DocumentTextExtractor
from docfp.interfaces.normalizer import Normalizer
from docfp.interfaces.shingle_hasher import ShingleHasher
from docfp.processors.shingle_hash_processor import ShingleHashProcessor
from docfp.processors.text_normalizer import TextNormalizer


class TextExtractorResource(ConfigurableResource):
    """Dagster resource wrapping the active DocumentTextExtractor.

    Args:
        engine: Extractor engine name. Supported values: 'tika'.

    Returns:
        DocumentTextExtractor instance.
    """

    engine: str = "tika"

    def get_extractor(self) -> DocumentTextExtractor:
        """Return the configured DocumentTextExtractor implementation.

        Args:
            None.

        Returns:
            DocumentTextExtractor instance for the configured engine.
        """
        if self.engine == "tika":
            return TikaDocumentTextExtractor()
        raise ValueError(f"Unsupported extractor engine: {self.engine!r}")


class TextNormalizerResource(ConfigurableResource):
    """Dagster resource wrapping the active Normalizer.

    Args:
        remove_stopwords: Whether stopwords should be removed during normalization.

    Returns:
        Normalizer instance.
    """

    remove_stopwords: bool = False

    def get_normalizer(self) -> Normalizer:
        """Return the configured Normalizer implementation.

        Args:
            None.

        Returns:
            Normalizer instance.
        """
        return TextNormalizer(remove_stopwords=self.remove_stopwords)


class ShingleHasherResource(ConfigurableResource):
    """Dagster resource wrapping the ShingleHasher.

    Returns:
        ShingleHasher instance (SHA-256 + xxhash64).
    """

    def get_hasher(self) -> ShingleHasher:
        """Return the ShingleHasher implementation.

        Args:
            None.

        Returns:
            ShingleHashProcessor instance.
        """
        return ShingleHashProcessor()
