"""Plain-language summary that needs no model, used as the default and as the fallback."""

from __future__ import annotations

from collections import Counter

from vaultscan.engine import Decision
from vaultscan.models import Verdict

_SOURCE_NAMES = {
    "secrets": "leaked credentials", "terraform": "the Terraform plan", "kubernetes": "Kubernetes manifests",
    "workflow": "CI workflows", "command": "the proposed command",
}


def offline_summary(decision: Decision) -> str:
    if not decision.findings:
        return "No risky changes were detected."
    by_severity = Counter(f.severity.name.lower() for f in decision.findings)
    counts = ", ".join(f"{n} {name}" for name, n in by_severity.most_common())
    areas = sorted({_SOURCE_NAMES.get(f.source, f.source) for f in decision.findings})
    text = f"{len(decision.findings)} finding(s) ({counts}) in {', '.join(areas)}."
    top = decision.findings[0]
    text += f" Most serious: {top.title.lower()} at {top.location or top.file}."
    if decision.verdict is Verdict.ASK_HUMAN:
        text += " Nothing is clearly wrong, but the change touches access or deletes resources, so it needs sign-off."
    return text
