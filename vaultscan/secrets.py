"""Secret scanning for source trees.

Two detectors run on every line: the named patterns in patterns.py, and a
Shannon-entropy check that catches random-looking strings assigned to
suspicious variable names when no named pattern applies.
"""

from __future__ import annotations

import fnmatch
import math
import os
import re
from typing import Callable, Iterable, List, Optional

from vaultscan.models import Finding, Severity
from vaultscan.patterns import SECRET_RULES, looks_like_placeholder

SCANNED_EXTENSIONS = (
    ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml", ".tf", ".tfvars",
    ".env", ".sh", ".php", ".java", ".go", ".rb", ".properties", ".ini", ".cfg",
    ".conf", ".toml", ".xml", ".txt",
)
SCANNED_FILENAMES = (".env", "dockerfile", "jenkinsfile", ".npmrc", ".pypirc")
ALWAYS_SKIPPED_DIRS = {".git", "node_modules", ".terraform", "__pycache__", ".venv", "venv"}
MAX_FILE_BYTES = 1_000_000

IGNORE_FILE = ".vaultscanignore"
INLINE_IGNORE = "vaultscan:ignore"

ENTROPY_THRESHOLD = 4.2
_ASSIGNMENT = re.compile(
    r"(?i)\b([a-z0-9_.-]*(?:secret|token|passw(?:or)?d|api[_-]?key|credential|private[_-]?key)[a-z0-9_.-]*)"
    r"[\"']?\s*[:=]\s*[\"']([^\"'\s]{20,})[\"']"
)


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {char: value.count(char) for char in set(value)}
    return -sum((n / len(value)) * math.log2(n / len(value)) for n in counts.values())


def redact(secret: str) -> str:
    """Show enough to locate the secret without reproducing it in logs."""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}{'*' * 8}{secret[-2:]}"


def load_ignore_patterns(base_path: str) -> List[str]:
    ignore_file = os.path.join(base_path, IGNORE_FILE)
    if not os.path.isfile(ignore_file):
        return []
    with open(ignore_file, "r", encoding="utf-8-sig") as handle:
        lines = (line.strip() for line in handle)
        return [line for line in lines if line and not line.startswith("#")]


def is_ignored(rel_path: str, patterns: Iterable[str]) -> bool:
    """Gitignore-style matching: 'dir/' for folders, globs for files."""
    path = rel_path.replace("\\", "/")
    parts = path.split("/")
    for pattern in patterns:
        if pattern.endswith("/"):
            if pattern.rstrip("/") in parts[:-1]:
                return True
        elif fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(parts[-1], pattern):
            return True
    return False


def should_scan(filename: str) -> bool:
    lowered = filename.lower()
    return lowered.endswith(SCANNED_EXTENSIONS) or lowered in SCANNED_FILENAMES or lowered.startswith(".env")


def scan_line(line: str, rel_path: str, line_no: int) -> List[Finding]:
    if INLINE_IGNORE in line:
        return []
    findings: List[Finding] = []
    seen = set()
    for rule in SECRET_RULES:
        for match in rule.pattern.finditer(line):
            value = match.group(1)
            if value in seen or looks_like_placeholder(value):
                continue
            seen.add(value)
            findings.append(Finding(
                rule_id=rule.rule_id, title=rule.title, severity=rule.severity,
                source="secrets", file=rel_path, line=line_no,
                detail=f"Matched value {redact(value)}",
                remediation="Revoke and rotate this credential, then load it from a secret manager or CI secret.",
            ))
    for match in _ASSIGNMENT.finditer(line):
        name, value = match.group(1), match.group(2)
        if value in seen or looks_like_placeholder(value):
            continue
        entropy = shannon_entropy(value)
        if entropy >= ENTROPY_THRESHOLD:
            seen.add(value)
            findings.append(Finding(
                rule_id="SEC-100", title="High-entropy value assigned to a secret-like name",
                severity=Severity.MEDIUM, source="secrets", file=rel_path, line=line_no,
                detail=f"{name} = {redact(value)} (entropy {entropy:.1f})",
                remediation="If this is a real credential, rotate it and move it out of the repository.",
            ))
    return findings


def scan_file(path: str, rel_path: str) -> List[Finding]:
    findings: List[Finding] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line_no, line in enumerate(handle, start=1):
            findings.extend(scan_line(line, rel_path, line_no))
    return findings


def scan_path(base_path: str, log: Optional[Callable[[str], None]] = None) -> List[Finding]:
    """Scan a directory tree (or a single file) for secrets."""
    log = log or (lambda message: None)
    if os.path.isfile(base_path):
        return scan_file(base_path, os.path.basename(base_path))

    patterns = load_ignore_patterns(base_path)
    findings: List[Finding] = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = sorted(d for d in dirs if d not in ALWAYS_SKIPPED_DIRS)
        for name in sorted(files):
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, base_path)
            if is_ignored(rel_path, patterns):
                log(f"skipped (ignored): {rel_path}")
                continue
            if not should_scan(name):
                continue
            try:
                if os.path.getsize(full_path) > MAX_FILE_BYTES:
                    log(f"skipped (too large): {rel_path}")
                    continue
                log(f"scanning: {rel_path}")
                findings.extend(scan_file(full_path, rel_path))
            except OSError as exc:
                log(f"could not read {rel_path}: {exc}")
    return findings
