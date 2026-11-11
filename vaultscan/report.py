"""Output formats: terminal table, JSON, Markdown (PR comments) and SARIF."""

from __future__ import annotations

import json
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from vaultscan import __version__
from vaultscan.engine import Decision
from vaultscan.models import Severity, Verdict

VERDICT_STYLE = {
    Verdict.ALLOW: "bold green",
    Verdict.WARN: "bold yellow",
    Verdict.ASK_HUMAN: "bold magenta",
    Verdict.BLOCK: "bold red",
}
SEVERITY_STYLE = {
    Severity.CRITICAL: "bold red", Severity.HIGH: "red", Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan", Severity.INFO: "dim",
}
VERDICT_HELP = {
    Verdict.ALLOW: "Nothing here needs attention.",
    Verdict.WARN: "Safe to proceed, but the findings below are worth fixing.",
    Verdict.ASK_HUMAN: "A person should review and approve this change before it goes ahead.",
    Verdict.BLOCK: "This change should not go ahead as it stands.",
}
_SARIF_LEVEL = {Severity.CRITICAL: "error", Severity.HIGH: "error", Severity.MEDIUM: "warning",
                Severity.LOW: "note", Severity.INFO: "note"}


def render_console(decision: Decision, summary: Optional[str] = None, console: Optional[Console] = None) -> None:
    console = console or Console()
    if decision.findings:
        table = Table(show_lines=True, title="VaultScan findings")
        table.add_column("Severity")
        table.add_column("Rule", style="bold")
        table.add_column("Where", overflow="fold")
        table.add_column("What and how to fix", overflow="fold")
        for finding in decision.findings:
            text = f"[bold]{finding.title}[/bold]\n{finding.detail}"
            if finding.explanation:
                text += f"\n[italic]{finding.explanation}[/italic]"
            if finding.remediation:
                text += f"\n[green]Fix:[/green] {finding.remediation}"
            style = SEVERITY_STYLE[finding.severity]
            table.add_row(f"[{style}]{finding.severity.name}[/{style}]", finding.rule_id,
                          finding.location or finding.file, text)
        console.print(table)
    body = VERDICT_HELP[decision.verdict]
    if summary:
        body += f"\n\n{summary}"
    style = VERDICT_STYLE[decision.verdict]
    console.print(Panel(body, title=f"[{style}]{decision.verdict.label}[/{style}]", border_style=style.split()[-1]))


def to_json(decision: Decision, summary: Optional[str] = None) -> str:
    return json.dumps({
        "tool": "vaultscan",
        "version": __version__,
        "verdict": decision.verdict.name,
        "exit_code": decision.exit_code,
        "summary": summary,
        "reasons": decision.reasons,
        "findings": [finding.to_dict() for finding in decision.findings],
    }, indent=2)


def to_markdown(decision: Decision, summary: Optional[str] = None) -> str:
    """Compact report suitable for a pull request comment or job summary."""
    lines = [f"## VaultScan: {decision.verdict.label}", "", VERDICT_HELP[decision.verdict], ""]
    if summary:
        lines += [summary, ""]
    if decision.findings:
        lines += ["| Severity | Rule | Where | Finding | Fix |", "| --- | --- | --- | --- | --- |"]
        for f in decision.findings:
            cells = [f.severity.name, f.rule_id, f"`{f.location or f.file}`",
                     f"{f.title}. {f.explanation or f.detail}", f.remediation]
            lines.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
    else:
        lines.append("No findings.")
    return "\n".join(lines) + "\n"


def to_sarif(decision: Decision) -> str:
    """SARIF 2.1.0, so results show up in GitHub code scanning."""
    rules = {}
    results = []
    for f in decision.findings:
        rules.setdefault(f.rule_id, {
            "id": f.rule_id,
            "name": f.title,
            "shortDescription": {"text": f.title},
            "help": {"text": f.remediation or f.title},
        })
        result = {
            "ruleId": f.rule_id,
            "level": _SARIF_LEVEL[f.severity],
            "message": {"text": f"{f.title}: {f.detail}".strip(": ")},
        }
        if f.file:
            location = {"artifactLocation": {"uri": f.file.replace("\\", "/")}}
            if f.line:
                location["region"] = {"startLine": f.line}
            result["locations"] = [{"physicalLocation": location}]
        results.append(result)
    return json.dumps({
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "VaultScan",
                "version": __version__,
                "informationUri": "https://github.com/vaultscanhq/vaultscan-community",
                "rules": list(rules.values()),
            }},
            "results": results,
        }],
    }, indent=2)
