"""Chinese PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.chinese import (
    validate_chinese_id,
    validate_chinese_phone,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# Chinese ID: 17 digits + digit/X
CN_ID_PATTERN = re.compile(
    r"(?<!\d)(?:\d{17}[\dXx])(?!\d)"
)

# Chinese mobile: 1XX XXXX XXXX with optional separators
CN_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+86|0086|86)?1[3-9]\d[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)"
)


# Context keywords
CN_ID_CONTEXT = re.compile(
    r"(?:身份证|身份证号|id\s*card|shenfenzheng)",
    re.IGNORECASE,
)

CN_PHONE_CONTEXT = re.compile(
    r"(?:手机|电话|号码|mobile|phone)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# Chinese Layer
# ═══════════════════════════════════════════════════════════

class ChineseLayer(BaseLayer):
    """Detects Chinese-specific PII."""

    language = "zh"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── ID Card ───
        for m in CN_ID_PATTERN.finditer(text):
            candidate = m.group()
            is_valid = validate_chinese_id(candidate)

            # Context window
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            window = text[start:end]
            has_context = bool(CN_ID_CONTEXT.search(window))

            if is_valid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.CN_ID_CARD,
                    score=0.98 if is_valid else 0.75,
                    source="regex-zh-id" if is_valid else "regex-zh-id-ctx",
                ))

        # ─── Mobile Phone ───
        for m in CN_PHONE_PATTERN.finditer(text):
            if validate_chinese_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.CN_PHONE, score=0.9,
                    source="regex-zh-phone",
                ))

        return entities