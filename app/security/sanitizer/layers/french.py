"""French PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.french import (
    validate_french_insee,
    validate_french_phone,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# INSEE: 15 digits with optional spaces (1 XX XX XX XXX XXX XX)
FR_INSEE_PATTERN = re.compile(
    r"(?<!\d)[12][\s]?\d{2}[\s]?\d{2}[\s]?\d{2}[\s]?\d{3}[\s]?\d{3}[\s]?\d{2}(?!\d)"
)

# Phone
FR_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+33|0033)[\s\-]?[1-9](?:[\s\-]?\d{2}){4}(?!\d)"
    r"|"
    r"(?<!\d)0[1-9](?:[\s\-]?\d{2}){4}(?!\d)"
)


# Context keywords
INSEE_CONTEXT = re.compile(
    r"(?:insee|nir|numéro\s*de\s*sécurité\s*sociale|sécurité\s*sociale)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# French Layer
# ═══════════════════════════════════════════════════════════

class FrenchLayer(BaseLayer):
    """Detects French-specific PII."""

    language = "fr"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── INSEE ───
        for m in FR_INSEE_PATTERN.finditer(text):
            if validate_french_insee(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.FR_INSEE, score=0.95,
                    source="regex-fr-insee",
                ))

        # ─── Phone ───
        for m in FR_PHONE_PATTERN.finditer(text):
            if validate_french_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.PHONE, score=0.85,
                    source="regex-fr-phone",
                ))

        return entities