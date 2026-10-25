"""Korean PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.korean import (
    validate_korean_rrn,
    validate_korean_phone,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# Korean RRN: 6-7 digits (with optional hyphen)
KR_RRN_PATTERN = re.compile(
    r"(?<!\d)\d{6}[\s\-]?\d{7}(?!\d)"
)

# Korean phone: various formats
KR_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+82|0082|82)?0?1[016789][\s\-]?\d{3,4}[\s\-]?\d{4}(?!\d)"
    r"|"
    r"(?<!\d)(?:\+82|0082|82)?0?[2-6]\d{0,2}[\s\-]?\d{3,4}[\s\-]?\d{4}(?!\d)"
)


# Context keywords
KR_RRN_CONTEXT = re.compile(
    r"(?:주민등록|주민번호|rrn|resident\s*registration)",
    re.IGNORECASE,
)

KR_PHONE_CONTEXT = re.compile(
    r"(?:전화|휴대|폰|phone|mobile)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# Korean Layer
# ═══════════════════════════════════════════════════════════

class KoreanLayer(BaseLayer):
    """Detects Korean-specific PII."""

    language = "ko"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── RRN ───
        for m in KR_RRN_PATTERN.finditer(text):
            raw = m.group()
            digits = re.sub(r"\D", "", raw)

            if len(digits) != 13:
                continue

            is_valid = validate_korean_rrn(digits)

            # Context window
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            window = text[start:end]
            has_context = bool(KR_RRN_CONTEXT.search(window))

            if is_valid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.KR_RRN,
                    score=0.98 if is_valid else 0.75,
                    source="regex-ko-rrn" if is_valid else "regex-ko-rrn-ctx",
                ))

        # ─── Phone ───
        for m in KR_PHONE_PATTERN.finditer(text):
            if validate_korean_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.KR_PHONE, score=0.85,
                    source="regex-ko-phone",
                ))

        return entities