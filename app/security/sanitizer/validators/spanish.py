"""Validators for Spanish PII."""
import re


# ═══════════════════════════════════════════════════════════
# Spanish DNI / NIF — 8 digits + 1 letter
# ═══════════════════════════════════════════════════════════

DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


def validate_spanish_dni(dni: str) -> bool:
    """
    Validate Spanish DNI (Documento Nacional de Identidad).

    Format: 8 digits + 1 letter.
    The letter is derived from the number mod 23.
    """
    if not dni:
        return False

    dni = dni.upper().replace("-", "").replace(" ", "")

    if len(dni) != 9:
        return False

    number_part = dni[:8]
    letter_part = dni[8]

    if not number_part.isdigit():
        return False

    if not letter_part.isalpha():
        return False

    expected_letter = DNI_LETTERS[int(number_part) % 23]

    return letter_part == expected_letter


# ═══════════════════════════════════════════════════════════
# Spanish NIE — X/Y/Z + 7 digits + 1 letter
# ═══════════════════════════════════════════════════════════

def validate_spanish_nie(nie: str) -> bool:
    """
    Validate Spanish NIE (Número de Identificación de Extranjero).

    Format: [XYZ] + 7 digits + 1 letter.
    """
    if not nie:
        return False

    nie = nie.upper().replace("-", "").replace(" ", "")

    if len(nie) != 9:
        return False

    prefix = nie[0]
    if prefix not in "XYZ":
        return False

    number_part = nie[1:8]
    letter_part = nie[8]

    if not number_part.isdigit():
        return False

    if not letter_part.isalpha():
        return False

    # Map XYZ to 0/1/2
    prefix_map = {"X": "0", "Y": "1", "Z": "2"}
    full_number = prefix_map[prefix] + number_part

    expected_letter = DNI_LETTERS[int(full_number) % 23]

    return letter_part == expected_letter


# ═══════════════════════════════════════════════════════════
# Spanish Phone
# ═══════════════════════════════════════════════════════════

def validate_spanish_phone(phone: str) -> bool:
    """
    Validate Spanish phone number.

    Mobile: 6XX XXX XXX or 7XX XXX XXX (9 digits)
    Landline: 9XX XXX XXX (9 digits)
    """
    digits = re.sub(r"\D", "", phone)

    # Strip +34 or 0034
    if digits.startswith("0034") and len(digits) == 13:
        digits = digits[4:]
    elif digits.startswith("34") and len(digits) == 11:
        digits = digits[2:]

    if len(digits) != 9:
        return False

    # Must start with 6, 7, or 9 (Spain)
    return digits[0] in "679"