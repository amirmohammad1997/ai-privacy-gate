"""Base class for language-specific regex layers."""
import logging
from abc import ABC, abstractmethod
from typing import Optional

from ..models import PIIEntity, PIIType

logger = logging.getLogger(__name__)


class LayerResult:
    """Result from a single layer."""

    def __init__(self, entities: Optional[list[PIIEntity]] = None):
        self.entities = entities or []

    def __len__(self):
        return len(self.entities)

    def __iter__(self):
        return iter(self.entities)


class BaseLayer(ABC):
    """
    Base class for all language layers.

    Each layer implements `detect()` to find PII specific
    to its language.
    """

    # نام زبان (برای لاگ)
    language: str = "unknown"

    @abstractmethod
    def detect(self, text: str) -> list[PIIEntity]:
        """
        Detect PII in text.

        Args:
            text: Input text

        Returns:
            List of PIIEntity objects
        """
        ...

    # ═══════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════

    def _make_entity(
        self,
        match,
        entity_type: PIIType,
        score: float = 0.9,
        source: Optional[str] = None,
    ) -> PIIEntity:
        """Helper to create a PIIEntity from a regex match."""
        return PIIEntity(
            start=match.start(),
            end=match.end(),
            entity_type=entity_type,
            text=match.group(),
            score=score,
            source=source or f"regex-{self.language}",
        )