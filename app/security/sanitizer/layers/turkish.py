"""Turkish PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.turkish import (
    validate_turkish_tckn,
    validate_turkish_phone,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# Turkish mobile: 05XX XXX XX XX or +90 5XX...
TR_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+90|0090|90|0)?5\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}(?!\d)"
)

# TCKN: 11 digits
TR_TCKN_PATTERN = re.compile(
    r"(?<!\d)\d{11}(?!\d)"
)


# Context keywords
TCKN_CONTEXT = re.compile(
    r"(?:tckn|tc\s*kimlik|kimlik\s*no|tc\s*no)",
    re.IGNORECASE,
)

PHONE_CONTEXT = re.compile(
    r"(?:telefon|cep|numara|tel|phone|mobile)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# Turkish Layer
# ═══════════════════════════════════════════════════════════

class TurkishLayer(BaseLayer):
    """Detects Turkish-specific PII: TCKN, mobile phone."""

    language = "tr"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── Mobile phone ───
        for m in TR_PHONE_PATTERN.finditer(text):
            if validate_turkish_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.TR_PHONE, score=0.9,
                    source="regex-tr-phone",
                ))

        # ─── TCKN ───
        for m in TR_TCKN_PATTERN.finditer(text):
            candidate = m.group()
            is_valid = validate_turkish_tckn(candidate)

            # Context window
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            window = text[start:end]
            has_context = bool(TCKN_CONTEXT.search(window))

            if is_valid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.TR_TCKN,
                    score=0.98 if is_valid else 0.7,
                    source="regex-tr-tckn" if is_valid else "regex-tr-tckn-ctx",
                ))

        return entities