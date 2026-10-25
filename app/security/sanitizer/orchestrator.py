"""
PII Sanitizer — Master Orchestrator.

Coordinates all detection layers:
  - Auto language detection
  - Universal layer
  - Language-specific layer
  - NER layer (for English)
"""
import uuid
import logging

from .models import PIIEntity, PIIType, SanitizationResult
from .language_detector import detect_language, SUPPORTED_LANGUAGES
from .ner_layer import NERLayer
from .layers import (
    UniversalLayer,
    EnglishLayer,
    PersianLayer,
    TurkishLayer,
    ChineseLayer,
    JapaneseLayer,
    KoreanLayer,
    ArabicLayer,
    SpanishLayer,
    FrenchLayer,
    GermanLayer,
    PortugueseLayer,
    RussianLayer,
)


logger = logging.getLogger(__name__)


LANGUAGE_LAYER_MAP = {
    "en": EnglishLayer,
    "fa": PersianLayer,
    "tr": TurkishLayer,
    "zh": ChineseLayer,
    "ja": JapaneseLayer,
    "ko": KoreanLayer,
    "ar": ArabicLayer,
    "es": SpanishLayer,
    "fr": FrenchLayer,
    "de": GermanLayer,
    "pt": PortugueseLayer,
    "ru": RussianLayer,
}


class PIISanitizer:
    """
    Main sanitizer.

    Layers:
      1. Universal (email, IP, card, etc.)
      2. Language-specific (per language)
      3. NER (only for English)
    """

    def __init__(
        self,
        min_score: float = 0.5,
        enable_auto_detect: bool = True,
        enable_ner: bool = True,
    ):
        self.universal_layer = UniversalLayer()
        self.ner_layer = NERLayer() if enable_ner else None
        self.min_score = min_score
        self.enable_auto_detect = enable_auto_detect
        self._layer_cache: dict[str, object] = {}

        if self.ner_layer and not self.ner_layer.is_available():
            logger.warning("NER Layer not available (spaCy model missing)")
            self.ner_layer = None

    # ═══════════════════════════════════════════════════════

    def sanitize(
        self,
        text: str,
        language: str | None = None,
        mode: str = "input",
    ) -> SanitizationResult:
        """
    Detect and replace all PII in text.

        Args:
            text: Input text
            language: Force specific language (None = auto-detect)
            mode: "input" (with NER) or "output" (regex only)

        Returns:
            SanitizationResult
        """
        if not text or not text.strip():
            return SanitizationResult(
                sanitized_text=text,
                detected_language="unknown",
            )

    # Detect language
        if language and language in SUPPORTED_LANGUAGES:
            detected_lang = language
        elif self.enable_auto_detect:
            detected_lang = detect_language(text)
        else:
            detected_lang = "en"

    # Collect entities
        entities: list[PIIEntity] = []

    # Layer 1: Universal
        try:
            entities.extend(self.universal_layer.detect(text))
        except Exception as e:
            logger.error(f"UniversalLayer error: {e}")

    # Layer 2: Language-specific
        layer = self._get_layer(detected_lang)
        if layer:
            try:
                entities.extend(layer.detect(text))
            except Exception as e:
                logger.error(f"{detected_lang} layer error: {e}")

    # ⭐ Layer 3: NER — ONLY in input mode
        if mode == "input" and self.ner_layer and detected_lang == "en":
            try:
                entities.extend(self.ner_layer.detect(text))
            except Exception as e:
                logger.error(f"NER layer error: {e}")

  
        # Filter by score
        entities = [e for e in entities if e.score >= self.min_score]

        if not entities:
            return SanitizationResult(
                sanitized_text=text,
                detected_language=detected_lang,
            )

        # Dedupe
        entities = self._dedupe(entities)

        # Replace
        sanitized = text
        mapping: dict[str, str] = {}
        by_type: dict[str, int] = {}

        entities_sorted = sorted(entities, key=lambda e: e.start, reverse=True)

        for entity in entities_sorted:
            original = text[entity.start:entity.end]
            token = self._make_token(entity.entity_type)

            mapping[token] = original
            by_type[entity.entity_type.value] = (
                by_type.get(entity.entity_type.value, 0) + 1
            )

            sanitized = (
                sanitized[:entity.start] + token + sanitized[entity.end:]
            )

            return SanitizationResult(
            sanitized_text=sanitized,
            mapping=mapping,
            entities=entities,
            by_type=by_type,
            detected_language=detected_lang,
        )

    def restore(self, text: str, mapping: dict[str, str]) -> str:
        if not mapping:
            return text
        for token, original in mapping.items():
            text = text.replace(token, original)
        return text

    def detect_language(self, text: str) -> str:
        return detect_language(text)

    # ═══════════════════════════════════════════════════════

    def _get_layer(self, language: str):
        if language not in self._layer_cache:
            layer_class = LANGUAGE_LAYER_MAP.get(language)
            if layer_class:
                self._layer_cache[language] = layer_class()
            else:
                return None
        return self._layer_cache.get(language)

    @staticmethod
    def _make_token(entity_type: PIIType) -> str:
        short_id = uuid.uuid4().hex[:8]
        return f"[[{entity_type.value}_{short_id}]]"

    @staticmethod
    def _dedupe(entities: list[PIIEntity]) -> list[PIIEntity]:
        if not entities:
            return []

        sorted_e = sorted(entities, key=lambda e: (-e.score, -e.length()))
        kept: list[PIIEntity] = []

        for entity in sorted_e:
            if any(entity.overlaps(k) for k in kept):
                continue
            kept.append(entity)

        return sorted(kept, key=lambda e: e.start)