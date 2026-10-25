"""Arabic PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.arabic import (
    validate_saudi_national_id,
    validate_egyptian_national_id,
    validate_uae_emirates_id,
    validate_arabic_mobile,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Persian/Arabic digit normalization
# ═══════════════════════════════════════════════════════════

ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
LATIN_DIGITS = "0123456789"

TRANSLATE_TABLE = str.maketrans(
    ARABIC_DIGITS + PERSIAN_DIGITS,
    LATIN_DIGITS + LATIN_DIGITS,
)


def normalize_digits(text: str) -> str:
    return text.translate(TRANSLATE_TABLE)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# Saudi National ID: 10 digits
SA_NATIONAL_ID_PATTERN = re.compile(
    r"(?<!\d)[12]\d{9}(?!\d)"
)

# Egyptian National ID: 14 digits
EG_NATIONAL_ID_PATTERN = re.compile(
    r"(?<!\d)[23]\d{13}(?!\d)"
)

# UAE Emirates ID: 15 digits starting with 784
AE_EMIRATES_ID_PATTERN = re.compile(
    r"(?<!\d)784[\s\-]?\d{4}[\s\-]?\d{7}[\s\-]?\d(?!\d)"
)

# Arabic mobile (GCC + Egypt)
AR_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?966|\+?971|\+?20|\+?974|\+?965|\+?973|\+?968|\+?962|\+?961)?"
    r"[\s\-]?0?5\d[\s\-]?\d{3}[\s\-]?\d{4}(?!\d)"
)


# Context keywords
SAUDI_ID_CONTEXT = re.compile(
    r"(?:هوية|هوية\s*وطنية|national\s*id|saudi\s*id)",
    re.IGNORECASE,
)

EGYPT_ID_CONTEXT = re.compile(
    r"(?:رقم\s*قومي|الرقم\s*القومي|national\s*id)",
    re.IGNORECASE,
)

UAE_ID_CONTEXT = re.compile(
    r"(?:emirates\s*id|هوية\s*الإمارات|eid)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# Arabic Layer
# ═══════════════════════════════════════════════════════════

class ArabicLayer(BaseLayer):
    """Detects Arabic-specific PII."""

    language = "ar"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        # Normalize Arabic digits
        normalized = normalize_digits(text)

        entities: list[PIIEntity] = []

        # ─── Saudi National ID ───
        for m in SA_NATIONAL_ID_PATTERN.finditer(normalized):
            candidate = m.group()
            is_valid = validate_saudi_national_id(candidate)

            start = max(0, m.start() - 30)
            end = min(len(normalized), m.end() + 30)
            window = normalized[start:end]
            has_context = bool(SAUDI_ID_CONTEXT.search(window))

            if is_valid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.AR_NATIONAL_ID,
                    score=0.95 if is_valid else 0.7,
                    source="regex-ar-sa-id" if is_valid else "regex-ar-sa-id-ctx",
                ))

        # ─── Egyptian National ID ───
        for m in EG_NATIONAL_ID_PATTERN.finditer(normalized):
            candidate = m.group()
            is_valid = validate_egyptian_national_id(candidate)

            start = max(0, m.start() - 30)
            end = min(len(normalized), m.end() + 30)
            window = normalized[start:end]
            has_context = bool(EGYPT_ID_CONTEXT.search(window))

            if is_valid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.AR_NATIONAL_ID,
                    score=0.95 if is_valid else 0.7,
                    source="regex-ar-eg-id" if is_valid else "regex-ar-eg-id-ctx",
                ))

        # ─── UAE Emirates ID ───
        for m in AE_EMIRATES_ID_PATTERN.finditer(normalized):
            if validate_uae_emirates_id(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.AR_NATIONAL_ID, score=0.95,
                    source="regex-ar-ae-id",
                ))

        # ─── Arabic Mobile ───
        for m in AR_PHONE_PATTERN.finditer(normalized):
            if validate_arabic_mobile(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.AR_PHONE, score=0.85,
                    source="regex-ar-phone",
                ))

        return entities