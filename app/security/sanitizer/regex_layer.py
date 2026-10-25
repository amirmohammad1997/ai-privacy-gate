"""
Regex-based PII detection (English only).

Detects:
- Email addresses
- US phone numbers
- SSN
- Credit cards (with Luhn validation)
- IP addresses
- US ZIP codes
"""
import re
import logging

from .models import PIIEntity, PIIType

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Regex Patterns
# ═══════════════════════════════════════════════════════════

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# US Phone: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
US_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}(?!\d)"
)

# SSN: 123-45-6789 or 123 45 6789
SSN_PATTERN = re.compile(
    r"\b\d{3}[\s\-]\d{2}[\s\-]\d{4}\b"
)

# Credit Card: 16 digits with optional separators
CREDIT_CARD_PATTERN = re.compile(
    r"(?<!\d)(?:\d{4}[\s\-]?){3}\d{4}(?!\d)"
)

# IP Address (IPv4)
IP_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# US ZIP: 12345 or 12345-6789
US_ZIP_PATTERN = re.compile(
    r"\b\d{5}(?:-\d{4})?\b"
)


# ═══════════════════════════════════════════════════════════
# Validators
# ═══════════════════════════════════════════════════════════

def validate_luhn(number: str) -> bool:
    """Luhn checksum for credit cards."""
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 2:
        return False

    digits.reverse()
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d

    return total % 10 == 0


def validate_us_ssn(ssn: str) -> bool:
    """Basic SSN validation."""
    digits = re.sub(r"\D", "", ssn)
    if len(digits) != 9:
        return False

    area, group, serial = digits[:3], digits[3:5], digits[5:]

    # Invalid area codes
    if area in ("000", "666") or area[0] == "9":
        return False

    # Invalid group/serial
    if group == "00" or serial == "0000":
        return False

    return True


def validate_us_phone(phone: str) -> bool:
    """Basic US phone validation."""
    digits = re.sub(r"\D", "", phone)

    if digits.startswith("1") and len(digits) == 11:
        digits = digits[1:]

    if len(digits) != 10:
        return False

    # Area code and exchange code cannot start with 0 or 1
    if digits[0] in "01" or digits[3] in "01":
        return False

    return True


# ═══════════════════════════════════════════════════════════
# Main Layer
# ═══════════════════════════════════════════════════════════

class RegexLayer:
    """
    Detects PII using regex patterns.

    Each detector uses format validation to reduce false positives.
    """

    def detect(self, text: str) -> list[PIIEntity]:
        """Detect all PII in the text."""
        if not text:
            return []

        entities: list[PIIEntity] = []

        # ─── Email ───
        for m in EMAIL_PATTERN.finditer(text):
            entities.append(PIIEntity(
                start=m.start(),
                end=m.end(),
                entity_type=PIIType.EMAIL,
                text=m.group(),
                score=0.95,
                source="regex-email",
            ))

        # ─── SSN ───
        for m in SSN_PATTERN.finditer(text):
            if validate_us_ssn(m.group()):
                entities.append(PIIEntity(
                    start=m.start(),
                    end=m.end(),
                    entity_type=PIIType.SSN,
                    text=m.group(),
                    score=0.95,
                    source="regex-ssn",
                ))

        # ─── Credit Card ───
        for m in CREDIT_CARD_PATTERN.finditer(text):
            digits = re.sub(r"[\s\-]", "", m.group())
            if validate_luhn(digits):
                entities.append(PIIEntity(
                    start=m.start(),
                    end=m.end(),
                    entity_type=PIIType.CREDIT_CARD,
                    text=m.group(),
                    score=0.95,
                    source="regex-cc",
                ))

        # ─── US Phone ───
        for m in US_PHONE_PATTERN.finditer(text):
            if validate_us_phone(m.group()):
                entities.append(PIIEntity(
                    start=m.start(),
                    end=m.end(),
                    entity_type=PIIType.PHONE,
                    text=m.group(),
                    score=0.85,
                    source="regex-phone",
                ))

        # ─── IP Address ───
        for m in IP_PATTERN.finditer(text):
            entities.append(PIIEntity(
                start=m.start(),
                end=m.end(),
                entity_type=PIIType.IP_ADDRESS,
                text=m.group(),
                score=0.85,
                source="regex-ip",
            ))

        # ─── US ZIP (only if context suggests it's a ZIP) ───
        for m in US_ZIP_PATTERN.finditer(text):
            # فقط اگر نزدیک کلمه‌ی zip باشه
            window_start = max(0, m.start() - 20)
            window_end = min(len(text), m.end() + 20)
            window = text[window_start:window_end].lower()

            if "zip" in window or "postal" in window:
                entities.append(PIIEntity(
                    start=m.start(),
                    end=m.end(),
                    entity_type=PIIType.US_ZIP,
                    text=m.group(),
                    score=0.8,
                    source="regex-zip-context",
                ))

        # حذف همپوشانی‌ها
        entities = self._dedupe(entities)

        return entities

    @staticmethod
    def _dedupe(entities: list[PIIEntity]) -> list[PIIEntity]:
        """Remove overlapping entities, preferring higher score."""
        if not entities:
            return []

        # Sort: higher score first, then longer
        sorted_e = sorted(entities, key=lambda e: (-e.score, -e.length()))

        kept: list[PIIEntity] = []
        for entity in sorted_e:
            if any(entity.overlaps(k) for k in kept):
                continue
            kept.append(entity)

        return sorted(kept, key=lambda e: e.start)