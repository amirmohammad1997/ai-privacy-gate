"""
Text normalizer for security analysis.

Handles common bypass techniques:
  - Invisible Unicode characters
  - Homoglyphs (Cyrillic/Greek lookalikes)
  - Base64 / Hex encoding
  - Reversed text
  - Leet speak
"""
import base64
import binascii
import logging
import re
import unicodedata
from typing import Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Invisible Characters
# ═══════════════════════════════════════════════════════════

INVISIBLE_CHARS = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\u200e",  # LRM
    "\u200f",  # RLM
    "\u202a",  # LEFT-TO-RIGHT EMBEDDING
    "\u202b",  # RIGHT-TO-LEFT EMBEDDING
    "\u202c",  # POP DIRECTIONAL
    "\u202d",  # LEFT-TO-RIGHT OVERRIDE
    "\u202e",  # RIGHT-TO-LEFT OVERRIDE
    "\u2060",  # WORD JOINER
    "\u2061",  # FUNCTION APPLICATION
    "\u2062",  # INVISIBLE TIMES
    "\u2063",  # INVISIBLE SEPARATOR
    "\u2064",  # INVISIBLE PLUS
    "\ufeff",  # BOM
    "\u00ad",  # SOFT HYPHEN
}


# ═══════════════════════════════════════════════════════════
# Homoglyphs (Cyrillic/Greek → Latin)
# ═══════════════════════════════════════════════════════════

HOMOGLYPH_MAP = {
    # Cyrillic → Latin
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c",
    "у": "y", "х": "x", "ѕ": "s", "і": "i", "ј": "j",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M",
    "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T",
    "У": "Y", "Х": "X",
    # Greek → Latin
    "α": "a", "β": "b", "ε": "e", "ι": "i", "κ": "k",
    "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "υ": "u",
    "χ": "x", "γ": "y",
}


# ═══════════════════════════════════════════════════════════
# Leet Speak
# ═══════════════════════════════════════════════════════════

LEET_MAP = {
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "8": "b", "@": "a", "$": "s",
}


# ═══════════════════════════════════════════════════════════
# Core Functions
# ═══════════════════════════════════════════════════════════

def remove_invisible(text: str) -> str:
    """Remove invisible characters."""
    return "".join(c for c in text if c not in INVISIBLE_CHARS)


def normalize_unicode(text: str) -> str:
    """Apply NFKC normalization."""
    return unicodedata.normalize("NFKC", text)


def replace_homoglyphs(text: str) -> str:
    """Replace lookalike characters."""
    return "".join(HOMOGLYPH_MAP.get(c, c) for c in text)


def replace_leet(text: str) -> str:
    """Convert leet speak."""
    return "".join(LEET_MAP.get(c, c) for c in text)


def collapse_spaces(text: str) -> str:
    """Collapse all whitespace to single spaces."""
    space_chars = r"[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000\s]"
    return re.sub(space_chars + "+", " ", text).strip()


def detect_base64(text: str) -> Optional[str]:
    """Detect & decode base64 chunks."""
    b64_pattern = re.compile(r"\b[A-Za-z0-9+/]{20,}={0,2}\b")
    for m in b64_pattern.finditer(text):
        candidate = m.group()
        try:
            decoded = base64.b64decode(candidate, validate=True).decode(
                "utf-8", errors="ignore"
            )
            if len(decoded) > 5 and decoded.isprintable():
                return decoded
        except (binascii.Error, ValueError, UnicodeDecodeError):
            continue
    return None


def detect_hex(text: str) -> Optional[str]:
    """Detect & decode hex chunks."""
    hex_pattern = re.compile(r"\b[0-9a-fA-F]{20,}\b")
    for m in hex_pattern.finditer(text):
        candidate = m.group()
        if len(candidate) % 2 != 0:
            continue
        try:
            decoded = bytes.fromhex(candidate).decode("utf-8", errors="ignore")
            if len(decoded) > 5 and decoded.isprintable():
                return decoded
        except (ValueError, UnicodeDecodeError):
            continue
    return None


def reverse_if_reversed(text: str) -> str:
    """Detect reversed text."""
    reversed_keywords = ["erongi", "suoiverp", "snoitcurtsni", "metsys"]
    words = text.lower().split()
    if sum(1 for w in words if w in reversed_keywords) >= 1:
        return text[::-1]
    return text


# ═══════════════════════════════════════════════════════════
# Main Normalize
# ═══════════════════════════════════════════════════════════

def normalize(text: str, aggressive: bool = True) -> dict:
    """
    Normalize text with all techniques.

    Returns:
        {
            "original": str,
            "normalized": str,
            "decoded_extras": list[str],  # decoded base64/hex
            "flags": list[str],           # what was detected
        }
    """
    if not text:
        return {
            "original": "",
            "normalized": "",
            "decoded_extras": [],
            "flags": [],
        }

    original = text
    flags: list[str] = []
    decoded_extras: list[str] = []

    # 1. Remove invisible
    cleaned = remove_invisible(text)
    if len(cleaned) != len(text):
        flags.append("invisible_chars_removed")

    # 2. NFKC normalization
    normalized = normalize_unicode(cleaned)

    # 3. Homoglyphs
    if aggressive:
        new = replace_homoglyphs(normalized)
        if new != normalized:
            flags.append("homoglyphs_replaced")
            normalized = new

    # 4. Base64
    b64 = detect_base64(normalized)
    if b64:
        decoded_extras.append(b64)
        flags.append("base64_decoded")

    # 5. Hex
    hx = detect_hex(normalized)
    if hx:
        decoded_extras.append(hx)
        flags.append("hex_decoded")

    # 6. Reversed
    if aggressive:
        reversed_check = reverse_if_reversed(normalized)
        if reversed_check != normalized:
            decoded_extras.append(reversed_check)
            flags.append("reversed_text")

    # 7. Collapse whitespace
    normalized = collapse_spaces(normalized)

    # 8. Leet (only if text has Latin letters)
    if aggressive and re.search(r"[A-Za-z]", normalized):
        leet = replace_leet(normalized)
        # Only apply if diff is small (< 40%)
        diff = sum(1 for a, b in zip(normalized.lower(), leet.lower()) if a != b)
        if diff / max(len(normalized), 1) < 0.4:
            normalized = leet

    return {
        "original": original,
        "normalized": normalized,
        "decoded_extras": decoded_extras,
        "flags": flags,
    }