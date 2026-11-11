import json
import os

from vaultscan.cli import main

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def run(capsys, *argv):
    code = main(list(argv))
    return code, capsys.readouterr().out


def test_plan_json_output_blocks(capsys):
    code, out = run(capsys, "plan", os.path.join(FIXTURES, "plan_risky.json"), "--format", "json")
    payload = json.loads(out)
    assert code == 1
    assert payload["verdict"] == "BLOCK"
    assert payload["findings"][0]["severity"] == "CRITICAL"


def test_safe_plan_exits_zero(capsys):
    code, out = run(capsys, "plan", os.path.join(FIXTURES, "plan_safe.json"), "--format", "json")
    assert code == 0 and json.loads(out)["verdict"] == "ALLOW"


def test_command_guard(capsys):
    code, out = run(capsys, "command", "kubectl delete ns payments", "--format", "json")
    assert code == 1 and json.loads(out)["verdict"] == "BLOCK"


def test_gate_combines_checks(capsys, tmp_path):
    (tmp_path / "app.py").write_text("print('hello')\n")
    code, out = run(capsys, "gate", "--path", str(tmp_path),
                    "--manifests", os.path.join(FIXTURES, "k8s_risky.yaml"), "--format", "json")
    payload = json.loads(out)
    assert code == 1
    assert {f["source"] for f in payload["findings"]} == {"kubernetes"}


def test_policy_file_can_relax_the_gate(capsys, tmp_path):
    policy = tmp_path / "policy.yml"
    policy.write_text("ignore_rules: [CMD-010]\n")
    code, _ = run(capsys, "command", "kubectl delete ns scratch", "--policy", str(policy), "--format", "json")
    assert code == 0


def test_sarif_and_markdown(capsys):
    _, sarif = run(capsys, "workflows", os.path.join(FIXTURES, "workflow_risky.yml"), "--format", "sarif")
    doc = json.loads(sarif)
    assert doc["version"] == "2.1.0" and len(doc["runs"][0]["results"]) == 5
    _, markdown = run(capsys, "workflows", os.path.join(FIXTURES, "workflow_risky.yml"), "--format", "markdown")
    assert markdown.startswith("## VaultScan: BLOCK")


def test_legacy_invocation_still_works(capsys, tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    assert main(["--path", str(tmp_path)]) == 0


def test_missing_input_is_a_usage_error(capsys):
    assert main(["plan", "does-not-exist.json"]) == 2
