"""
Layer 1: Secrets detection in LLM output.

Detects API keys, tokens, private keys, and other credentials
that might have been leaked by the LLM.
"""
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Known Secret Patterns
# ═══════════════════════════════════════════════════════════

# Format: (regex, name, severity, replacement)
SECRET_PATTERNS = [
    # ═══ OpenAI ═══
    (r"sk-[a-zA-Z0-9]{20,}",
     "openai_key", 0.98, "[REDACTED_OPENAI_KEY]"),
    (r"sk-proj-[a-zA-Z0-9_\-]{20,}",
     "openai_project_key", 0.98, "[REDACTED_OPENAI_KEY]"),

    # ═══ Anthropic ═══
    (r"sk-ant-[a-zA-Z0-9_\-]{20,}",
     "anthropic_key", 0.98, "[REDACTED_ANTHROPIC_KEY]"),

    # ═══ AWS ═══
    (r"AKIA[0-9A-Z]{16}",
     "aws_access_key", 0.98, "[REDACTED_AWS_KEY]"),
    (r"ASIA[0-9A-Z]{16}",
     "aws_temp_key", 0.95, "[REDACTED_AWS_KEY]"),

    # ═══ Google ═══
    (r"AIza[0-9A-Za-z_\-]{35}",
     "google_api_key", 0.98, "[REDACTED_GOOGLE_KEY]"),

    # ═══ GitHub ═══
    (r"ghp_[a-zA-Z0-9]{36}",
     "github_pat", 0.98, "[REDACTED_GITHUB_TOKEN]"),
    (r"gho_[a-zA-Z0-9]{36}",
     "github_oauth", 0.98, "[REDACTED_GITHUB_TOKEN]"),
    (r"ghu_[a-zA-Z0-9]{36}",
     "github_user_token", 0.98, "[REDACTED_GITHUB_TOKEN]"),
    (r"ghs_[a-zA-Z0-9]{36}",
     "github_server_token", 0.98, "[REDACTED_GITHUB_TOKEN]"),
    (r"ghr_[a-zA-Z0-9]{36}",
     "github_refresh", 0.98, "[REDACTED_GITHUB_TOKEN]"),

    # ═══ GitLab ═══
    (r"glpat-[a-zA-Z0-9_\-]{20}",
     "gitlab_pat", 0.98, "[REDACTED_GITLAB_TOKEN]"),

    # ═══ Stripe ═══
    (r"sk_live_[a-zA-Z0-9]{24,}",
     "stripe_live", 0.98, "[REDACTED_STRIPE_KEY]"),
    (r"sk_test_[a-zA-Z0-9]{24,}",
     "stripe_test", 0.9, "[REDACTED_STRIPE_KEY]"),
    (r"pk_live_[a-zA-Z0-9]{24,}",
     "stripe_publishable", 0.7, "[REDACTED_STRIPE_KEY]"),

    # ═══ Slack ═══
    (r"xox[baprs]-[a-zA-Z0-9\-]+",
     "slack_token", 0.95, "[REDACTED_SLACK_TOKEN]"),

    # ═══ Discord ═══
    (r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}",
     "discord_token", 0.95, "[REDACTED_DISCORD_TOKEN]"),

    # ═══ Telegram Bot ═══
    (r"\d{8,10}:[A-Za-z0-9_\-]{35}",
     "telegram_bot_token", 0.9, "[REDACTED_TELEGRAM_TOKEN]"),

    # ═══ Twilio ═══
    (r"SK[0-9a-fA-F]{32}",
     "twilio_key", 0.9, "[REDACTED_TWILIO_KEY]"),

    # ═══ SendGrid ═══
    (r"SG\.[a-zA-Z0-9_\-]{22}\.[a-zA-Z0-9_\-]{43}",
     "sendgrid_key", 0.95, "[REDACTED_SENDGRID_KEY]"),

    # ═══ Mailgun ═══
    (r"key-[0-9a-zA-Z]{32}",
     "mailgun_key", 0.85, "[REDACTED_MAILGUN_KEY]"),

    # ═══ Private Keys ═══
    (r"-----BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY-----[\s\S]+?"
     r"-----END \1 PRIVATE KEY-----",
     "private_key", 0.99, "[REDACTED_PRIVATE_KEY]"),

    # ═══ JWT ═══
    (r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",
     "jwt", 0.85, "[REDACTED_JWT]"),

    # ═══ Bearer Token ═══
    (r"Bearer\s+[A-Za-z0-9_\-\.]{30,}",
     "bearer_token", 0.85, "[REDACTED_BEARER_TOKEN]"),

    # ═══ Basic Auth ═══
    (r"Basic\s+[A-Za-z0-9+/=]{20,}",
     "basic_auth", 0.85, "[REDACTED_BASIC_AUTH]"),
]


_COMPILED_SECRETS = [
    (re.compile(pattern), name, severity, replacement)
    for pattern, name, severity, replacement in SECRET_PATTERNS
]


# ═══════════════════════════════════════════════════════════
# Result
# ═══════════════════════════════════════════════════════════

@dataclass
class SecretFinding:
    name: str
    matched_text: str
    start: int
    end: int
    severity: float
    replacement: str


# ═══════════════════════════════════════════════════════════
# Detector
# ═══════════════════════════════════════════════════════════

class SecretsDetector:
    """Detect secrets in LLM output."""

    def detect(self, text: str) -> list[SecretFinding]:
        if not text:
            return []

        findings: list[SecretFinding] = []

        for regex, name, severity, replacement in _COMPILED_SECRETS:
            for m in regex.finditer(text):
                findings.append(SecretFinding(
                    name=name,
                    matched_text=m.group()[:50],  # truncate for logging
                    start=m.start(),
                    end=m.end(),
                    severity=severity,
                    replacement=replacement,
                ))

        return findings

    def has_critical(self, findings: list[SecretFinding]) -> bool:
        """Check if any finding is critical (severity >= 0.9)."""
        return any(f.severity >= 0.9 for f in findings)

    @staticmethod
    def redact(text: str, findings: list[SecretFinding]) -> str:
        """Replace secrets with placeholders."""
        if not findings:
            return text

        # Sort by start descending to replace from right
        sorted_f = sorted(findings, key=lambda f: f.start, reverse=True)

        result = text
        for f in sorted_f:
            result = result[:f.start] + f.replacement + result[f.end:]

        return result