"""Validators for Persian (Iranian) PII."""
import re


def validate_iran_national_id(nid: str) -> bool:
    """
    Validate Iranian National ID (کد ملی).

    Format: 10 digits with checksum.
    Algorithm:
        sum = Σ(digit[i] * (10 - i)) for i in 0..8
        remainder = sum % 11
        check_digit = remainder if remainder < 2 else 11 - remainder
    """
    if not nid or len(nid) != 10:
        return False

    if not nid.isdigit():
        return False

    # Reject all-same-digit numbers (0000000000, 1111111111, ...)
    if len(set(nid)) == 1:
        return False

    # Reject known test IDs
    if nid in {"0123456789", "9876543210"}:
        return False

    digits = [int(d) for d in nid]
    checksum = sum(digits[i] * (10 - i) for i in range(9))
    remainder = checksum % 11

    if remainder < 2:
        check_digit = remainder
    else:
        check_digit = 11 - remainder

    return check_digit == digits[9]


def validate_iran_mobile(mobile: str) -> bool:
    """
    Validate Iranian mobile number.

    Handles all common formats:
      - +98 914 587 2154  → +98 + 10 digits
      - 0098 914 587 2154 → 0098 + 10 digits
      - 98 914 587 2154   → 98 + 10 digits
      - 0914 587 2154     → 0 + 10 digits (local)
      - 914 587 2154      → 10 digits (bare)
    """
    digits = re.sub(r"\D", "", mobile)

    # Strip international prefixes
    # 0098... (14 digits: 0098 + 10)
    if digits.startswith("0098") and len(digits) == 14:
        digits = digits[4:]

    # 98... (12 digits: 98 + 10)
    elif digits.startswith("98") and len(digits) == 12:
        digits = digits[2:]

    # Strip leading 0 for local format
    # 0 + 10 digits (11 total)
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]

    # Now should be exactly 10 digits
    if len(digits) != 10:
        return False

    # Must start with 9 (Iranian mobile prefix)
    if not digits.startswith("9"):
        return False

    # Second digit must be a valid operator code
    # 0: Irancell, 1: Hamrah-e-Aval, 2: Rightel, 3: MTN, 9: Shatel
    if digits[1] not in "01239":
        return False

    return True


def validate_iran_postal_code(code: str) -> bool:
    """
    Validate Iranian Postal Code.

    Format: 10 digits, not starting with 0 or 2.
    """
    if not code or len(code) != 10:
        return False

    if not code.isdigit():
        return False

    if code[0] in ("0", "2"):
        return False

    if len(set(code)) == 1:
        return False

    return True