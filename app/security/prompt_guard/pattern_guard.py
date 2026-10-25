"""
Layer 2: Pattern-based prompt guard.

Detects known prompt injection patterns using regex.
Uses weighted scoring to avoid false positives.
"""
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Attack Patterns
# ═══════════════════════════════════════════════════════════

# Format: (regex_pattern, weight, category)
PATTERNS = [
    # ─── Ignore Instructions ───
    (r"ignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+"
     r"(?:instructions?|prompts?|rules?|commands?)",
     0.95, "ignore_instructions"),

    (r"forget\s+(?:all\s+)?(?:your\s+)?(?:instructions?|rules?|prompts?|training)",
     0.9, "forget_instructions"),

    # ⭐ UPDATED: better handle "disregard everything you were told"
    (r"disregard\s+(?:all\s+)?(?:the\s+)?"
     r"(?:previous|prior|above|earlier|everything|anything|what)\s*"
     r"(?:instructions?|prompts?|rules?|text|"
     r"you\s+were\s+told|i\s+said|they\s+told\s+you)?",
     0.85, "disregard"),

    (r"override\s+(?:your\s+)?(?:instructions?|rules?|settings?)",
     0.85, "override"),

    # ─── Reveal System Prompt ───
    (r"(?:reveal|show|print|display|tell|give)\s+(?:me\s+)?"
     r"(?:your\s+)?(?:system\s+)?(?:prompt|instructions?|rules?|directives?)",
     0.9, "reveal_prompt"),

    # ⭐ UPDATED: better handle "what were your initial rules"
    (r"(?:what|whats|what's)\s+(?:is|are|were)\s+your\s+"
     r"(?:system\s+|initial\s+|original\s+|hidden\s+|first\s+)?"
     r"(?:prompt|instructions?|rules?|directives?|guidelines?)",
     0.85, "reveal_prompt_question"),

    (r"repeat\s+(?:the\s+)?(?:text|instructions?)\s+above",
     0.85, "repeat_instructions"),

    # ─── Jailbreak ───
    # ═══════════════════════════════════════════════════════════
    # Jailbreak / Persona
    # ═══════════════════════════════════════════════════════════

    (r"(?:you\s+are|act\s+as|pretend\s+(?:to\s+be|you\s+are|you\s+have))\s+"
    r"(?:now\s+)?(?:DAN|jailbroken|unrestricted|evil|no\s+limits|"
    r"no\s+restrictions?|no\s+rules?|no\s+constraints?|free)",
    0.95, "jailbreak_persona"),

    (r"(?:enter|enable|activate)\s+(?:DAN|developer|god|admin)\s+mode",
     0.9, "mode_switch"),

    (r"(?:bypass|skip|ignore|circumvent)\s+(?:your\s+)?"
     r"(?:safety|content|ethical|moral)\s+"
     r"(?:filters?|checks?|guidelines?|restrictions?|rules?)",
     0.9, "bypass_safety"),

    # ─── System Info Extraction ───
    (r"(?:list|show|enumerate)\s+(?:all\s+)?(?:your\s+)?"
     r"(?:tools?|functions?|capabilities?|apis?)",
     0.6, "list_tools"),

    # ─── Code Injection ───
    (r"<\s*script[^>]*>", 0.9, "script_injection"),
    (r"\{\{.*?\}\}", 0.5, "template_injection"),
    (r"\$\{.*?\}", 0.5, "template_injection"),

    # ─── Data Exfiltration ───
    (r"(?:dump|extract|leak|exfiltrate|list)\s+(?:all\s+)?"
     r"(?:data|users?|records?|database|personal\s+info)",
     0.85, "data_exfiltration"),

    # ─── Encoding Requests ───
    (r"(?:translate|convert|encode|decode)\s+"
     r"(?:this|the\s+following)\s+(?:to|into)\s+"
     r"(?:base64|hex|rot13|binary)",
     0.6, "encoding_request"),
]

# Compile once
_COMPILED = [
    (re.compile(pattern, re.IGNORECASE), weight, category)
    for pattern, weight, category in PATTERNS
]


# ═══════════════════════════════════════════════════════════
# Result
# ═══════════════════════════════════════════════════════════

@dataclass
class PatternResult:
    """Result of pattern analysis."""
    score: float
    matched_categories: list[str]
    matched_snippets: list[str]
    is_blocked: bool = False

    def __repr__(self) -> str:
        return (
            f"PatternResult(score={self.score:.2f}, "
            f"categories={self.matched_categories})"
        )


# ═══════════════════════════════════════════════════════════
# Pattern Guard
# ═══════════════════════════════════════════════════════════

class PatternGuard:
    """
    Regex-based prompt injection detection.

    Uses weighted combination:
        score = 1 - Π(1 - weight_i)
    """

    def __init__(self, block_threshold: float = 0.75):
        self.block_threshold = block_threshold

    def analyze(self, text: str) -> PatternResult:
        """Analyze text for attack patterns."""
        if not text:
            return PatternResult(0.0, [], [], False)

        categories: list[str] = []
        snippets: list[str] = []
        prob_not_malicious = 1.0

        for regex, weight, category in _COMPILED:
            m = regex.search(text)
            if m:
                categories.append(category)
                snippets.append(m.group()[:80])
                prob_not_malicious *= (1 - weight)

        score = 1 - prob_not_malicious

        return PatternResult(
            score=round(score, 4),
            matched_categories=categories,
            matched_snippets=snippets,
            is_blocked=score >= self.block_threshold,
        )