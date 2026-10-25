"""Spanish PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.spanish import (
    validate_spanish_dni,
    validate_spanish_nie,
    validate_spanish_phone,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# DNI: 8 digits + letter (with optional separators)
ES_DNI_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])\d{8}[\s\-]?[A-Za-z](?![A-Za-z0-9])"
)

# NIE: X/Y/Z + 7 digits + letter
ES_NIE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])[XYZxyz][\s\-]?\d{7}[\s\-]?[A-Za-z](?![A-Za-z0-9])"
)

# Phone
ES_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+34|0034|34)?[\s\-]?[679]\d{2}[\s\-]?\d{3}[\s\-]?\d{3}(?!\d)"
)


# Context keywords
DNI_CONTEXT = re.compile(
    r"(?:dni|nif|documento\s*nacional|documento\s*de\s*identidad)",
    re.IGNORECASE,
)

NIE_CONTEXT = re.compile(
    r"(?:nie|número\s*de\s*identificación\s*de\s*extranjero)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# Spanish Layer
# ═══════════════════════════════════════════════════════════

class SpanishLayer(BaseLayer):
    """Detects Spanish-specific PII."""

    language = "es"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── DNI ───
        for m in ES_DNI_PATTERN.finditer(text):
            if validate_spanish_dni(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.ES_DNI, score=0.95,
                    source="regex-es-dni",
                ))

        # ─── NIE ───
        for m in ES_NIE_PATTERN.finditer(text):
            if validate_spanish_nie(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.ES_NIE, score=0.95,
                    source="regex-es-nie",
                ))

        # ─── Phone ───
        for m in ES_PHONE_PATTERN.finditer(text):
            if validate_spanish_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.PHONE, score=0.85,
                    source="regex-es-phone",
                ))

        return entities