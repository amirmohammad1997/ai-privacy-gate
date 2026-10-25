"""
Universal validators — work for all languages.

These validate format and checksum for PII types that
are language-independent (emails, IPs, credit cards, etc.).
"""
import ipaddress
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Luhn Algorithm — Credit Cards
# ═══════════════════════════════════════════════════════════

def validate_luhn(number: str) -> bool:
    """
    Luhn checksum for credit/debit cards.

    Works with any card issuer worldwide (Visa, Mastercard,
    Amex, UnionPay, JCB, etc.).
    """
    digits = [int(d) for d in number if d.isdigit()]

    if len(digits) < 12 or len(digits) > 19:
        return False

    # Reject all-same-digit numbers
    if len(set(digits)) == 1:
        return False

    digits.reverse()
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d

    return total % 10 == 0


# ═══════════════════════════════════════════════════════════
# IBAN — International Bank Account Number
# ═══════════════════════════════════════════════════════════

# IBAN lengths per country (partial list — expanding as needed)
IBAN_LENGTHS = {
    "AL": 28, "AD": 24, "AT": 20, "AZ": 28, "BH": 22, "BE": 16,
    "BA": 20, "BR": 29, "BG": 22, "CR": 22, "HR": 21, "CY": 28,
    "CZ": 24, "DK": 18, "DO": 28, "EE": 20, "FO": 18, "FI": 18,
    "FR": 27, "GE": 22, "DE": 22, "GI": 23, "GR": 27, "GL": 18,
    "GT": 28, "HU": 28, "IS": 26, "IE": 22, "IL": 23, "IT": 27,
    "JO": 30, "KZ": 20, "KW": 30, "LV": 21, "LB": 28, "LI": 21,
    "LT": 20, "LU": 20, "MK": 19, "MT": 31, "MR": 27, "MU": 30,
    "MD": 24, "MC": 27, "ME": 22, "NL": 18, "NO": 15, "PK": 24,
    "PS": 29, "PL": 28, "PT": 25, "QA": 29, "RO": 24, "SM": 27,
    "SA": 24, "RS": 22, "SK": 24, "SI": 19, "ES": 24, "SE": 24,
    "CH": 21, "TN": 24, "TR": 26, "AE": 23, "GB": 22, "VA": 22,
    "IR": 26,  # Iran (Sheba)
}


def validate_iban(iban: str) -> bool:
    """
    Validate IBAN using MOD-97 checksum.

    Also used for Iran Sheba (IR prefix).
    """
    iban = iban.strip().upper().replace(" ", "").replace("-", "")

    if len(iban) < 15 or len(iban) > 34:
        return False

    country = iban[:2]
    if not country.isalpha():
        return False

    # Length check per country
    if country in IBAN_LENGTHS:
        if len(iban) != IBAN_LENGTHS[country]:
            return False

    # Rearrange: move first 4 chars to end
    rearranged = iban[4:] + iban[:4]

    # Replace letters with numbers (A=10, ..., Z=35)
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        elif ch.isalpha():
            numeric += str(ord(ch) - ord("A") + 10)
        else:
            return False

    # MOD 97
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


# ═══════════════════════════════════════════════════════════
# IP Address
# ═══════════════════════════════════════════════════════════

def validate_ip(ip: str) -> bool:
    """
    Validate IPv4 or IPv6 address.

    Uses Python's built-in ipaddress module.
    """
    try:
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False


# ═══════════════════════════════════════════════════════════
# URL
# ═══════════════════════════════════════════════════════════

def validate_url(url: str) -> bool:
    """
    Basic URL validation.

    Only accepts http, https, ftp, ftps.
    """
    try:
        parsed = urlparse(url.strip())
        return (
            parsed.scheme in ("http", "https", "ftp", "ftps")
            and bool(parsed.netloc)
            and "." in parsed.netloc
        )
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
# Email
# ═══════════════════════════════════════════════════════════

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
)


def validate_email(email: str) -> bool:
    """Basic email validation."""
    if not email or len(email) > 254:
        return False

    if email.count("@") != 1:
        return False

    local, _, domain = email.partition("@")

    if not local or not domain or len(local) > 64:
        return False

    if not EMAIL_REGEX.match(email):
        return False

    if domain.startswith(".") or domain.endswith("."):
        return False

    return True


# ═══════════════════════════════════════════════════════════
# MAC Address
# ═══════════════════════════════════════════════════════════

MAC_REGEX = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
)


def validate_mac(mac: str) -> bool:
    """Validate MAC address."""
    return bool(MAC_REGEX.match(mac.strip()))