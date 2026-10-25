"""Validators for Turkish PII."""
import re


def validate_turkish_tckn(tckn: str) -> bool:
    """
    Validate Turkish Republic ID Number (TCKN).

    Format: 11 digits with a specific checksum algorithm.
    """
    if not tckn or len(tckn) != 11:
        return False

    if not tckn.isdigit():
        return False

    # First digit cannot be 0
    if tckn[0] == "0":
        return False

    digits = [int(d) for d in tckn]

    # ─── Check digit 10 (index 9) ───
    odd_sum = sum(digits[i] for i in [0, 2, 4, 6, 8])
    even_sum = sum(digits[i] for i in [1, 3, 5, 7])

    check_10 = (odd_sum * 7 - even_sum) % 10

    if check_10 != digits[9]:
        return False

    # ─── Check digit 11 (index 10) ───
    check_11 = sum(digits[:10]) % 10

    if check_11 != digits[10]:
        return False

    return True


def validate_turkish_phone(phone: str) -> bool:
    """
    Validate Turkish mobile phone number.

    Format: 05XX XXX XX XX (11 digits)
    Or with country code: +90 5XX XXX XX XX
    """
    digits = re.sub(r"\D", "", phone)

    # +90 5XX → 905XX → strip 90
    if digits.startswith("90") and len(digits) == 12:
        digits = digits[2:]

    # Leading 0 (Turkish local format)
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]

    # Now should be 10 digits starting with 5 (mobile)
    if len(digits) != 10:
        return False

    if not digits.startswith("5"):
        return False

    # Second digit should be 3, 4, 5, or 6 (mobile operators)
    if digits[1] not in "3456":
        return False

    return True