import pytest

from vaultscan.engine import decide
from vaultscan.models import Finding, Severity, Verdict
from vaultscan.policy import Policy


def make(rule="X-1", severity=Severity.LOW, approval=False):
    return Finding(rule_id=rule, title="t", severity=severity, source="terraform",
                   resource="aws_thing.x", needs_approval=approval)


def test_no_findings_allows():
    decision = decide([])
    assert decision.verdict is Verdict.ALLOW
    assert decision.exit_code == 0


def test_medium_warns_but_does_not_fail():
    decision = decide([make(severity=Severity.MEDIUM)])
    assert decision.verdict is Verdict.WARN
    assert decision.exit_code == 0


def test_approval_flag_asks_human():
    decision = decide([make(severity=Severity.LOW, approval=True)])
    assert decision.verdict is Verdict.ASK_HUMAN
    assert decision.exit_code == 1


def test_critical_blocks_and_wins_over_everything():
    decision = decide([make(approval=True), make(rule="X-2", severity=Severity.CRITICAL)])
    assert decision.verdict is Verdict.BLOCK
    assert decision.findings[0].rule_id == "X-2"  # most severe first


def test_policy_ignore_and_override():
    policy = Policy.from_dict({"ignore_rules": ["x-1"], "severity_overrides": {"X-2": "critical"}})
    decision = decide([make(severity=Severity.CRITICAL), make(rule="X-2")], policy)
    assert [f.rule_id for f in decision.findings] == ["X-2"]
    assert decision.verdict is Verdict.BLOCK


def test_policy_rejects_inverted_thresholds():
    with pytest.raises(ValueError):
        Policy.from_dict({"block_on": "low", "warn_on": "high"})
