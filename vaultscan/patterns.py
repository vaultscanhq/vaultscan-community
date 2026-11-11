"""Secret detection rules.

Each rule has a stable id so it can be ignored or re-rated from the policy
file. Patterns with a capture group report only the captured value, which
keeps the surrounding variable name out of the redacted snippet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Pattern

from vaultscan.models import Severity


@dataclass(frozen=True)
class SecretRule:
    rule_id: str
    title: str
    severity: Severity
    pattern: Pattern[str]


def _rule(rule_id: str, title: str, severity: Severity, regex: str) -> SecretRule:
    return SecretRule(rule_id, title, severity, re.compile(regex))


SECRET_RULES: List[SecretRule] = [
    _rule("SEC-001", "AWS access key ID", Severity.CRITICAL, r"\b((?:AKIA|ASIA)[0-9A-Z]{16})\b"),
    _rule("SEC-002", "AWS secret access key", Severity.CRITICAL,
          r"(?i)aws_secret_access_key[\"'\s:=]+([0-9a-zA-Z/+]{40})\b"),
    _rule("SEC-003", "GitHub token", Severity.CRITICAL,
          r"\b((?:ghp|gho|ghu|ghs|ghr)_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{50,})\b"),
    _rule("SEC-004", "Slack token", Severity.HIGH, r"\b(xox[baprs]-[0-9a-zA-Z-]{10,72})\b"),
    _rule("SEC-005", "Stripe live secret key", Severity.CRITICAL, r"\b(sk_live_[0-9a-zA-Z]{24,})\b"),
    _rule("SEC-006", "Google API key", Severity.HIGH, r"\b(AIza[0-9A-Za-z_-]{35})(?![0-9A-Za-z_-])"),
    _rule("SEC-007", "Azure key or token", Severity.HIGH,
          r"(?i)azure\w*(?:key|token|secret)[\"'\s:=]+([a-z0-9+/=]{32,})"),
    _rule("SEC-008", "JSON Web Token", Severity.MEDIUM,
          r"\b(eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,})\b"),
    _rule("SEC-009", "Database connection string with password", Severity.HIGH,
          r"(?i)\b((?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:@/]+:[^\s@/]+@[^\s/:]+)"),
    _rule("SEC-010", "Credentials embedded in URL", Severity.HIGH,
          r"\b(https?://[^\s:@/]+:[^\s@/]+@[^\s/]+)"),
    _rule("SEC-011", "Twilio auth token", Severity.HIGH,
          r"(?i)twilio\w*(?:token|auth)[\"'\s:=]+([a-f0-9]{32})\b"),
    _rule("SEC-012", "Private key", Severity.CRITICAL,
          r"(-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----)"),
    _rule("SEC-013", "Hard-coded API key or secret", Severity.MEDIUM,
          r"(?i)\b(?:api[_-]?key|secret|token|passwd|password)\b[\"']?\s*[:=]\s*[\"']([0-9a-zA-Z_\-+/=]{16,})[\"']"),
]

# Placeholder values that show up in docs and example configs. Matching these
# only trains people to ignore the scanner.
PLACEHOLDER_HINTS = ("example", "changeme", "your_", "your-", "xxxx", "placeholder", "dummy", "<", "${", "{{")


def looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    if any(hint in lowered for hint in PLACEHOLDER_HINTS):
        return True
    return len(set(value)) <= 3  # e.g. "aaaaaaaaaaaaaaaa"
