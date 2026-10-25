"""
Universal PII layer — works for all languages.

Detects:
- Email addresses
- IP addresses (IPv4, IPv6)
- URLs
- Credit cards (16+ digits with Luhn)
- IBAN / Sheba
- MAC addresses
"""
import logging
import re

from ..models import PIIEntity, PIIType
from ..validators.universal import (
    validate_luhn,
    validate_iban,
    validate_ip,
    validate_email,
)
from .base import BaseLayer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

# Email (universal)
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# IPv4
IPV4_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# IPv6 (simplified)
IPV6_PATTERN = re.compile(
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
)

# URL
URL_PATTERN = re.compile(
    r"\bhttps?://[^\s<>\"']+"
)

# Credit card: 13-19 digits with separators (space, dash)
CREDIT_CARD_PATTERN = re.compile(
    r"(?<!\d)(?:\d[\s\-]?){12,18}\d(?!\d)"
)

# IBAN: 2 letters + 2 digits + 11-30 alphanumeric
IBAN_PATTERN = re.compile(
    r"\b[A-Z]{2}\d{2}[\s\-]?"
    r"(?:[A-Z0-9]{4}[\s\-]?){2,7}[A-Z0-9]{1,4}\b"
)

# MAC Address
MAC_PATTERN = re.compile(
    r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"
)


# ═══════════════════════════════════════════════════════════
# Universal Layer
# ═══════════════════════════════════════════════════════════

class UniversalLayer(BaseLayer):
    """
    Language-independent PII detection.

    This layer runs for every input, regardless of language.
    """

    language = "universal"

    def detect(self, text: str) -> list[PIIEntity]:
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── Email ───
        for m in EMAIL_PATTERN.finditer(text):
            if validate_email(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.EMAIL, score=0.95,
                    source="universal-email",
                ))

        # ─── URL ───
        for m in URL_PATTERN.finditer(text):
            entities.append(self._make_entity(
                m, PIIType.URL, score=0.9,
                source="universal-url",
            ))

        # ─── IPv4 ───
        for m in IPV4_PATTERN.finditer(text):
            if validate_ip(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.IP_ADDRESS, score=0.9,
                    source="universal-ipv4",
                ))

        # ─── IPv6 ───
        for m in IPV6_PATTERN.finditer(text):
            if validate_ip(m.group()):
                entities.append(self._make_entity(
                    m, PIIType.IP_ADDRESS, score=0.85,
                    source="universal-ipv6",
                ))

        # ─── Credit Card (Luhn) ───
        for m in CREDIT_CARD_PATTERN.finditer(text):
            raw = m.group()
            digits = re.sub(r"[\s\-]", "", raw)

            if 13 <= len(digits) <= 19 and validate_luhn(digits):
                entities.append(self._make_entity(
                    m, PIIType.CREDIT_CARD, score=0.97,
                    source="universal-cc",
                ))

        # ─── IBAN ───
        for m in IBAN_PATTERN.finditer(text):
            raw = m.group()
            # Handle potential whitespace/hyphen
            cleaned = raw.replace(" ", "").replace("-", "")
            if validate_iban(cleaned):
                entities.append(self._make_entity(
                    m, PIIType.IBAN, score=0.98,
                    source="universal-iban",
                ))

        # ─── MAC Address ───
        for m in MAC_PATTERN.finditer(text):
            entities.append(self._make_entity(
                m, PIIType.MAC_ADDRESS, score=0.9,
                source="universal-mac",
            ))

        return entities