"""Persian (Farsi/Iranian) PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.persian import (
    validate_iran_national_id,
    validate_iran_mobile,
    validate_iran_postal_code,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Helper: Persian → Latin digit normalization
# ═══════════════════════════════════════════════════════════

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
LATIN_DIGITS = "0123456789"

TRANSLATE_TABLE = str.maketrans(
    PERSIAN_DIGITS + ARABIC_DIGITS,
    LATIN_DIGITS + LATIN_DIGITS,
)


def normalize_digits(text: str) -> str:
    """Convert Persian/Arabic digits to Latin."""
    return text.translate(TRANSLATE_TABLE)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# Iranian mobile: 09XXXXXXXXX with optional separators
IR_MOBILE_PATTERN = re.compile(
    r"(?<!\d)(?:\+98|0098|98|0)?9\d{2}[\s\-]?\d{3}[\s\-]?\d{4}(?!\d)"
)

# National ID: 10 digits (will validate with checksum)
IR_NATIONAL_ID_PATTERN = re.compile(
    r"(?<!\d)\d{10}(?!\d)"
)

# Postal code: 10 digits (context-aware)
IR_POSTAL_PATTERN = re.compile(
    r"(?<!\d)\d{10}(?!\d)"
)

# Passport: 9 chars, first is letter
IR_PASSPORT_PATTERN = re.compile(
    r"\b[A-Za-z]\d{8}\b"
)


# Context keywords
MOBILE_CONTEXT = re.compile(
    r"(?:موبایل|همراه|تلفن|شماره|mobile|phone)",
    re.IGNORECASE,
)

NATIONAL_ID_CONTEXT = re.compile(
    r"(?:کد\s*ملی|شماره\s*ملی|کدملی|national\s*id|nid)",
    re.IGNORECASE,
)

POSTAL_CONTEXT = re.compile(
    r"(?:کد\s*پستی|کدپستی|postal\s*code|zip)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# Persian Layer
# ═══════════════════════════════════════════════════════════

class PersianLayer(BaseLayer):
    """Detects Persian-specific PII: national ID, mobile, postal code."""

    language = "fa"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        # Normalize Persian digits to Latin
        normalized = normalize_digits(text)

        entities: list[PIIEntity] = []

        # ─── Iranian mobile ───
        for m in IR_MOBILE_PATTERN.finditer(normalized):
            if validate_iran_mobile(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.IR_MOBILE, score=0.9,
                    source="regex-fa-mobile",
                ))

        # ─── National ID (with checksum) ───
        for m in IR_NATIONAL_ID_PATTERN.finditer(normalized):
            candidate = m.group()

            # Skip if it's also a valid mobile (overlap check)
            is_nid = validate_iran_national_id(candidate)

            # Context window
            start = max(0, m.start() - 30)
            end = min(len(normalized), m.end() + 30)
            window = normalized[start:end]
            has_context = bool(NATIONAL_ID_CONTEXT.search(window))

            # Accept if checksum valid OR context keyword present
            if is_nid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.IR_NATIONAL_ID,
                    score=0.95 if is_nid else 0.75,
                    source="regex-fa-nid" if is_nid else "regex-fa-nid-ctx",
                ))

        # ─── Postal code (context-aware) ───
        for m in IR_POSTAL_PATTERN.finditer(normalized):
            candidate = m.group()

            if not validate_iran_postal_code(candidate):
                continue

            start = max(0, m.start() - 30)
            end = min(len(normalized), m.end() + 30)
            window = normalized[start:end]

            if POSTAL_CONTEXT.search(window):
                entities.append(self._make_entity(
                    m, PIIType.IR_POSTAL_CODE, score=0.85,
                    source="regex-fa-postal",
                ))

        # ─── Passport ───
        for m in IR_PASSPORT_PATTERN.finditer(normalized):
            # Passport format is generic; only accept with context
            start = max(0, m.start() - 30)
            end = min(len(normalized), m.end() + 30)
            window = normalized[start:end]

            if re.search(r"(?:پاسپورت|گذرنامه|passport)", window, re.IGNORECASE):
                entities.append(self._make_entity(
                    m, PIIType.IR_PASSPORT, score=0.8,
                    source="regex-fa-passport",
                ))

        return entities