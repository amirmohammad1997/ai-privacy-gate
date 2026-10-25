"""German PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.german import (
    validate_german_steuer_id,
    validate_german_phone,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# Steuer-ID: 11 digits
DE_STEUER_PATTERN = re.compile(
    r"(?<!\d)\d{11}(?!\d)"
)

# Phone
DE_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+49|0049)[\s\-]?[1-9][\d\s\-]{8,15}(?!\d)"
    r"|"
    r"(?<!\d)0[1-9][\d\s\-]{8,15}(?!\d)"
)


# Context keywords
STEUER_CONTEXT = re.compile(
    r"(?:steuer|steuer-id|steueridentifikationsnummer|tax\s*id|identifikationsnummer)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# German Layer
# ═══════════════════════════════════════════════════════════

class GermanLayer(BaseLayer):
    """Detects German-specific PII."""

    language = "de"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── Steuer-ID ───
        for m in DE_STEUER_PATTERN.finditer(text):
            candidate = m.group()
            is_valid = validate_german_steuer_id(candidate)

            # Context window
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            window = text[start:end]
            has_context = bool(STEUER_CONTEXT.search(window))

            if is_valid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.DE_STEUER_ID,
                    score=0.98 if is_valid else 0.7,
                    source="regex-de-steuer" if is_valid else "regex-de-steuer-ctx",
                ))

        # ─── Phone ───
        for m in DE_PHONE_PATTERN.finditer(text):
            if validate_german_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.PHONE, score=0.85,
                    source="regex-de-phone",
                ))

        return entities