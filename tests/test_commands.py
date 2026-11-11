import pytest

from vaultscan.analyzers.commands import analyze_command
from vaultscan.engine import decide
from vaultscan.models import Severity, Verdict


def verdict(command):
    return decide(analyze_command(command)).verdict


@pytest.mark.parametrize("command", [
    "terraform destroy -auto-approve",
    "terraform -chdir=envs/prod apply -destroy",
    "kubectl delete namespace payments",
    "kubectl delete pods --all -n web",
    "rm -rf /",
    "rm -rf ~",
    "aws s3 rb s3://company-backups --force",
    "aws rds delete-db-instance --db-instance-identifier orders",
    'psql -c "DROP DATABASE orders"',
])
def test_destructive_commands_are_blocked(command):
    assert verdict(command) is Verdict.BLOCK


@pytest.mark.parametrize("command", [
    "terraform apply -auto-approve",
    "git push --force origin main",
    "git push origin +main",
    "helm uninstall ingress-nginx -n ingress",
    "kubectl delete pod api-7d9f -n web",
    "aws iam attach-role-policy --role-name ci --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess",
    "terraform state rm aws_instance.web",
])
def test_risky_commands_need_a_human(command):
    assert verdict(command) is Verdict.ASK_HUMAN


@pytest.mark.parametrize("command", [
    "terraform plan -out tfplan",
    "kubectl get pods -A",
    "git push origin feature/login",
    "aws s3 ls",
    "rm -rf ./build",
    "helm upgrade --install api ./chart",
])
def test_everyday_commands_are_allowed(command):
    assert verdict(command) is Verdict.ALLOW


def test_chained_commands_are_checked_individually():
    findings = analyze_command("terraform plan && kubectl delete ns staging; echo done")
    assert [f.rule_id for f in findings] == ["CMD-010"]


def test_production_target_raises_severity():
    normal = analyze_command("helm uninstall api -n staging")[0]
    prod = analyze_command("helm uninstall api -n prod")[0]
    assert normal.severity is Severity.HIGH
    assert prod.severity is Severity.CRITICAL
