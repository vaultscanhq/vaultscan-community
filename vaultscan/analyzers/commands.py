"""Guard for shell commands proposed by an AI agent or a script.

An agent that can run `terraform`, `kubectl` or `aws` can do as much damage
as an engineer with the same credentials, but without the hesitation. This
module classifies a command *before* it runs so the caller can stop, ask a
person, or carry on.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import List, Pattern

from vaultscan.models import Finding, Severity


@dataclass(frozen=True)
class CommandRule:
    rule_id: str
    title: str
    severity: Severity
    pattern: Pattern[str]
    remediation: str
    needs_approval: bool = False


def _rule(rule_id, title, severity, regex, remediation, approval=False):
    return CommandRule(rule_id, title, severity, re.compile(regex, re.IGNORECASE), remediation, approval)


COMMAND_RULES: List[CommandRule] = [
    _rule("CMD-001", "Terraform destroy", Severity.CRITICAL,
          r"\bterraform\b.*\b(destroy\b|apply\b.*-destroy\b)",
          "Never let an unattended process destroy a workspace; plan the destroy and have it reviewed."),
    _rule("CMD-002", "Terraform apply without review", Severity.HIGH,
          r"\bterraform\b.*\bapply\b.*-auto-approve\b",
          "Run `terraform plan -out`, gate the plan with `vaultscan plan`, then apply that saved plan.",
          approval=True),
    _rule("CMD-003", "Terraform state surgery", Severity.HIGH,
          r"\bterraform\b.*\b(state\s+(rm|mv|push)|force-unlock)\b",
          "State edits are hard to undo; take a state backup and get a second pair of eyes.", approval=True),
    _rule("CMD-010", "Kubernetes namespace or cluster-wide delete", Severity.CRITICAL,
          r"\bkubectl\b.*\bdelete\b.*(\b(namespace|ns|node|pv|crd)s?\b|--all\b|-A\b|--all-namespaces\b)",
          "Delete the specific workload by name instead of a namespace or everything."),
    _rule("CMD-011", "Kubernetes delete", Severity.MEDIUM,
          r"\bkubectl\b.*\bdelete\b",
          "Confirm the target context and resource before deleting.", approval=True),
    _rule("CMD-012", "Helm release removal", Severity.HIGH,
          r"\bhelm\b.*\b(uninstall|delete)\b",
          "Uninstalling removes the release's resources, including PVCs for some charts.", approval=True),
    _rule("CMD-020", "Force push", Severity.HIGH,
          r"\bgit\b.*\bpush\b.*(--force\b|-f\b|--force-with-lease\b|\s\+\S+)",
          "Force pushing rewrites shared history; push a new commit or open a PR instead.", approval=True),
    _rule("CMD-021", "Git history or working tree wipe", Severity.MEDIUM,
          r"\bgit\b.*\b(reset\s+--hard|clean\s+-[a-z]*f|branch\s+-D)\b",
          "Stash or commit local work first.", approval=True),
    _rule("CMD-030", "Recursive delete of a root or home path", Severity.CRITICAL,
          r"\brm\b\s+(-[a-z]*\s+)*-[a-z]*[rf][a-z]*\s+(-[a-z-]+\s+)*(/|~|\$HOME|/\*|\.\.?)(\s|$)",
          "Point the delete at a specific build directory."),
    _rule("CMD-040", "AWS data deletion", Severity.CRITICAL,
          r"\baws\b.*\b(s3\s+rb\b|s3\s+rm\b.*--recursive|rds\s+delete-db-(instance|cluster)|"
          r"dynamodb\s+delete-table|ec2\s+terminate-instances|kms\s+schedule-key-deletion|"
          r"cloudformation\s+delete-stack|eks\s+delete-cluster)",
          "Deleting cloud data is irreversible; a human should run this deliberately."),
    _rule("CMD-041", "AWS IAM change", Severity.HIGH,
          r"\baws\b.*\biam\b.*\b(create-access-key|attach-(user|role|group)-policy|put-(user|role|group)-policy|"
          r"create-user|update-assume-role-policy|delete-\w+)",
          "Access changes should go through reviewed infrastructure code.", approval=True),
    _rule("CMD-050", "Destructive SQL", Severity.CRITICAL,
          r"\b(drop\s+(database|schema|table)|truncate\s+table)\b",
          "Take a backup and run schema changes through a migration tool."),
    _rule("CMD-060", "Remote script piped into a shell", Severity.HIGH,
          r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba|z)?sh\b",
          "Download the script, read it, then run a pinned version."),
    _rule("CMD-061", "World-writable permissions", Severity.MEDIUM,
          r"\bchmod\b\s+(-[a-z]+\s+)*0?777\b",
          "Grant the narrowest mode that works."),
]

_PROD_HINT = re.compile(r"(?<![a-z])(prod|production|prd|live)(?![a-z])", re.IGNORECASE)


def split_commands(command_line: str) -> List[str]:
    """Split on shell separators so `a && b` is checked piece by piece."""
    parts = re.split(r"\s*(?:&&|\|\||;|\n)\s*", command_line)
    return [part for part in (p.strip() for p in parts) if part]


def analyze_command(command_line: str) -> List[Finding]:
    findings: List[Finding] = []
    for command in split_commands(command_line):
        try:
            normalised = " ".join(shlex.split(command, posix=True))
        except ValueError:
            normalised = command
        matched = None
        for rule in COMMAND_RULES:  # ordered: the more serious rule for a tool comes first
            if rule.pattern.search(normalised) or rule.pattern.search(command):
                matched = rule
                break
        if matched is None:
            continue
        severity = matched.severity
        detail = f"Command: {command}"
        if _PROD_HINT.search(command) and severity < Severity.CRITICAL:
            severity = Severity(severity + 1)
            detail += " (targets something that looks like production)"
        findings.append(Finding(
            rule_id=matched.rule_id, title=matched.title, severity=severity, source="command",
            resource=command[:80], detail=detail, remediation=matched.remediation,
            needs_approval=matched.needs_approval,
        ))
    return findings
