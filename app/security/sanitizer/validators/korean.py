"""Validators for Korean PII."""
import re
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# Korean Resident Registration Number (주민등록번호) — 13 digits
# ═══════════════════════════════════════════════════════════

def validate_korean_rrn(rrn: str) -> bool:
    """
    Validate Korean Resident Registration Number.

    Format: YYMMDD-GXXXXXX (13 digits)
    - YYMMDD: birth date (6 digits)
    - G: century/gender (1 digit)
    - XXXXXX: sequence + checksum
    """
    digits = re.sub(r"\D", "", rrn)

    if len(digits) != 13:
        return False

    # ─── Birth date ───
    yy = int(digits[0:2])
    mm = int(digits[2:4])
    dd = int(digits[4:6])

    if mm < 1 or mm > 12:
        return False
    if dd < 1 or dd > 31:
        return False

    # ─── Century/gender digit (7th) ───
    gender_digit = int(digits[6])

    # 1,2 = 1900s; 3,4 = 2000s; 5,6 = 1900s foreigners; 7,8 = 2000s foreigners; 9,0 = 1800s
    if gender_digit not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 0):
        return False

    # ─── Checksum ───
    weights = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
    total = sum(int(digits[i]) * weights[i] for i in range(12))
    check_digit = (11 - (total % 11)) % 10

    return check_digit == int(digits[12])


# ═══════════════════════════════════════════════════════════
# Korean Phone
# ═══════════════════════════════════════════════════════════

def validate_korean_phone(phone: str) -> bool:
    """
    Validate Korean phone number.

    Mobile: 010-XXXX-XXXX, 011-XXX-XXXX, etc.
    Landline: 02-XXX-XXXX (Seoul), 0XX-XXX-XXXX
    """
    digits = re.sub(r"\D", "", phone)

    # Strip +82 or 0082
    if digits.startswith("0082") and len(digits) >= 13:
        digits = digits[4:]
    elif digits.startswith("82") and len(digits) >= 11:
        digits = digits[2:]

    # Strip leading 0
    if digits.startswith("0"):
        digits = digits[1:]

    # Mobile: starts with 10 (after stripping 0)
    if len(digits) == 10 and digits.startswith("10"):
        return True

    # Some older mobiles: 11, 16, 17, 18, 19 (8 digits after stripping 0)
    if len(digits) in (9, 10):
        if digits[:2] in ("11", "16", "17", "18", "19"):
            return True

    # Seoul landline: 2 (after stripping 0)
    if len(digits) in (9, 10) and digits.startswith("2"):
        return True

    # Other landlines: 31-99 prefixes
    if len(digits) in (9, 10):
        if digits[0] in "3456":
            return True

    return False