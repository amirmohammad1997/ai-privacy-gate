"""Russian PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.russian import (
    validate_russian_snils,
    validate_russian_inn,
    validate_russian_phone,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# SNILS: 11 digits (###-###-### ##)
RU_SNILS_PATTERN = re.compile(
    r"(?<!\d)\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}(?!\d)"
)

# INN: 10 or 12 digits
RU_INN_PATTERN = re.compile(
    r"(?<!\d)\d{12}(?!\d)"
    r"|"
    r"(?<!\d)\d{10}(?!\d)"
)

# Phone
RU_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}(?!\d)"
)


# Context keywords (transliterated + English)
SNILS_CONTEXT = re.compile(
    r"(?:снилс|snils|pension\s*insurance)",
    re.IGNORECASE,
)

INN_CONTEXT = re.compile(
    r"(?:инн|inn|tax\s*id|налоговый)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# Russian Layer
# ═══════════════════════════════════════════════════════════

class RussianLayer(BaseLayer):
    """Detects Russian-specific PII."""

    language = "ru"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── SNILS ───
        for m in RU_SNILS_PATTERN.finditer(text):
            raw = m.group()
            digits = re.sub(r"\D", "", raw)

            if len(digits) != 11:
                continue

            is_valid = validate_russian_snils(digits)

            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            window = text[start:end]
            has_context = bool(SNILS_CONTEXT.search(window))

            if is_valid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.RU_SNILS,
                    score=0.98 if is_valid else 0.7,
                    source="regex-ru-snils" if is_valid else "regex-ru-snils-ctx",
                ))

        # ─── INN ───
        for m in RU_INN_PATTERN.finditer(text):
            raw = m.group()
            digits = re.sub(r"\D", "", raw)

            if len(digits) not in (10, 12):
                continue

            is_valid = validate_russian_inn(digits)

            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            window = text[start:end]
            has_context = bool(INN_CONTEXT.search(window))

            if is_valid or has_context:
                entities.append(self._make_entity(
                    m, PIIType.RU_INN,
                    score=0.95 if is_valid else 0.7,
                    source="regex-ru-inn" if is_valid else "regex-ru-inn-ctx",
                ))

        # ─── Phone ───
        for m in RU_PHONE_PATTERN.finditer(text):
            if validate_russian_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.PHONE, score=0.85,
                    source="regex-ru-phone",
                ))

        return entities