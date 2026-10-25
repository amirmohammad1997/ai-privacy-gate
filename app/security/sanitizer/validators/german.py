"""Validators for German PII."""
import re


# ═══════════════════════════════════════════════════════════
# German Steuer-ID (Tax ID) — 11 digits
# ═══════════════════════════════════════════════════════════

def validate_german_steuer_id(tax_id: str) -> bool:
    """
    Validate German Steuer-ID (Tax Identification Number).

    Format: 11 digits with ISO 7064 MOD 11,10 checksum.
      - First digit: 1-9 (never 0)
      - Digits 2-10: any (but not all same)
      - Digit 11: check digit
    """
    digits = re.sub(r"\D", "", tax_id)

    if len(digits) != 11:
        return False

    # First digit cannot be 0
    if digits[0] == "0":
        return False

    # Not all same digit
    if len(set(digits)) == 1:
        return False

    # ─── ISO 7064 MOD 11,10 checksum ───
    # Process first 10 digits
    product = 10
    for i in range(10):
        digit = int(digits[i])
        # Sum
        s = (digit + product) % 10
        if s == 0:
            s = 10
        # Multiply
        product = (s * 2) % 11

    check_digit = 11 - product
    if check_digit == 10:
        check_digit = 0

    return check_digit == int(digits[10])


# ═══════════════════════════════════════════════════════════
# German Phone
# ═══════════════════════════════════════════════════════════

def validate_german_phone(phone: str) -> bool:
    """
    Validate German phone number.

    Accepts both:
      - Local: 0171 1234567
      - International: +49 171 1234567
    """
    digits = re.sub(r"\D", "", phone)

    # Strip +49 or 0049
    if digits.startswith("0049"):
        digits = digits[4:]
    elif digits.startswith("49") and len(digits) >= 11:
        digits = digits[2:]

    # Now handle local format with leading 0
    if digits.startswith("0"):
        digits = digits[1:]

    # Mobile (after stripping 0): starts with 15, 16, 17
    if 10 <= len(digits) <= 11:
        if digits[:2] in ("15", "16", "17"):
            return True

    # Landline: 2-9
    if 9 <= len(digits) <= 12:
        if digits[0] in "23456789":
            return True

    return False