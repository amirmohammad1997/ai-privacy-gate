"""Validators for Chinese PII."""
import re


# ═══════════════════════════════════════════════════════════
# Chinese ID Card (身份证) — 18 digits
# ═══════════════════════════════════════════════════════════

# Weights for ISO 7064 MOD 11-2 checksum
_ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_ID_CHECK_CHARS = "10X98765432"


def validate_chinese_id(id_number: str) -> bool:
    """
    Validate Chinese national ID (身份证).

    Format: 18 characters
      - 6 digits: region code
      - 8 digits: birth date (YYYYMMDD)
      - 3 digits: sequence (odd=male, even=female)
      - 1 char: checksum (0-9 or X)
    """
    if not id_number or len(id_number) != 18:
        return False

    id_number = id_number.upper()

    # First 17 chars must be digits
    if not id_number[:17].isdigit():
        return False

    # Last char is digit or X
    if not (id_number[17].isdigit() or id_number[17] == "X"):
        return False

    # ─── Validate birth date ───
    year = int(id_number[6:10])
    month = int(id_number[10:12])
    day = int(id_number[12:14])

    if year < 1900 or year > 2100:
        return False
    if month < 1 or month > 12:
        return False
    if day < 1 or day > 31:
        return False

    # ─── Checksum ───
    total = sum(int(id_number[i]) * _ID_WEIGHTS[i] for i in range(17))
    expected_check = _ID_CHECK_CHARS[total % 11]

    return id_number[17] == expected_check


# ═══════════════════════════════════════════════════════════
# Chinese Mobile Phone
# ═══════════════════════════════════════════════════════════

def validate_chinese_phone(phone: str) -> bool:
    """
    Validate Chinese mobile phone.

    Format: 1XX XXXX XXXX (11 digits)
    - Starts with 1
    - Second digit: 3-9 (major operators)
    """
    digits = re.sub(r"\D", "", phone)

    # Strip +86 or 0086
    if digits.startswith("0086") and len(digits) == 15:
        digits = digits[4:]
    elif digits.startswith("86") and len(digits) == 13:
        digits = digits[2:]

    if len(digits) != 11:
        return False

    if not digits.startswith("1"):
        return False

    # Second digit: 3, 4, 5, 6, 7, 8, 9
    if digits[1] not in "3456789":
        return False

    return True