"""
Output Filter — Master Orchestrator.

Coordinates:
  1. Secrets detection (API keys, tokens)
  2. PII detection (reuse Sanitizer)
  3. Entropy analysis (unknown secrets)

Decisions:
  - ALLOW:  safe
  - REDACT: partial redaction, response shown
  - BLOCK:  dangerous, response replaced
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .secrets_detector import SecretsDetector, SecretFinding
from .entropy_analyzer import EntropyAnalyzer, EntropyFinding

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Decision Types
# ═══════════════════════════════════════════════════════════

class OutputDecision(str, Enum):
    ALLOW = "allow"
    REDACT = "redact"
    BLOCK = "block"


@dataclass
class OutputVerdict:
    decision: OutputDecision
    reason: str
    safe_text: str
    secret_findings: list[SecretFinding] = field(default_factory=list)
    entropy_findings: list[EntropyFinding] = field(default_factory=list)
    pii_count: int = 0
    pii_by_type: dict = field(default_factory=dict)

    @property
    def is_safe(self) -> bool:
        return self.decision != OutputDecision.BLOCK


# ═══════════════════════════════════════════════════════════
# Output Filter
# ═══════════════════════════════════════════════════════════

class OutputFilter:
    """
    Multi-layer output filter.

    Layers:
      1. Secrets detector (known patterns)
      2. PII detector (via Sanitizer)
      3. Entropy analyzer (unknown secrets)
    """

    # Thresholds
    PII_BLOCK_COUNT = 5        # بیش از این تعداد PII → BLOCK
    PII_REDACT_COUNT = 1       # حداقل برای REDACT
    SECRET_SEVERITY_BLOCK = 0.95
    ENTROPY_SCORE_BLOCK = 0.80

    def __init__(self, sanitizer):
        """
        Args:
            sanitizer: PIISanitizer instance (from gام ۴)
        """
        self.sanitizer = sanitizer
        self.secrets_detector = SecretsDetector()
        self.entropy_analyzer = EntropyAnalyzer()

    # ═══════════════════════════════════════════════════════

    def check(self, text: str) -> OutputVerdict:
        """Filter LLM output."""
        if not text:
            return OutputVerdict(
                decision=OutputDecision.ALLOW,
                reason="",
                safe_text=text,
            )

        # ─── Layer 1: Secrets ───
        secret_findings = self.secrets_detector.detect(text)

        # Check for critical secrets
        critical_secrets = [
            f for f in secret_findings
            if f.severity >= self.SECRET_SEVERITY_BLOCK
        ]

        if critical_secrets:
            names = ", ".join(set(f.name for f in critical_secrets))
            logger.warning(f"Critical secrets detected: {names}")
            return OutputVerdict(
                decision=OutputDecision.BLOCK,
                reason=f"Critical secrets detected: {names}",
                safe_text="⚠️ Response blocked: it contained sensitive credentials.",
                secret_findings=secret_findings,
            )

        
        # ─── Layer 2: PII ───
        pii_result = self.sanitizer.sanitize(text, mode="output")

        # ─── Layer 3: Entropy ───
        entropy_findings = self.entropy_analyzer.analyze(text)

        # Critical entropy finding
        critical_entropy = [
            f for f in entropy_findings
            if f.score >= self.ENTROPY_SCORE_BLOCK
        ]

        # ─── Decision ───

        # Rule 1: Too many PII → BLOCK
        if pii_result.total >= self.PII_BLOCK_COUNT:
            return OutputVerdict(
                decision=OutputDecision.BLOCK,
                reason=f"Too many PII leaks: {pii_result.total}",
                safe_text="⚠️ Response blocked: it contained too much personal data.",
                secret_findings=secret_findings,
                entropy_findings=entropy_findings,
                pii_count=pii_result.total,
                pii_by_type=pii_result.by_type,
            )

        # Rule 2: Critical entropy → BLOCK
        if critical_entropy:
            return OutputVerdict(
                decision=OutputDecision.BLOCK,
                reason=f"High-entropy strings detected: {len(critical_entropy)}",
                safe_text="⚠️ Response blocked: it contained suspicious encoded data.",
                secret_findings=secret_findings,
                entropy_findings=entropy_findings,
                pii_count=pii_result.total,
                pii_by_type=pii_result.by_type,
            )

        # Rule 3: Some PII or non-critical secrets → REDACT
        if pii_result.total >= self.PII_REDACT_COUNT or secret_findings or entropy_findings:
            redacted = self._redact(
                text,
                pii_result.sanitized_text,
                secret_findings,
                entropy_findings,
            )

            reasons = []
            if pii_result.total > 0:
                reasons.append(f"{pii_result.total} PII")
            if secret_findings:
                reasons.append(f"{len(secret_findings)} secrets")
            if entropy_findings:
                reasons.append(f"{len(entropy_findings)} high-entropy")

            return OutputVerdict(
                decision=OutputDecision.REDACT,
                reason=f"Redacted: {', '.join(reasons)}",
                safe_text=redacted,
                secret_findings=secret_findings,
                entropy_findings=entropy_findings,
                pii_count=pii_result.total,
                pii_by_type=pii_result.by_type,
            )

        # ALLOW
        return OutputVerdict(
            decision=OutputDecision.ALLOW,
            reason="",
            safe_text=text,
            secret_findings=secret_findings,
            entropy_findings=entropy_findings,
            pii_count=pii_result.total,
            pii_by_type=pii_result.by_type,
        )

    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _redact(
        original: str,
        sanitized: str,
        secret_findings: list[SecretFinding],
        entropy_findings: list[EntropyFinding],
    ) -> str:
        """Apply redactions from all layers."""
        result = sanitized  # already redacted PII

        # Note: after sanitizer redaction, offsets change
        # So we redact secrets/entropy on the sanitized text
        # by finding their text patterns

        # Redact secrets
        for f in secret_findings:
            result = result.replace(f.matched_text, f.replacement, 1)

        # Redact entropy (only exact matches to avoid false positives)
        for f in entropy_findings:
            if f.text in result:
                result = result.replace(f.text, "[REDACTED_HIGH_ENTROPY]", 1)

        return result