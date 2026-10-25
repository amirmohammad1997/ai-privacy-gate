"""
NER Layer — Named Entity Recognition via spaCy.

Detects persons, locations, organizations in English text.
Only runs when detected language is English.
"""
import logging

from .models import PIIEntity, PIIType

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# spaCy → PIIType mapping
# ═══════════════════════════════════════════════════════════

SPACY_LABEL_MAP = {
    "PERSON": PIIType.PERSON,
    "PER": PIIType.PERSON,
    "GPE": PIIType.LOCATION,
    "LOC": PIIType.LOCATION,
    "LOCATION": PIIType.LOCATION,
    "ORG": PIIType.ORGANIZATION,
    "ORGANIZATION": PIIType.ORGANIZATION,
    "FAC": PIIType.LOCATION,
    "NORP": PIIType.ORGANIZATION,
    "EVENT": PIIType.ORGANIZATION,
}


# Labels we don't want to redact (too common)
IGNORED_LABELS = {
    "DATE", "TIME", "MONEY", "PERCENT",
    "CARDINAL", "ORDINAL", "QUANTITY",
    "LANGUAGE", "LAW", "PRODUCT",
    "WORK_OF_ART",
}


# ═══════════════════════════════════════════════════════════
# NER Layer
# ═══════════════════════════════════════════════════════════

class NERLayer:
    """
    Named Entity Recognition via spaCy.

    Only for English. For other languages, use language-specific layers.
    """

    def __init__(self, min_length: int = 2):
        self.min_length = min_length
        self._nlp = None
        self._load()

    def _load(self):
        """Load spaCy model."""
        try:
            import spacy
            self._nlp = spacy.load(
                "en_core_web_sm",
                disable=["parser", "lemmatizer", "textcat"],
            )
            logger.info("spaCy NER model loaded")
        except OSError:
            logger.warning(
                "spaCy model 'en_core_web_sm' not found. "
                "Install: python -m spacy download en_core_web_sm"
            )
        except Exception as e:
            logger.error(f"spaCy load error: {e}")

    # ═══════════════════════════════════════════════════════

    def is_available(self) -> bool:
        """Check if NER is ready."""
        return self._nlp is not None

    def detect(self, text: str) -> list[PIIEntity]:
        """Detect named entities in text."""
        if not self._nlp or not text:
            return []

        entities: list[PIIEntity] = []

        try:
            doc = self._nlp(text)

            for ent in doc.ents:
                # Skip ignored labels
                if ent.label_ in IGNORED_LABELS:
                    continue

                # Map to our PIIType
                pii_type = SPACY_LABEL_MAP.get(ent.label_)
                if not pii_type:
                    continue

                # Filter very short entities
                if len(ent.text) < self.min_length:
                    continue

                # Filter entities that are only digits
                if ent.text.strip().isdigit():
                    continue

                entities.append(PIIEntity(
                    start=ent.start_char,
                    end=ent.end_char,
                    entity_type=pii_type,
                    text=ent.text,
                    score=0.75,  # NER is heuristic — lower than regex
                    source=f"ner-spacy-{ent.label_.lower()}",
                ))

        except Exception as e:
            logger.error(f"NER detection error: {e}")

        return entities