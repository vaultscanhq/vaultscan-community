"""Checks for GitHub Actions workflows.

CI has write access to the repository and usually to cloud credentials, so a
workflow that can be steered by a pull request is a supply-chain risk.
"""

from __future__ import annotations

import os
import re
from typing import Any, Iterable, List

import yaml

from vaultscan.models import Finding, Severity

TRUSTED_ACTION_OWNERS = {"actions", "github"}
_SHA = re.compile(r"^[0-9a-f]{40}$")
# Values an outside contributor controls. Interpolating them into a shell
# script lets the contributor run their own commands.
_UNTRUSTED_EXPR = re.compile(
    r"\$\{\{\s*github\.(?:event\.(?:issue|pull_request|comment|review|discussion|head_commit)"
    r"\.(?:title|body|message|head\.ref|head\.label)|head_ref)\s*\}\}"
)
_PIPE_TO_SHELL = re.compile(r"(?:curl|wget)[^\n|]*\|\s*(?:sudo\s+)?(?:ba)?sh\b")
_PR_HEAD_REF = re.compile(r"github\.event\.pull_request\.head\.(?:sha|ref)|github\.head_ref")


def _triggers(workflow: dict) -> set:
    # PyYAML follows YAML 1.1 and reads the bare key `on` as boolean True.
    raw = workflow.get("on", workflow.get(True))
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return set(raw)
    if isinstance(raw, dict):
        return set(raw)
    return set()


def analyze_workflow(workflow: Any, source_file: str = "") -> List[Finding]:
    if not isinstance(workflow, dict) or not isinstance(workflow.get("jobs"), dict):
        return []
    findings: List[Finding] = []

    def add(rule_id, title, severity, where, detail, remediation):
        findings.append(Finding(rule_id=rule_id, title=title, severity=severity, source="workflow",
                                file=source_file, resource=where, detail=detail, remediation=remediation))

    triggers = _triggers(workflow)
    top_permissions = workflow.get("permissions")
    if top_permissions == "write-all":
        add("GHA-004", "Workflow token has write access to everything", Severity.HIGH, "permissions",
            "permissions: write-all gives every job a fully privileged GITHUB_TOKEN.",
            "Set permissions: contents: read at the top and grant more per job.")

    any_job_permissions = False
    for job_id, job in workflow["jobs"].items():
        if not isinstance(job, dict):
            continue
        where = f"jobs.{job_id}"
        if "permissions" in job:
            any_job_permissions = True
            if job["permissions"] == "write-all":
                add("GHA-004", "Job token has write access to everything", Severity.HIGH, where,
                    "permissions: write-all on this job.", "Grant only the scopes the job uses.")
        for index, step in enumerate(job.get("steps") or []):
            if not isinstance(step, dict):
                continue
            step_where = f"{where}.steps[{index}]"
            uses = step.get("uses")
            if isinstance(uses, str) and "@" in uses and not uses.startswith(("./", "docker://")):
                action, ref = uses.rsplit("@", 1)
                owner = action.split("/", 1)[0]
                if owner not in TRUSTED_ACTION_OWNERS and not _SHA.match(ref):
                    add("GHA-003", "Third-party action is not pinned to a commit", Severity.MEDIUM, step_where,
                        f"{uses} uses a tag or branch that its owner can move.",
                        "Pin to the full commit SHA and note the version in a comment.")
                if "pull_request_target" in triggers and action == "actions/checkout":
                    checkout_ref = str((step.get("with") or {}).get("ref", ""))
                    if _PR_HEAD_REF.search(checkout_ref):
                        add("GHA-001", "pull_request_target checks out untrusted code", Severity.CRITICAL, step_where,
                            "The workflow runs with repository secrets but checks out the pull request's code.",
                            "Use the pull_request trigger, or never build or run the checked-out PR code here.")
            run = step.get("run")
            if isinstance(run, str):
                if _UNTRUSTED_EXPR.search(run):
                    add("GHA-002", "Untrusted input is interpolated into a shell script", Severity.HIGH, step_where,
                        "A value such as the PR title or branch name is expanded inside run:.",
                        "Pass the value through env: and reference it as a quoted shell variable.")
                if _PIPE_TO_SHELL.search(run):
                    add("GHA-005", "Script is downloaded and piped straight into a shell", Severity.MEDIUM, step_where,
                        "curl | sh runs whatever the remote server returns at that moment.",
                        "Download a pinned version, verify its checksum, then run it.")

    if top_permissions is None and not any_job_permissions:
        add("GHA-004", "No permissions block", Severity.LOW, "permissions",
            "The workflow inherits the repository's default token permissions.",
            "Add permissions: contents: read and widen it only where needed.")
    return findings


def iter_workflow_files(path: str) -> Iterable[str]:
    if os.path.isfile(path):
        yield path
        return
    workflows_dir = os.path.join(path, ".github", "workflows")
    root = workflows_dir if os.path.isdir(workflows_dir) else path
    for name in sorted(os.listdir(root)):
        if name.endswith((".yml", ".yaml")):
            yield os.path.join(root, name)


def analyze_workflows(path: str) -> List[Finding]:
    findings: List[Finding] = []
    for file_path in iter_workflow_files(path):
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                findings.extend(analyze_workflow(yaml.safe_load(handle), file_path))
        except yaml.YAMLError:
            continue
    return findings
