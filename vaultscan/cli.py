"""Command line interface.

    vaultscan gate --path . --plan plan.json     # everything, one verdict
    vaultscan secrets --path .
    vaultscan plan plan.json
    vaultscan k8s deploy/
    vaultscan workflows .
    vaultscan command "terraform destroy"        # for AI agents and wrappers

Exit codes: 0 = ALLOW or WARN, 1 = ASK HUMAN or BLOCK, 2 = usage or input error.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from rich.console import Console

from vaultscan import __version__, report
from vaultscan.analyzers.commands import analyze_command
from vaultscan.analyzers.kubernetes import analyze_manifests
from vaultscan.analyzers.terraform_plan import analyze_plan_file
from vaultscan.analyzers.workflows import analyze_workflows
from vaultscan.engine import decide
from vaultscan.models import Finding
from vaultscan.policy import Policy
from vaultscan.secrets import scan_path

FORMATS = ("table", "json", "markdown", "sarif")


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=FORMATS, default="table", help="output format (default: table)")
    parser.add_argument("--output", metavar="FILE", help="write the report to a file instead of stdout")
    parser.add_argument("--policy", metavar="FILE", help="policy file (default: .vaultscan.yml if present)")
    parser.add_argument("--ai", action="store_true",
                        help="ask the configured AI model to explain the findings (see docs/ai.md)")
    parser.add_argument("--verbose", action="store_true", help="show files as they are scanned")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vaultscan",
        description="Change gate for infrastructure: secrets, Terraform plans, Kubernetes manifests, "
                    "CI workflows and agent commands.",
    )
    parser.add_argument("--version", action="version", version=f"vaultscan {__version__}")
    sub = parser.add_subparsers(dest="command_name", metavar="COMMAND")

    gate = sub.add_parser("gate", help="run every check that applies and return one verdict")
    gate.add_argument("--path", default=".", help="repository to scan (default: current directory)")
    gate.add_argument("--plan", metavar="PLAN_JSON", help="output of `terraform show -json`")
    gate.add_argument("--manifests", metavar="PATH", help="Kubernetes manifests (file or directory)")
    gate.add_argument("--skip", action="append", default=[], choices=("secrets", "workflows"),
                      help="skip a check that runs by default")
    _common(gate)

    secrets = sub.add_parser("secrets", help="scan a directory or file for leaked credentials")
    secrets.add_argument("--path", default=".")
    _common(secrets)

    plan = sub.add_parser("plan", help="review a Terraform plan (JSON)")
    plan.add_argument("plan_file", metavar="PLAN_JSON")
    _common(plan)

    k8s = sub.add_parser("k8s", help="review Kubernetes manifests")
    k8s.add_argument("manifest_path", metavar="PATH")
    _common(k8s)

    workflows = sub.add_parser("workflows", help="review GitHub Actions workflows")
    workflows.add_argument("workflow_path", metavar="PATH", nargs="?", default=".")
    _common(workflows)

    command = sub.add_parser("command", help="classify a shell command before it runs")
    command.add_argument("shell_command", metavar="COMMAND_STRING")
    _common(command)
    return parser


def _require(path: str, kind: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{kind} not found: {path}")


def collect(args: argparse.Namespace, policy: Policy, log) -> List[Finding]:
    name = args.command_name
    if name == "secrets":
        _require(args.path, "path")
        return scan_path(args.path, log)
    if name == "plan":
        _require(args.plan_file, "plan file")
        return analyze_plan_file(args.plan_file, policy.max_deletes)
    if name == "k8s":
        _require(args.manifest_path, "manifest path")
        return analyze_manifests(args.manifest_path)
    if name == "workflows":
        _require(args.workflow_path, "workflow path")
        return analyze_workflows(args.workflow_path)
    if name == "command":
        return analyze_command(args.shell_command)

    # gate
    _require(args.path, "path")
    findings: List[Finding] = []
    if "secrets" not in args.skip:
        findings += scan_path(args.path, log)
    if "workflows" not in args.skip and os.path.isdir(os.path.join(args.path, ".github", "workflows")):
        findings += analyze_workflows(args.path)
    if args.plan:
        _require(args.plan, "plan file")
        findings += analyze_plan_file(args.plan, policy.max_deletes)
    if args.manifests:
        _require(args.manifests, "manifest path")
        findings += analyze_manifests(args.manifests)
    return findings


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # v1.x was invoked as `vaultscan --path DIR`; keep that working.
    if argv and argv[0] in ("--path", "--verbose"):
        argv = ["secrets"] + argv
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command_name:
        parser.print_help()
        return 2

    stderr = Console(stderr=True)
    log = (lambda message: stderr.print(f"[dim]{message}[/dim]")) if args.verbose else None
    try:
        search_dir = getattr(args, "path", ".")
        policy = Policy.load(args.policy, search_dir if os.path.isdir(search_dir) else ".")
        findings = collect(args, policy, log)
    except (FileNotFoundError, ValueError) as exc:
        stderr.print(f"[red]error:[/red] {exc}")
        return 2

    decision = decide(findings, policy)
    summary = None
    if args.ai:
        from vaultscan.ai.review import review

        summary, decision = review(decision, warn=lambda m: stderr.print(f"[yellow]ai:[/yellow] {m}"))

    if args.format == "json":
        text = report.to_json(decision, summary)
    elif args.format == "markdown":
        text = report.to_markdown(decision, summary)
    elif args.format == "sarif":
        text = report.to_sarif(decision)
    else:
        text = None

    if text is None:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                report.render_console(decision, summary, Console(file=handle, width=120))
        else:
            report.render_console(decision, summary)
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
        stderr.print(f"{decision.verdict.label}: report written to {args.output}")
    else:
        print(text)
    return decision.exit_code


if __name__ == "__main__":
    sys.exit(main())
