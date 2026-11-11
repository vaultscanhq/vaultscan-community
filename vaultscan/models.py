"""Shared data types: findings, severities and the gate verdict."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Optional


class Severity(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def parse(cls, value: str) -> "Severity":
        try:
            return cls[value.strip().upper()]
        except KeyError as exc:
            raise ValueError(f"unknown severity: {value!r}") from exc


class Verdict(IntEnum):
    """Ordered so that the strictest verdict always wins with max()."""

    ALLOW = 0
    WARN = 1
    ASK_HUMAN = 2
    BLOCK = 3

    @property
    def label(self) -> str:
        return self.name.replace("_", " ")


@dataclass
class Finding:
    rule_id: str
    title: str
    severity: Severity
    source: str  # secrets | terraform | kubernetes | workflow
    file: str = ""
    line: int = 0
    resource: str = ""
    detail: str = ""
    remediation: str = ""
    # Destructive or privilege-changing actions that a person should sign off
    # on even when nothing is technically misconfigured.
    needs_approval: bool = False
    explanation: Optional[str] = None  # filled in by the AI explainer
    extra: dict = field(default_factory=dict)

    @property
    def location(self) -> str:
        if self.resource:
            # A job path or a Deployment name is ambiguous without its file.
            if self.file and self.source in ("workflow", "kubernetes"):
                return f"{self.file} ({self.resource})"
            return self.resource
        if self.file and self.line:
            return f"{self.file}:{self.line}"
        return self.file

    def to_dict(self) -> dict:
        data = asdict(self)
        data["severity"] = self.severity.name
        return data
