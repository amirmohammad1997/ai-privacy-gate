"""
Automatic language detection.

Supports 12 languages with layered heuristics:
  1. Script ranges (fastest for non-Latin)
  2. PII markers (very reliable)
  3. Special characters (Latin languages)
  4. Common words
  5. langdetect library (fallback)
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Supported Languages
# ═══════════════════════════════════════════════════════════

SUPPORTED_LANGUAGES = {
    "en", "fa", "tr", "ar", "zh", "ru",
    "es", "fr", "de", "pt", "ja", "ko",
}

DEFAULT_LANGUAGE = "en"


# ═══════════════════════════════════════════════════════════
# Persian vs Arabic Disambiguation
# ═══════════════════════════════════════════════════════════

PERSIAN_ONLY_CHARS = set("پچژگ")
PERSIAN_PREFERRED = set("یک")
ARABIC_PREFERRED = set("يكة")
ARABIC_DIACRITICS = set("ًٌٍَُِّْٰ")


PERSIAN_WORDS = {
    "است", "هستم", "هستی", "هستیم", "هستید", "هستند",
    "من", "تو", "او", "ما", "شما", "آنها", "ایشان",
    "این", "آن", "همین", "همان", "چه", "چی", "کجا",
    "کی", "چطور", "چگونه", "چرا", "که", "را", "با",
    "در", "به", "از", "برای", "هم", "نیز", "بسیار",
    "اگر", "آیا", "اما", "ولی", "یا", "و", "نه", "بله",
    "اسم", "نام", "سلام", "خداحافظ", "ممنون", "لطفا",
    "ملی", "کد", "شماره", "کارت", "بانکی", "موبایل",
    "شبا", "پستی", "همراه", "تلفن",
}

ARABIC_WORDS = {
    "هو", "هي", "هما", "هم", "هن",
    "أنا", "نحن", "أنت", "أنتم",
    "في", "على", "إلى", "عن", "من",
    "هذا", "هذه", "ذلك", "تلك", "هؤلاء",
    "التي", "الذي", "الذين",
    "كان", "كانت", "يكون", "تكون",
    "ليس", "ليست", "لكن", "لكنه",
    "هل", "كيف", "متى", "أين", "لماذا", "ماذا",
    "اسم", "سلام", "شكرا", "عفوا", "مرحبا",
    "هوية", "وطنية", "رقم", "قومي", "جوال",
}


# ═══════════════════════════════════════════════════════════
# ⭐ PII Markers — language-specific keywords
# ═══════════════════════════════════════════════════════════

LANGUAGE_PII_MARKERS = {
    "en": [
        "ssn", "social security", "zip code", "postal code",
        "driver license", "driver's license",
    ],
    "fa": [
        "کد ملی", "کدملی", "شماره ملی", "کدپستی", "کد پستی",
        "موبایل", "همراه", "شبا", "پاسپورت", "گذرنامه",
    ],
    "tr": [
        "tckn", "tc kimlik", "kimlik no", "tc no",
        "cep telefonu", "cep telefon", "cep no", "gsm",
    ],
    "ar": [
        "هوية وطنية", "هوية", "رقم قومي", "رقم قومى",
        "الرقم القومي", "جوال", "هاتف", "ibrahim",
    ],
    "zh": [
        "身份证", "身份证号", "手机号", "手机", "电话", "号码",
    ],
    "ja": [
        "マイナンバー", "個人番号", "電話番号", "携帯番号",
    ],
    "ko": [
        "주민등록번호", "주민번호", "전화번호", "휴대폰", "핸드폰",
    ],
    "ru": [
        "снилс", "инн", "паспорт", "телефон", "номер",
        "мобильный",
    ],
    "es": [
        "dni", "nie", "nif", "documento nacional",
        "móvil", "movil", "teléfono", "telefono",
        "número de", "numero de",
    ],
    "fr": [
        "insee", "nir", "sécurité sociale", "securite sociale",
        "téléphone", "telephone", "numéro",
    ],
    "de": [
        "steuer-id", "steuerid", "steuernummer",
        "handynummer", "telefonnummer", "telefon",
    ],
    "pt": [
        "cpf", "cnpj", "cadastro de pessoas",
        "celular", "telefone", "número",
    ],
}


# ═══════════════════════════════════════════════════════════
# Character Ranges
# ═══════════════════════════════════════════════════════════

CHAR_RANGES = {
    "ar": [
        (0x0600, 0x06FF),   # Arabic
        (0x0750, 0x077F),
        (0x08A0, 0x08FF),
        (0xFB50, 0xFDFF),
        (0xFE70, 0xFEFF),
    ],
    "zh": [
        (0x4E00, 0x9FFF),   # CJK Unified
        (0x3400, 0x4DBF),
        (0xF900, 0xFAFF),
        (0x20000, 0x2A6DF),
    ],
    "ja": [
        (0x3040, 0x309F),   # Hiragana
        (0x30A0, 0x30FF),   # Katakana
        (0x4E00, 0x9FFF),   # Kanji
    ],
    "ko": [
        (0xAC00, 0xD7AF),   # Hangul
        (0x1100, 0x11FF),
        (0x3130, 0x318F),
    ],
    "ru": [
        (0x0400, 0x04FF),   # Cyrillic
        (0x0500, 0x052F),
    ],
}


SPECIAL_CHARS = {
    "tr": set("ğĞıİşŞçÇöÖüÜ"),
    "es": set("ñÑ¿¡"),
    "fr": set("àâäéèêëïîôöùûüÿçÇœŒæÆ"),
    "de": set("äöüÄÖÜß"),
    "pt": set("ãõáéíóúâêôàçÃÕÁÉÍÓÚÂÊÔÀÇ"),
}


COMMON_WORDS = {
    "en": {
        "the", "is", "are", "and", "or", "my", "name", "hello", "world",
        "ssn", "phone", "email", "zip", "social", "security",
    },
    "fa": {
        "من", "است", "هستم", "اسم", "سلام", "شما", "این", "که",
        "کد", "ملی", "موبایل", "شماره", "تلفن", "پستی", "شبا",
    },
    "tr": {
        "ben", "sen", "ve", "bir", "bu", "değil", "merhaba", "adım",
        "tckn", "kimlik", "cep", "telefon", "numara", "tc",
    },
    "ru": {
        "я", "ты", "он", "она", "это", "и", "не", "привет",
        "инн", "снилс", "телефон", "номер", "мобильный",
    },
    "es": {
        "el", "la", "es", "y", "o", "mi", "nombre", "hola",
        "dni", "nie", "móvil", "movil", "teléfono", "telefono",
        "número", "documento", "nacional",
    },
    "fr": {
        "le", "la", "est", "et", "ou", "mon", "nom", "bonjour",
        "téléphone", "telephone", "numéro", "sécurité", "sociale",
    },
    "de": {
        "der", "die", "das", "ist", "und", "oder", "mein",
        "hallo", "telefon", "nummer", "steuer", "handynummer",
    },
    "pt": {
        "o", "a", "é", "e", "ou", "meu", "nome", "olá",
        "cpf", "cnpj", "telefone", "número", "celular", "cadastro",
    },
}


# ═══════════════════════════════════════════════════════════
# Detector
# ═══════════════════════════════════════════════════════════

class LanguageDetector:
    """Layered language detection."""

    def __init__(self, use_langdetect: bool = True):
        self.use_langdetect = use_langdetect
        self._langdetect_available = False

        if use_langdetect:
            try:
                import langdetect  # noqa
                self._langdetect_available = True
                logger.info("langdetect available")
            except ImportError:
                logger.info("langdetect not installed")

    def detect(self, text: str) -> str:
        """Detect language of text."""
        if not text or len(text.strip()) < 2:
            return DEFAULT_LANGUAGE

        # 1. Script detection
        script_lang = self._detect_by_script(text)
        if script_lang:
            return script_lang

        # 2. ⭐ PII markers (very reliable)
        pii_lang = self._detect_by_pii_markers(text)
        if pii_lang:
            return pii_lang

        # 3. Special chars (Latin)
        latin_lang = self._detect_by_special_chars(text)
        if latin_lang:
            return latin_lang

        # 4. Common words
        word_lang = self._detect_by_common_words(text)
        if word_lang:
            return word_lang

        # 5. langdetect
        if self._langdetect_available:
            try:
                import langdetect
                langdetect.DetectorFactory.seed = 0
                detected = langdetect.detect(text)
                mapping = {"zh-cn": "zh", "zh-tw": "zh", "pt-br": "pt"}
                detected = mapping.get(detected, detected)
                if detected in SUPPORTED_LANGUAGES:
                    return detected
            except Exception as e:
                logger.warning(f"langdetect failed: {e}")

        return DEFAULT_LANGUAGE

    # ═══════════════════════════════════════════════════════

    def _detect_by_script(self, text: str) -> Optional[str]:
        """Detect by script ranges."""
        counts: dict[str, int] = {}

        for char in text:
            code = ord(char)

            if 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F \
                    or 0x08A0 <= code <= 0x08FF or 0xFB50 <= code <= 0xFDFF \
                    or 0xFE70 <= code <= 0xFEFF:
                counts["arabic_script"] = counts.get("arabic_script", 0) + 1
            elif 0x3040 <= code <= 0x309F or 0x30A0 <= code <= 0x30FF:
                counts["ja_specific"] = counts.get("ja_specific", 0) + 1
            elif 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF \
                    or 0xF900 <= code <= 0xFAFF:
                counts["cjk"] = counts.get("cjk", 0) + 1
            elif 0xAC00 <= code <= 0xD7AF or 0x1100 <= code <= 0x11FF \
                    or 0x3130 <= code <= 0x318F:
                counts["ko"] = counts.get("ko", 0) + 1
            elif 0x0400 <= code <= 0x04FF or 0x0500 <= code <= 0x052F:
                counts["ru"] = counts.get("ru", 0) + 1

        if counts.get("arabic_script", 0) > 0:
            return self._disambiguate_persian_arabic(text)
        if counts.get("ja_specific", 0) > 0:
            return "ja"
        if counts.get("cjk", 0) > 0:
            return "zh"
        if counts.get("ko", 0) > 0:
            return "ko"
        if counts.get("ru", 0) > 0:
            return "ru"

        return None

    @staticmethod
    def _disambiguate_persian_arabic(text: str) -> str:
        """Distinguish Persian from Arabic."""
        persian_only = sum(1 for c in text if c in PERSIAN_ONLY_CHARS)
        arabic_only = sum(1 for c in text if c in ARABIC_PREFERRED)
        diacritics = sum(1 for c in text if c in ARABIC_DIACRITICS)

        words = set(re.findall(r"\S+", text))
        persian_count = len(words & PERSIAN_WORDS)
        arabic_count = len(words & ARABIC_WORDS)

        if persian_only > 0:
            return "fa"
        if arabic_only > 0 or diacritics > 2:
            return "ar"
        if persian_count > arabic_count:
            return "fa"
        if arabic_count > persian_count:
            return "ar"

        return "fa"

    def _detect_by_pii_markers(self, text: str) -> Optional[str]:
        """⭐ Detect by PII-specific keywords."""
        text_lower = text.lower()
        scores: dict[str, int] = {}

        for lang, markers in LANGUAGE_PII_MARKERS.items():
            for marker in markers:
                if marker.lower() in text_lower:
                    scores[lang] = scores.get(lang, 0) + 1

        if not scores:
            return None

        return max(scores, key=scores.get)

    @staticmethod
    def _detect_by_special_chars(text: str) -> Optional[str]:
        """Detect by unique special characters."""
        counts: dict[str, int] = {}

        for lang, chars in SPECIAL_CHARS.items():
            count = sum(1 for c in text if c in chars)
            if count > 0:
                counts[lang] = count

        if not counts:
            return None

        return max(counts, key=counts.get)

    @staticmethod
    def _detect_by_common_words(text: str) -> Optional[str]:
        """Detect by counting common words."""
        words = set(re.findall(r"\w+", text.lower()))
        if not words:
            return None

        counts: dict[str, int] = {}
        for lang, common in COMMON_WORDS.items():
            count = len(words & common)
            if count > 0:
                counts[lang] = count

        if not counts:
            return None

        return max(counts, key=counts.get)


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_detector: Optional[LanguageDetector] = None


def get_language_detector() -> LanguageDetector:
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    return _detector


def detect_language(text: str) -> str:
    return get_language_detector().detect(text)