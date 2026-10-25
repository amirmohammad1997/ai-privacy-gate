"""Data models for PII sanitization."""
from dataclasses import dataclass, field
from enum import Enum


class PIIType(str, Enum):
    # ─── Universal ───
    EMAIL = "EMAIL"
    URL = "URL"
    IP_ADDRESS = "IP_ADDRESS"
    MAC_ADDRESS = "MAC_ADDRESS"
    CREDIT_CARD = "CREDIT_CARD"
    IBAN = "IBAN"

    # ─── English ───
    SSN = "SSN"
    PHONE = "PHONE"
    US_ZIP = "US_ZIP"

    # ─── Persian ───
    IR_NATIONAL_ID = "IR_NATIONAL_ID"
    IR_MOBILE = "IR_MOBILE"
    IR_POSTAL_CODE = "IR_POSTAL_CODE"
    IR_PASSPORT = "IR_PASSPORT"

    # ─── Turkish ───
    TR_TCKN = "TR_TCKN"
    TR_PHONE = "TR_PHONE"

    # ─── Arabic ───
    AR_NATIONAL_ID = "AR_NATIONAL_ID"
    AR_PHONE = "AR_PHONE"

    # ─── Chinese ───
    CN_ID_CARD = "CN_ID_CARD"
    CN_PHONE = "CN_PHONE"

    # ─── Russian ───
    RU_SNILS = "RU_SNILS"
    RU_INN = "RU_INN"
    RU_PASSPORT = "RU_PASSPORT"

    # ─── Spanish ───
    ES_DNI = "ES_DNI"
    ES_NIE = "ES_NIE"

    # ─── French ───
    FR_INSEE = "FR_INSEE"

    # ─── German ───
    DE_STEUER_ID = "DE_STEUER_ID"

    # ─── Portuguese ───
    PT_CPF = "PT_CPF"
    PT_CNPJ = "PT_CNPJ"

    # ─── Japanese ───
    JP_MY_NUMBER = "JP_MY_NUMBER"
    JP_PHONE = "JP_PHONE"

    # ─── Korean ───
    KR_RRN = "KR_RRN"
    KR_PHONE = "KR_PHONE"

    # ─── NER-based (any language) ───
    PERSON = "PERSON"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"


@dataclass
class PIIEntity:
    """A detected PII entity in text."""
    start: int
    end: int
    entity_type: PIIType
    text: str
    score: float = 1.0
    source: str = "unknown"

    def overlaps(self, other: "PIIEntity") -> bool:
        return not (self.end <= other.start or self.start >= other.end)

    def length(self) -> int:
        return self.end - self.start

    def __repr__(self) -> str:
        return (
            f"PIIEntity({self.entity_type.value}, "
            f"[{self.start}:{self.end}], {self.text!r})"
        )


@dataclass
class SanitizationResult:
    """Result of sanitizing a text."""
    sanitized_text: str
    mapping: dict[str, str] = field(default_factory=dict)
    entities: list[PIIEntity] = field(default_factory=list)
    by_type: dict[str, int] = field(default_factory=dict)
    detected_language: str = "unknown"

    @property
    def total(self) -> int:
        return len(self.entities)

    def __repr__(self) -> str:
        return (
            f"SanitizationResult(entities={self.total}, "
            f"lang={self.detected_language}, types={self.by_type})"
        )