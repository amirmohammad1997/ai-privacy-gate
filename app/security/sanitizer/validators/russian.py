"""Validators for Russian PII."""
import re


# ═══════════════════════════════════════════════════════════
# Russian SNILS (СНИЛС) — 11 digits
# ═══════════════════════════════════════════════════════════

def validate_russian_snils(snils: str) -> bool:
    """
    Validate Russian SNILS (pension insurance number).

    Format: 11 digits (###-###-### ##).
    Last 2 digits are checksum.
    """
    digits = re.sub(r"\D", "", snils)

    if len(digits) != 11:
        return False

    # Reject all-same-digit
    if len(set(digits)) == 1:
        return False

    # Checksum: sum of digit[i] * (9 - i) for i in 0..8
    total = sum(int(digits[i]) * (9 - i) for i in range(9))

    # Handle cases
    if total < 100:
        check = total
    elif total in (100, 101):
        check = 0
    else:
        check = total % 101
        if check == 100:
            check = 0

    return check == int(digits[9:11])


# ═══════════════════════════════════════════════════════════
# Russian INN (ИНН) — 10 or 12 digits
# ═══════════════════════════════════════════════════════════

def validate_russian_inn_10(inn: str) -> bool:
    """Validate Russian INN for legal entities (10 digits)."""
    digits = re.sub(r"\D", "", inn)

    if len(digits) != 10:
        return False

    weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
    total = sum(int(digits[i]) * weights[i] for i in range(9))
    check = (total % 11) % 10

    return check == int(digits[9])


def validate_russian_inn_12(inn: str) -> bool:
    """Validate Russian INN for individuals (12 digits)."""
    digits = re.sub(r"\D", "", inn)

    if len(digits) != 12:
        return False

    # First check digit (11th)
    weights_1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    total = sum(int(digits[i]) * weights_1[i] for i in range(10))
    check_1 = (total % 11) % 10

    if check_1 != int(digits[10]):
        return False

    # Second check digit (12th)
    weights_2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    total = sum(int(digits[i]) * weights_2[i] for i in range(11))
    check_2 = (total % 11) % 10

    return check_2 == int(digits[11])


def validate_russian_inn(inn: str) -> bool:
    """Auto-detect INN length and validate."""
    digits = re.sub(r"\D", "", inn)
    if len(digits) == 10:
        return validate_russian_inn_10(digits)
    elif len(digits) == 12:
        return validate_russian_inn_12(digits)
    return False


# ═══════════════════════════════════════════════════════════
# Russian Phone
# ═══════════════════════════════════════════════════════════

def validate_russian_phone(phone: str) -> bool:
    """
    Validate Russian phone number.

    Mobile: +7 9XX XXX-XX-XX
    Landline: +7 XXX XXX-XX-XX
    """
    digits = re.sub(r"\D", "", phone)

    # Strip +7 or 8
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]

    if not digits.startswith("7"):
        return False

    if len(digits) != 11:
        return False

    # Mobile: 9XX
    if digits[1] == "9":
        return True

    # Landline: 3, 4, 8
    if digits[1] in "348":
        return True

    return False