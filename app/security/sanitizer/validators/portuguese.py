"""Validators for Portuguese/Brazilian PII."""
import re


# ═══════════════════════════════════════════════════════════
# Brazilian CPF (individual) — 11 digits
# ═══════════════════════════════════════════════════════════

def validate_brazilian_cpf(cpf: str) -> bool:
    """
    Validate Brazilian CPF (Cadastro de Pessoas Físicas).

    Format: 11 digits with two check digits.
    """
    digits = re.sub(r"\D", "", cpf)

    if len(digits) != 11:
        return False

    # Reject all-same-digit (known invalid)
    if len(set(digits)) == 1:
        return False

    # ─── First check digit ───
    total = sum(int(digits[i]) * (10 - i) for i in range(9))
    remainder = total % 11
    check_1 = 0 if remainder < 2 else 11 - remainder

    if check_1 != int(digits[9]):
        return False

    # ─── Second check digit ───
    total = sum(int(digits[i]) * (11 - i) for i in range(10))
    remainder = total % 11
    check_2 = 0 if remainder < 2 else 11 - remainder

    return check_2 == int(digits[10])


# ═══════════════════════════════════════════════════════════
# Brazilian CNPJ (company) — 14 digits
# ═══════════════════════════════════════════════════════════

def validate_brazilian_cnpj(cnpj: str) -> bool:
    """
    Validate Brazilian CNPJ (Cadastro Nacional da Pessoa Jurídica).

    Format: 14 digits with two check digits.
    """
    digits = re.sub(r"\D", "", cnpj)

    if len(digits) != 14:
        return False

    # Reject all-same-digit
    if len(set(digits)) == 1:
        return False

    # ─── First check digit ───
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(digits[i]) * weights_1[i] for i in range(12))
    remainder = total % 11
    check_1 = 0 if remainder < 2 else 11 - remainder

    if check_1 != int(digits[12]):
        return False

    # ─── Second check digit ───
    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(digits[i]) * weights_2[i] for i in range(13))
    remainder = total % 11
    check_2 = 0 if remainder < 2 else 11 - remainder

    return check_2 == int(digits[13])


# ═══════════════════════════════════════════════════════════
# Portuguese Phone (Portugal + Brazil)
# ═══════════════════════════════════════════════════════════

def validate_portuguese_phone(phone: str) -> bool:
    """
    Validate Portuguese or Brazilian phone number.

    Accepts both local and international formats.
    """
    digits = re.sub(r"\D", "", phone)

    # ─── Portugal (+351) ───
    if digits.startswith("00351"):
        digits = digits[5:]
    elif digits.startswith("351") and len(digits) >= 11:
        digits = digits[3:]

    # Portugal: 9 digits starting with 2 or 9
    if len(digits) == 9 and digits[0] in "29":
        return True

    # ─── Brazil (+55) ───
    # Reset for Brazil check
    digits_br = re.sub(r"\D", "", phone)

    if digits_br.startswith("0055"):
        digits_br = digits_br[4:]
    elif digits_br.startswith("55") and len(digits_br) >= 11:
        digits_br = digits_br[2:]

    # Brazil: area code (2 digits) + number (8-9 digits) = 10-11 digits
    if len(digits_br) in (10, 11):
        # Area code: 11-99
        area = int(digits_br[:2])
        if 11 <= area <= 99:
            return True

    return False