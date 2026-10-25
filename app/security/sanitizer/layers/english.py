"""English (US/UK) PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.english import (
    validate_us_ssn,
    validate_us_phone,
    validate_us_zip,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# US Phone: (123) 456-7890, 123-456-7890, 123.456.7890
US_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?1[\s\-.]?)?"
    r"\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}(?!\d)"
)

# SSN: 123-45-6789 or 123 45 6789
SSN_PATTERN = re.compile(
    r"\b\d{3}[\s\-]\d{2}[\s\-]\d{4}\b"
)

# US ZIP: 12345 or 12345-6789
US_ZIP_PATTERN = re.compile(
    r"\b\d{5}(?:-\d{4})?\b"
)

# Context keywords for ZIP
ZIP_CONTEXT = re.compile(
    r"\b(?:zip|zip\s+code|postal\s+code|postcode)\b",
    re.IGNORECASE,
)

# Context keywords for SSN
SSN_CONTEXT = re.compile(
    r"\b(?:ssn|social\s+security)\b",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# English Layer
# ═══════════════════════════════════════════════════════════

class EnglishLayer(BaseLayer):
    """Detects English-specific PII: SSN, US Phone, US ZIP."""

    language = "en"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── SSN ───
        for m in SSN_PATTERN.finditer(text):
            if validate_us_ssn(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.SSN, score=0.95,
                    source="regex-en-ssn",
                ))

        # ─── US Phone ───
        for m in US_PHONE_PATTERN.finditer(text):
            if validate_us_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.PHONE, score=0.85,
                    source="regex-en-phone",
                ))

        # ─── US ZIP (context-aware) ───
        # فقط اگر «zip» یا «postal» در ۳۰ کاراکتر اطراف باشد
        for m in US_ZIP_PATTERN.finditer(text):
            if not validate_us_zip(m.group()):
                continue

            # Context window
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            window = text[start:end]

            if ZIP_CONTEXT.search(window):
                entities.append(self._make_entity(
                    m, PIIType.US_ZIP, score=0.85,
                    source="regex-en-zip",
                ))

        return entities