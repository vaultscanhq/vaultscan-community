import os

from vaultscan.analyzers.workflows import analyze_workflows
from vaultscan.engine import decide
from vaultscan.models import Verdict

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_risky_workflow():
    findings = analyze_workflows(os.path.join(FIXTURES, "workflow_risky.yml"))
    rules = {f.rule_id for f in findings}
    assert rules == {"GHA-001", "GHA-002", "GHA-003", "GHA-004", "GHA-005"}
    assert decide(findings).verdict is Verdict.BLOCK


def test_safe_workflow():
    # SHA-pinned third-party action, read-only token, and untrusted input
    # passed through env instead of being expanded in the script.
    assert analyze_workflows(os.path.join(FIXTURES, "workflow_safe.yml")) == []


def test_directory_scan_finds_dot_github(tmp_path):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "on: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make\n"
    )
    findings = analyze_workflows(str(tmp_path))
    assert [f.rule_id for f in findings] == ["GHA-004"]  # only the missing permissions note
