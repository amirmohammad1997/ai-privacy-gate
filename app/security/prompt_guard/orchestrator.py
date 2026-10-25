"""
Prompt Guard — Master Orchestrator.

Coordinates:
  1. Normalization
  2. Pattern analysis (regex)
  3. Embedding analysis (semantic similarity)
  4. Smart decision using multi-threshold logic
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .normalizer import normalize
from .pattern_guard import PatternGuard, PatternResult
from .embedding_guard import EmbeddingGuard, EmbeddingResult

logger = logging.getLogger(__name__)


class Decision(str, Enum):
    ALLOW = "allow"
    FLAG = "flag"
    BLOCK = "block"


@dataclass
class PromptVerdict:
    decision: Decision
    score: float
    reason: str
    normalized_text: str
    flags: list[str] = field(default_factory=list)
    pattern_result: Optional[PatternResult] = None
    embedding_result: Optional[EmbeddingResult] = None

    @property
    def is_safe(self) -> bool:
        return self.decision != Decision.BLOCK


class PromptGuard:
    """
    Multi-layer prompt guard with smart combination.

    Decision logic:
      1. Pattern strong (>=0.72) → BLOCK
      2. Embedding strong (>=0.65) → BLOCK
      3. Combined moderate (>=0.5) → FLAG
      4. Otherwise → ALLOW
    """

    PATTERN_BLOCK = 0.72
    PATTERN_FLAG = 0.40

    # Embedding: بازگشت به آستانه‌ی بالا
    EMBEDDING_BLOCK = 0.75   # ← فقط برای سیگنال‌های بسیار قوی
    EMBEDDING_FLAG = 0.60    # ← برای موارد مشکوک

    COMBINED_BLOCK = 0.55
    COMBINED_FLAG = 0.40

    # Weights for combination
    PATTERN_WEIGHT = 0.5
    EMBEDDING_WEIGHT = 0.5

    def __init__(
        self,
        max_length: int = 15000,
        enable_embedding: bool = True,
    ):
        self.pattern_guard = PatternGuard(block_threshold=self.PATTERN_BLOCK)
        self.max_length = max_length

        self.embedding_guard: Optional[EmbeddingGuard] = None
        if enable_embedding:
            try:
                self.embedding_guard = EmbeddingGuard(
                    block_threshold=self.EMBEDDING_BLOCK,
                )
            except Exception as e:
                logger.warning(f"Embedding Guard init failed: {e}")

    # ═══════════════════════════════════════════════════════

    def check(self, text: str) -> PromptVerdict:
        """Analyze prompt and return verdict."""
        if not text or not text.strip():
            return PromptVerdict(
                decision=Decision.BLOCK,
                score=1.0,
                reason="Empty input",
                normalized_text="",
            )

        if len(text) > self.max_length:
            return PromptVerdict(
                decision=Decision.BLOCK,
                score=1.0,
                reason=f"Input exceeds {self.max_length} characters",
                normalized_text=text[:100] + "...",
            )

        # ─── Normalize ───
        norm = normalize(text, aggressive=True)
        normalized = norm["normalized"]
        flags = list(norm["flags"])
        extras = norm["decoded_extras"]

        # ─── Pattern analysis ───
        pattern_result = self.pattern_guard.analyze(normalized)
        for extra in extras:
            r = self.pattern_guard.analyze(extra)
            if r.score > pattern_result.score:
                pattern_result = r

        # ─── Embedding analysis ───
        embedding_result = None
        if self.embedding_guard:
            embedding_result = self.embedding_guard.analyze(normalized)
            for extra in extras:
                r = self.embedding_guard.analyze(extra)
                if r.score > embedding_result.score:
                    embedding_result = r

        # ─── SMART DECISION ───

        p_score = pattern_result.score
        e_score = embedding_result.score if embedding_result else 0.0

        # ════ Rule 1: Pattern strong → BLOCK ════
        if p_score >= self.PATTERN_BLOCK:
            return PromptVerdict(
                decision=Decision.BLOCK,
                score=p_score,
                reason=self._build_reason(pattern_result, embedding_result, "pattern"),
                normalized_text=normalized,
                flags=flags,
                pattern_result=pattern_result,
                embedding_result=embedding_result,
            )

        # ════ Rule 2: Embedding strong → BLOCK ════
        if e_score >= self.EMBEDDING_BLOCK:
            return PromptVerdict(
                decision=Decision.BLOCK,
                score=e_score,
                reason=self._build_reason(pattern_result, embedding_result, "embedding"),
                normalized_text=normalized,
                flags=flags + ["embedding_strong"],
                pattern_result=pattern_result,
                embedding_result=embedding_result,
            )

        # ════ Rule 3: Combined check ════
        combined = (
            p_score * self.PATTERN_WEIGHT
            + e_score * self.EMBEDDING_WEIGHT
        )

        if combined >= self.COMBINED_BLOCK:
            return PromptVerdict(
                decision=Decision.BLOCK,
                score=combined,
                reason=self._build_reason(pattern_result, embedding_result, "combined"),
                normalized_text=normalized,
                flags=flags + ["combined_strong"],
                pattern_result=pattern_result,
                embedding_result=embedding_result,
            )

        # ════ Rule 4: Pattern flag ════
        if p_score >= self.PATTERN_FLAG:
            return PromptVerdict(
                decision=Decision.FLAG,
                score=p_score,
                reason="Pattern suspicious",
                normalized_text=normalized,
                flags=flags,
                pattern_result=pattern_result,
                embedding_result=embedding_result,
            )

        # ════ Rule 5: Embedding flag ════
        if e_score >= self.EMBEDDING_FLAG:
            return PromptVerdict(
                decision=Decision.FLAG,
                score=e_score,
                reason="Semantic similarity to attack patterns",
                normalized_text=normalized,
                flags=flags + ["embedding_flag"],
                pattern_result=pattern_result,
                embedding_result=embedding_result,
            )

        # ════ Rule 6: Combined flag ════
        if combined >= self.COMBINED_FLAG:
            return PromptVerdict(
                decision=Decision.FLAG,
                score=combined,
                reason="Combined suspicious",
                normalized_text=normalized,
                flags=flags + ["combined_flag"],
                pattern_result=pattern_result,
                embedding_result=embedding_result,
            )

        # ════ ALLOW ════
        return PromptVerdict(
            decision=Decision.ALLOW,
            score=max(p_score, e_score),
            reason="",
            normalized_text=normalized,
            flags=flags,
            pattern_result=pattern_result,
            embedding_result=embedding_result,
        )

    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _build_reason(
        pattern_result: PatternResult,
        embedding_result: Optional[EmbeddingResult],
        source: str,
    ) -> str:
        parts = [f"[{source}]"]
        if pattern_result.matched_categories:
            cats = ", ".join(pattern_result.matched_categories[:3])
            parts.append(f"Patterns: {cats}")
        if embedding_result and embedding_result.best_category:
            parts.append(
                f"Semantic: {embedding_result.best_category} "
                f"({embedding_result.best_similarity:.2f})"
            )
        return " | ".join(parts)