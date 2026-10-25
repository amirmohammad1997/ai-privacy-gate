"""Validators for Arabic PII."""
import re


# ═══════════════════════════════════════════════════════════
# Saudi National ID (هوية وطنية) — 10 digits
# ═══════════════════════════════════════════════════════════

def validate_saudi_national_id(sid: str) -> bool:
    """
    Validate Saudi National ID (10 digits).

    Starts with 1 (citizen) or 2 (resident).
    Uses Luhn-like checksum.
    """
    digits = re.sub(r"\D", "", sid)

    if len(digits) != 10:
        return False

    # First digit: 1 (citizen) or 2 (resident)
    if digits[0] not in ("1", "2"):
        return False

    # Luhn-like checksum
    total = 0
    for i in range(9):
        d = int(digits[i])
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d

    check = (10 - (total % 10)) % 10
    return check == int(digits[9])


# ═══════════════════════════════════════════════════════════
# Egyptian National ID — 14 digits
# ═══════════════════════════════════════════════════════════

def validate_egyptian_national_id(eid: str) -> bool:
    """
    Validate Egyptian National ID (14 digits).

    Format: C YYMMDD GG SSSS C
    - C: century (2=1900s, 3=2000s)
    - YYMMDD: birth date
    - GG: governorate code
    - SSSS: sequence
    - C: check digit
    """
    digits = re.sub(r"\D", "", eid)

    if len(digits) != 14:
        return False

    # Century digit
    if digits[0] not in ("2", "3"):
        return False

    # Birth date
    yy = int(digits[1:3])
    mm = int(digits[3:5])
    dd = int(digits[5:7])

    if mm < 1 or mm > 12:
        return False
    if dd < 1 or dd > 31:
        return False

    # Governorate code
    gov = int(digits[7:9])
    if gov < 1 or gov > 88:
        return False

    return True


# ═══════════════════════════════════════════════════════════
# UAE Emirates ID — 15 digits
# ═══════════════════════════════════════════════════════════

def validate_uae_emirates_id(eid: str) -> bool:
    """
    Validate UAE Emirates ID (15 digits).

    Format: 784-YYYY-NNNNNNN-C
    - 784: UAE country code
    - YYYY: year of birth
    - NNNNNNN: serial
    - C: check digit
    """
    digits = re.sub(r"\D", "", eid)

    if len(digits) != 15:
        return False

    # Must start with 784 (UAE)
    if not digits.startswith("784"):
        return False

    # Birth year
    year = int(digits[3:7])
    if year < 1900 or year > 2100:
        return False

    return True


# ═══════════════════════════════════════════════════════════
# Arabic Mobile Phone (generic — for common formats)
# ═══════════════════════════════════════════════════════════

def validate_arabic_mobile(phone: str) -> bool:
    """
    Validate Arabic mobile phone.

    Covers: Saudi, UAE, Egypt, Qatar, Kuwait, Bahrain, Oman, Jordan, Lebanon.
    """
    digits = re.sub(r"\D", "", phone)

    # GCC country codes: 966 (SA), 971 (AE), 20 (EG), 974 (QA), 965 (KW),
    # 973 (BH), 968 (OM), 962 (JO), 961 (LB)

    country_codes = {
        "966": 9,   # Saudi: 966 5X XXX XXXX
        "971": 9,   # UAE: 971 5X XXX XXXX
        "20": 10,   # Egypt: 20 1X XXXX XXXX
        "974": 8,   # Qatar
        "965": 8,   # Kuwait
        "973": 8,   # Bahrain
        "968": 8,   # Oman
        "962": 9,   # Jordan
        "961": 8,   # Lebanon
    }

    for cc, expected_len in country_codes.items():
        if digits.startswith(cc):
            remaining = digits[len(cc):]
            if len(remaining) == expected_len:
                # Must start with 5 (mobile) for GCC, 1 for Egypt
                if cc == "20":
                    return remaining.startswith("1")
                return remaining.startswith("5")

    # Without country code — try leading 0 + number
    if digits.startswith("0"):
        digits = digits[1:]

    # Saudi/UAE: 5XXXXXXXX
    if len(digits) == 9 and digits.startswith("5"):
        return True

    # Egypt: 1XXXXXXXXX
    if len(digits) == 10 and digits.startswith("1"):
        return True

    return False