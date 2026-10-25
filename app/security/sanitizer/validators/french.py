"""Validators for French PII."""
import re


# ═══════════════════════════════════════════════════════════
# French INSEE / NIR — 15 digits (Social Security Number)
# ═══════════════════════════════════════════════════════════

def validate_french_insee(insee: str) -> bool:
    """
    Validate French INSEE/NIR (social security number).

    Format: 15 digits
      - 1: gender (1=male, 2=female)
      - 2-3: year of birth
      - 4-5: month of birth (01-12, or 20-42 for special cases)
      - 6-7: department code (01-95, 2A, 2B, 97, 98, 99)
      - 8-10: commune code
      - 11-13: order number
      - 14-15: checksum (97 - (number mod 97))
    """
    digits = re.sub(r"\D", "", insee)

    if len(digits) != 15:
        return False

    # First digit: gender
    if digits[0] not in ("1", "2", "3", "4", "7", "8"):
        return False

    # Month: 01-12 or 20-42 (special cases) or 62-64
    month = int(digits[3:5])
    if not (1 <= month <= 12 or 20 <= month <= 42 or 62 <= month <= 64):
        return False

    # Checksum: 97 - (14 digits mod 97)
    number = int(digits[:13])
    check = 97 - (number % 97)

    return check == int(digits[13:15])


# ═══════════════════════════════════════════════════════════
# French Phone
# ═══════════════════════════════════════════════════════════

def validate_french_phone(phone: str) -> bool:
    """
    Validate French phone number.

    Accepts both:
      - Local: 06 12 34 56 78
      - International: +33 6 12 34 56 78
    """
    digits = re.sub(r"\D", "", phone)

    # Strip +33 or 0033
    if digits.startswith("0033"):
        digits = digits[4:]
    elif digits.startswith("33") and len(digits) >= 11:
        digits = digits[2:]

    # Now handle local format with leading 0
    if digits.startswith("0"):
        digits = digits[1:]

    if len(digits) != 9:
        return False

    # First digit (after stripping 0): 1-7, 9
    return digits[0] in "12345679"