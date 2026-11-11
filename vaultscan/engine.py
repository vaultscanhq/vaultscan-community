"""Turns a list of findings into a single gate decision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from vaultscan.models import Finding, Verdict
from vaultscan.policy import Policy


@dataclass
class Decision:
    verdict: Verdict
    findings: List[Finding]
    reasons: List[str]

    @property
    def exit_code(self) -> int:
        # WARN is advisory, so only the two stopping verdicts fail a pipeline.
        return 1 if self.verdict >= Verdict.ASK_HUMAN else 0


def apply_policy(findings: Iterable[Finding], policy: Policy) -> List[Finding]:
    """Drop ignored rules and apply severity overrides."""
    kept = []
    for finding in findings:
        rule = finding.rule_id.upper()
        if rule in policy.ignore_rules:
            continue
        if rule in policy.severity_overrides:
            finding.severity = policy.severity_overrides[rule]
        kept.append(finding)
    return kept


def verdict_for(finding: Finding, policy: Policy) -> Verdict:
    if finding.severity >= policy.block_on:
        return Verdict.BLOCK
    if finding.needs_approval:
        return Verdict.ASK_HUMAN
    if finding.severity >= policy.warn_on:
        return Verdict.WARN
    return Verdict.ALLOW


def decide(findings: Iterable[Finding], policy: Policy | None = None) -> Decision:
    policy = policy or Policy()
    kept = apply_policy(findings, policy)
    verdict = Verdict.ALLOW
    reasons: List[str] = []
    for finding in kept:
        outcome = verdict_for(finding, policy)
        if outcome > verdict:
            verdict = outcome
        if outcome >= Verdict.ASK_HUMAN:
            reasons.append(f"{finding.rule_id}: {finding.title} ({finding.location})")
    kept.sort(key=lambda f: (-f.severity, f.source, f.location))
    return Decision(verdict=verdict, findings=kept, reasons=reasons)
