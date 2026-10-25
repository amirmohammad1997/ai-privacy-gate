"""Japanese PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.japanese import (
    validate_japanese_my_number,
    validate_japanese_phone,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# My Number: 12 digits with optional separators
JP_MY_NUMBER_PATTERN = re.compile(
    r"(?<!\d)\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)"
)

# Japanese phone
JP_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+81|0081|81)?0?[789]0[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)"
    r"|"
    r"(?<!\d)(?:\+81|0081|81)?0\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{4}(?!\d)"
)


# Context keywords
JP_MY_NUMBER_CONTEXT = re.compile(
    r"(?:マイナンバー|個人番号|my\s*number)",
    re.IGNORECASE,
)

JP_PHONE_CONTEXT = re.compile(
    r"(?:電話|携帯|mobile|phone)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# Japanese Layer
# ═══════════════════════════════════════════════════════════

class JapaneseLayer(BaseLayer):
    """Detects Japanese-specific PII."""

    language = "ja"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── My Number ───
        for m in JP_MY_NUMBER_PATTERN.finditer(text):
            raw = m.group()
            digits = re.sub(r"\D", "", raw)

            if len(digits) != 12:
                continue

            is_valid = validate_japanese_my_number(digits)

            # Context window
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            window = text[start:end]
            has_context = bool(JP_MY_NUMBER_CONTEXT.search(window))

            if is_valid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.JP_MY_NUMBER,
                    score=0.98 if is_valid else 0.7,
                    source="regex-ja-mynum" if is_valid else "regex-ja-mynum-ctx",
                ))

        # ─── Phone ───
        for m in JP_PHONE_PATTERN.finditer(text):
            if validate_japanese_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.JP_PHONE, score=0.85,
                    source="regex-ja-phone",
                ))

        return entities