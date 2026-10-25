"""Validators for Japanese PII."""
import re


# ═══════════════════════════════════════════════════════════
# Japanese My Number (マイナンバー) — 12 digits
# ═══════════════════════════════════════════════════════════

def validate_japanese_my_number(number: str) -> bool:
    """
    Validate Japanese My Number (12 digits).

    Checksum algorithm:
      For 12-digit number d1 d2 ... d12:
      - n = 11 - (Σ Pn × Qn mod 11)
      - Pn = digit value at position n (1-indexed)
      - Qn = n + 1 for n = 1..6, n - 5 for n = 7..11
      - If n > 9, use 0 as check digit
    """
    digits = re.sub(r"\D", "", number)

    if len(digits) != 12:
        return False

    # Reject all-same-digit
    if len(set(digits)) == 1:
        return False

    # Check digit calculation
    d = [int(x) for x in digits]

    # Compute weighted sum for first 11 digits
    total = 0
    for n in range(1, 12):  # n = 1..11
        p = d[11 - n]  # position from the right
        if n <= 6:
            q = n + 1
        else:
            q = n - 5
        total += p * q

    remainder = total % 11

    if remainder <= 1:
        check_digit = 0
    else:
        check_digit = 11 - remainder

    return check_digit == d[0]


# ═══════════════════════════════════════════════════════════
# Japanese Phone
# ═══════════════════════════════════════════════════════════

def validate_japanese_phone(phone: str) -> bool:
    """
    Validate Japanese phone number.

    Mobile: 090-XXXX-XXXX, 080-XXXX-XXXX, 070-XXXX-XXXX
    Landline: 0X-XXXX-XXXX, 0XX-XXX-XXXX, 0XXX-XX-XXXX
    """
    digits = re.sub(r"\D", "", phone)

    # Strip +81 or 0081
    if digits.startswith("0081") and len(digits) == 15:
        digits = digits[4:]
    elif digits.startswith("81") and len(digits) == 12:
        digits = digits[2:]

    # Strip leading 0
    if digits.startswith("0"):
        digits = digits[1:]

    # Now should be 9-10 digits
    if not (9 <= len(digits) <= 10):
        return False

    # Mobile: starts with 90, 80, 70
    if len(digits) == 10:
        if digits[:2] in ("90", "80", "70"):
            return True

    # Landline: starts with 3-9
    if len(digits) in (9, 10):
        if digits[0] in "3456789":
            return True

    return False