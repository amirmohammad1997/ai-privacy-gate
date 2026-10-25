"""Portuguese/Brazilian PII layer."""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.portuguese import (
    validate_brazilian_cpf,
    validate_brazilian_cnpj,
    validate_portuguese_phone,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# CPF: 11 digits with optional separators (###.###.###-##)
PT_CPF_PATTERN = re.compile(
    r"(?<!\d)\d{3}[\s\.\-]?\d{3}[\s\.\-]?\d{3}[\s\.\-]?\d{2}(?!\d)"
)

# CNPJ: 14 digits with optional separators (##.###.###/####-##)
PT_CNPJ_PATTERN = re.compile(
    r"(?<!\d)\d{2}[\s\.\-]?\d{3}[\s\.\-]?\d{3}[\s\.\-/]?\d{4}[\s\.\-]?\d{2}(?!\d)"
)

# Phone
PT_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+351|\+55|00351|0055|351|55)?[\s\-]?"
    r"\(?\d{2,3}\)?[\s\-]?\d{4,5}[\s\-]?\d{4}(?!\d)"
)


# Context keywords
CPF_CONTEXT = re.compile(
    r"(?:cpf|cadastro\s*de\s*pessoas\s*físicas)",
    re.IGNORECASE,
)

CNPJ_CONTEXT = re.compile(
    r"(?:cnpj|cadastro\s*nacional)",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════
# Portuguese Layer
# ═══════════════════════════════════════════════════════════

class PortugueseLayer(BaseLayer):
    """Detects Portuguese/Brazilian PII."""

    language = "pt"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── CNPJ (check before CPF since CNPJ is longer) ───
        for m in PT_CNPJ_PATTERN.finditer(text):
            raw = m.group()
            digits = re.sub(r"\D", "", raw)

            if len(digits) != 14:
                continue

            if validate_brazilian_cnpj(digits):
                entities.append(self._make_entity(
                    m, PIIType.PT_CNPJ, score=0.98,
                    source="regex-pt-cnpj",
                ))

        # ─── CPF ───
        for m in PT_CPF_PATTERN.finditer(text):
            raw = m.group()
            digits = re.sub(r"\D", "", raw)

            if len(digits) != 11:
                continue

            if validate_brazilian_cpf(digits):
                entities.append(self._make_entity(
                    m, PIIType.PT_CPF, score=0.98,
                    source="regex-pt-cpf",
                ))

        # ─── Phone ───
        for m in PT_PHONE_PATTERN.finditer(text):
            if validate_portuguese_phone(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.PHONE, score=0.8,
                    source="regex-pt-phone",
                ))

        return entities