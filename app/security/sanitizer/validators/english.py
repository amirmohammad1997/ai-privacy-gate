"""Validators for English/US PII."""
import re


def validate_us_ssn(ssn: str) -> bool:
    """
    Validate US Social Security Number.

    Format: AAA-GG-SSSS
    - Area (AAA): 001-899, excluding 666 and 900-999
    - Group (GG): 01-99
    - Serial (SSSS): 0001-9999
    """
    digits = re.sub(r"\D", "", ssn)
    if len(digits) != 9:
        return False

    area, group, serial = digits[:3], digits[3:5], digits[5:]

    # Invalid area codes
    if area == "000" or area == "666" or area[0] == "9":
        return False

    # Invalid group
    if group == "00":
        return False

    # Invalid serial
    if serial == "0000":
        return False

    # Reject known invalid test SSNs
    if ssn.replace("-", "").replace(" ", "") in {
        "078051120",  # Woolworth wallet
        "219099999",  # ()
        "123456789",  # Sequential
    }:
        return False

    return True


def validate_us_phone(phone: str) -> bool:
    """
    Validate US/Canada phone number.

    Format: NPA-NXX-XXXX
    - NPA (Area code): 2-9 as first digit
    - NXX (Exchange): 2-9 as first digit
    """
    digits = re.sub(r"\D", "", phone)

    # Handle country code +1
    if digits.startswith("1") and len(digits) == 11:
        digits = digits[1:]

    if len(digits) != 10:
        return False

    # Area code and exchange code cannot start with 0 or 1
    if digits[0] in "01" or digits[3] in "01":
        return False

    # Reject 555 fake numbers (555-0100 to 555-0199 are reserved)
    # Actually keep 555 since it appears in real areas
    # Only reject obviously fake
    if digits[3:6] == "555" and digits[6:10].startswith("01"):
        return False

    return True


def validate_us_zip(zip_code: str) -> bool:
    """
    Validate US ZIP code.

    Format: 12345 or 12345-6789
    """
    zip_code = zip_code.strip()
    return bool(re.fullmatch(r"\d{5}(?:-\d{4})?", zip_code))