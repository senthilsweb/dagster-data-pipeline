"""
File Name: artifact_writer.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: ArtifactWriter ABC — generic interface for writing any pipeline
             artifact to disk.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ArtifactWriter(ABC):
    """Abstract base class for all artifact writers.

    Implementations write a given artifact to the filesystem and return
    the path of the written file.
    """

    @abstractmethod
    def write(self, artifact: Any, output_dir: Path) -> Path:
        """Serialize and write an artifact to disk.

        Args:
            artifact: The artifact object to write.
            output_dir: Directory into which the artifact file is written.

        Returns:
            Path of the written file.
        """
