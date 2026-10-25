"""Validators for PII detection."""

from .universal import (
    validate_luhn, validate_iban, validate_ip, validate_email,
)
from .english import (
    validate_us_ssn, validate_us_phone, validate_us_zip,
)
from .persian import (
    validate_iran_national_id, validate_iran_mobile, validate_iran_postal_code,
)
from .turkish import (
    validate_turkish_tckn, validate_turkish_phone,
)
from .chinese import (
    validate_chinese_id, validate_chinese_phone,
)
from .japanese import (
    validate_japanese_my_number, validate_japanese_phone,
)
from .korean import (
    validate_korean_rrn, validate_korean_phone,
)
from .arabic import (
    validate_saudi_national_id, validate_egyptian_national_id,
    validate_uae_emirates_id, validate_arabic_mobile,
)
from .spanish import (
    validate_spanish_dni, validate_spanish_nie, validate_spanish_phone,
)
from .french import (
    validate_french_insee, validate_french_phone,
)
from .german import (
    validate_german_steuer_id, validate_german_phone,
)
from .portuguese import (
    validate_brazilian_cpf, validate_brazilian_cnpj, validate_portuguese_phone,
)
from .russian import (
    validate_russian_snils, validate_russian_inn, validate_russian_phone,
)


__all__ = [
    # Universal
    "validate_luhn", "validate_iban", "validate_ip", "validate_email",
    # English
    "validate_us_ssn", "validate_us_phone", "validate_us_zip",
    # Persian
    "validate_iran_national_id", "validate_iran_mobile", "validate_iran_postal_code",
    # Turkish
    "validate_turkish_tckn", "validate_turkish_phone",
    # Chinese
    "validate_chinese_id", "validate_chinese_phone",
    # Japanese
    "validate_japanese_my_number", "validate_japanese_phone",
    # Korean
    "validate_korean_rrn", "validate_korean_phone",
    # Arabic
    "validate_saudi_national_id", "validate_egyptian_national_id",
    "validate_uae_emirates_id", "validate_arabic_mobile",
    # Spanish
    "validate_spanish_dni", "validate_spanish_nie", "validate_spanish_phone",
    # French
    "validate_french_insee", "validate_french_phone",
    # German
    "validate_german_steuer_id", "validate_german_phone",
    # Portuguese
    "validate_brazilian_cpf", "validate_brazilian_cnpj", "validate_portuguese_phone",
    # Russian
    "validate_russian_snils", "validate_russian_inn", "validate_russian_phone",
]