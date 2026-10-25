"""
Layer 3: Entropy analysis.

Detects unknown secrets by high entropy (randomness).
Useful for keys that don't match known patterns.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

MIN_LENGTH = 20
MAX_LENGTH = 200
ENTROPY_THRESHOLD = 4.2  # bits per character


# Whitelist prefixes (don't flag these)
WHITELIST_PREFIXES = (
    "[[",           # our own tokens
    "http://",
    "https://",
    "www.",
    "mailto:",
)


# ═══════════════════════════════════════════════════════════
# Shannon Entropy
# ═══════════════════════════════════════════════════════════

def shannon_entropy(s: str) -> float:
    """Compute Shannon entropy (bits per character)."""
    if not s:
        return 0.0

    counter = Counter(s)
    length = len(s)
    entropy = 0.0

    for count in counter.values():
        p = count / length
        entropy -= p * math.log2(p)

    return entropy


# ═══════════════════════════════════════════════════════════
# Result
# ═══════════════════════════════════════════════════════════

@dataclass
class EntropyFinding:
    text: str
    start: int
    end: int
    entropy: float
    score: float


# ═══════════════════════════════════════════════════════════
# Analyzer
# ═══════════════════════════════════════════════════════════

class EntropyAnalyzer:
    """Detect high-entropy strings in text."""

    # Candidate pattern: alphanumeric with some symbols
    CANDIDATE_PATTERN = re.compile(r"[A-Za-z0-9_\-\.+/=]{20,200}")

    def analyze(self, text: str) -> list[EntropyFinding]:
        if not text:
            return []

        findings: list[EntropyFinding] = []

        for m in self.CANDIDATE_PATTERN.finditer(text):
            candidate = m.group()

            # Whitelist
            if candidate.lower().startswith(WHITELIST_PREFIXES):
                continue

            # Must have mix of letters and digits (or symbols)
            has_letter = any(c.isalpha() for c in candidate)
            has_digit = any(c.isdigit() for c in candidate)

            if not (has_letter and has_digit):
                continue

            # Length check
            if not (MIN_LENGTH <= len(candidate) <= MAX_LENGTH):
                continue

            # Entropy check
            entropy = shannon_entropy(candidate)

            if entropy >= ENTROPY_THRESHOLD:
                # Score normalized: 0.6 to 0.85
                score = min(0.85, 0.6 + (entropy - ENTROPY_THRESHOLD) * 0.15)

                findings.append(EntropyFinding(
                    text=candidate,
                    start=m.start(),
                    end=m.end(),
                    entropy=round(entropy, 2),
                    score=round(score, 3),
                ))

        return findings