import os

import pytest

from vaultscan.analyzers.terraform_plan import analyze_plan, analyze_plan_file, load_plan
from vaultscan.engine import decide
from vaultscan.models import Severity, Verdict

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def by_rule(findings):
    grouped = {}
    for finding in findings:
        grouped.setdefault(finding.rule_id, []).append(finding)
    return grouped


def test_risky_plan_is_blocked():
    findings = analyze_plan_file(os.path.join(FIXTURES, "plan_risky.json"))
    rules = by_rule(findings)
    assert rules["TF-001"][0].resource == "aws_db_instance.orders"
    assert rules["TF-002"][0].resource == "aws_dynamodb_table.sessions"
    assert rules["TF-004"][0].severity is Severity.CRITICAL
    assert "SSH" in rules["TF-006"][0].detail
    assert {"TF-007", "TF-008", "TF-010"} <= set(rules)
    assert decide(findings).verdict is Verdict.BLOCK


def test_safe_plan_is_allowed():
    findings = analyze_plan_file(os.path.join(FIXTURES, "plan_safe.json"))
    assert findings == []
    assert decide(findings).verdict is Verdict.ALLOW


def change(rtype, actions, after=None, before=None, name="x"):
    return {"address": f"{rtype}.{name}", "type": rtype,
            "change": {"actions": actions, "before": before, "after": after}}


def test_plain_iam_change_asks_for_a_human():
    plan = {"resource_changes": [change("aws_iam_role", ["create"], {"name": "ci"})]}
    decision = decide(analyze_plan(plan))
    assert decision.verdict is Verdict.ASK_HUMAN


def test_bulk_delete_threshold():
    plan = {"resource_changes": [change("aws_sqs_queue", ["delete"], name=f"q{i}") for i in range(4)]}
    assert "TF-003" not in by_rule(analyze_plan(plan, max_deletes=5))
    assert "TF-003" in by_rule(analyze_plan(plan, max_deletes=3))


def test_all_protocols_open_to_world_is_critical():
    after = {"ip_protocol": "-1", "cidr_ipv4": "0.0.0.0/0"}
    plan = {"resource_changes": [change("aws_vpc_security_group_ingress_rule", ["create"], after)]}
    finding = analyze_plan(plan)[0]
    assert finding.rule_id == "TF-006" and finding.severity is Severity.CRITICAL


def test_non_web_port_open_to_world_is_high():
    after = {"type": "ingress", "from_port": 8080, "to_port": 8080, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}
    plan = {"resource_changes": [change("aws_security_group_rule", ["create"], after)]}
    assert analyze_plan(plan)[0].severity is Severity.HIGH


def test_rejects_files_that_are_not_plans(tmp_path):
    bogus = tmp_path / "x.json"
    bogus.write_text('{"hello": "world"}')
    with pytest.raises(ValueError):
        load_plan(str(bogus))
