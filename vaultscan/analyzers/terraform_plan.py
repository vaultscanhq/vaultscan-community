"""Review a Terraform plan before it is applied.

Input is the JSON form of a plan:

    terraform plan -out tfplan
    terraform show -json tfplan > plan.json

The checks focus on what an apply would *change*, not on static style:
data loss, widening network exposure and privilege changes.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from vaultscan.models import Finding, Severity

# Resources that hold data which cannot be recreated by re-running Terraform.
STATEFUL_TYPES = {
    "aws_db_instance", "aws_rds_cluster", "aws_dynamodb_table", "aws_s3_bucket",
    "aws_efs_file_system", "aws_ebs_volume", "aws_elasticache_replication_group",
    "aws_opensearch_domain", "aws_elasticsearch_domain", "aws_kms_key",
    "aws_redshift_cluster", "aws_docdb_cluster", "aws_secretsmanager_secret",
    "aws_kinesis_stream", "aws_route53_zone", "aws_ecr_repository",
}
IAM_TYPES = {
    "aws_iam_role", "aws_iam_policy", "aws_iam_role_policy", "aws_iam_user_policy",
    "aws_iam_group_policy", "aws_iam_role_policy_attachment", "aws_iam_user_policy_attachment",
    "aws_iam_group_policy_attachment", "aws_iam_user", "aws_iam_access_key",
}
ADMIN_POLICY_ARN = "arn:aws:iam::aws:policy/AdministratorAccess"
SENSITIVE_PORTS = {22: "SSH", 3389: "RDP", 3306: "MySQL", 5432: "PostgreSQL",
                   1433: "SQL Server", 6379: "Redis", 27017: "MongoDB", 9200: "Elasticsearch"}
WEB_PORTS = {80, 443}
WORLD = {"0.0.0.0/0", "::/0"}


def load_plan(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        plan = json.load(handle)
    if not isinstance(plan, dict) or not ({"resource_changes", "format_version"} & set(plan)):
        raise ValueError(f"{path} does not look like `terraform show -json` output")
    return plan


def _as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _policy_statements(document: Any) -> List[dict]:
    """IAM policy documents arrive as JSON strings inside the plan."""
    if isinstance(document, str):
        try:
            document = json.loads(document)
        except ValueError:
            return []
    if not isinstance(document, dict):
        return []
    return [s for s in _as_list(document.get("Statement")) if isinstance(s, dict)]


def _is_wildcard_admin(statement: dict) -> bool:
    if statement.get("Effect") != "Allow":
        return False
    actions = _as_list(statement.get("Action"))
    resources = _as_list(statement.get("Resource"))
    return "*" in actions and "*" in resources


def _open_ingress(resource_type: str, after: dict) -> Iterable[tuple]:
    """Yield (from_port, to_port) for every ingress rule open to the internet."""
    if resource_type == "aws_security_group":
        rules = _as_list(after.get("ingress"))
    elif resource_type == "aws_security_group_rule":
        rules = [after] if after.get("type") == "ingress" else []
    elif resource_type == "aws_vpc_security_group_ingress_rule":
        rules = [after]
    else:
        rules = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        cidrs = set(_as_list(rule.get("cidr_blocks"))) | set(_as_list(rule.get("ipv6_cidr_blocks")))
        cidrs |= {c for c in (rule.get("cidr_ipv4"), rule.get("cidr_ipv6")) if c}
        if not cidrs & WORLD:
            continue
        protocol = str(rule.get("protocol", rule.get("ip_protocol", "")))
        if protocol in ("-1", "all"):
            yield (0, 65535)
        else:
            from_port = rule.get("from_port")
            to_port = rule.get("to_port", from_port)
            if from_port is not None and to_port is not None:
                yield (int(from_port), int(to_port))


def analyze_plan(plan: Dict[str, Any], max_deletes: int = 5, source_file: str = "plan.json") -> List[Finding]:
    findings: List[Finding] = []
    deletes = 0

    def add(rule_id, title, severity, address, detail, remediation, approval=False):
        findings.append(Finding(
            rule_id=rule_id, title=title, severity=severity, source="terraform",
            file=source_file, resource=address, detail=detail, remediation=remediation,
            needs_approval=approval,
        ))

    for change in plan.get("resource_changes") or []:
        address = change.get("address", "?")
        rtype = change.get("type", "")
        body = change.get("change") or {}
        actions = body.get("actions") or []
        before = body.get("before") or {}
        after = body.get("after") or {}
        if actions in (["no-op"], ["read"]):
            continue

        deleting = "delete" in actions
        replacing = deleting and "create" in actions
        if deleting:
            deletes += 1

        if deleting and rtype in STATEFUL_TYPES:
            if replacing:
                add("TF-002", "Stateful resource will be replaced", Severity.CRITICAL, address,
                    f"{rtype} is destroyed and recreated; existing data does not carry over.",
                    "Check which attribute forces replacement and change it in place, or migrate the data first.")
            else:
                add("TF-001", "Stateful resource will be destroyed", Severity.CRITICAL, address,
                    f"{rtype} holds data that Terraform cannot restore.",
                    "Confirm a backup exists and the deletion is intended; use prevent_destroy on resources that must stay.")
        elif deleting and not replacing:
            add("TF-011", "Resource will be destroyed", Severity.LOW, address,
                f"{rtype} is removed by this plan.", "Confirm the resource is no longer in use.")

        if not after:
            continue

        # --- privilege changes -------------------------------------------
        if rtype in IAM_TYPES:
            statements = _policy_statements(after.get("policy"))
            if any(_is_wildcard_admin(s) for s in statements):
                add("TF-004", "IAM policy grants every action on every resource", Severity.CRITICAL, address,
                    'A statement allows Action "*" on Resource "*".',
                    "Scope the policy to the actions and ARNs the workload needs.")
            elif after.get("policy_arn") == ADMIN_POLICY_ARN:
                add("TF-005", "AdministratorAccess attached", Severity.HIGH, address,
                    "The AWS managed AdministratorAccess policy is being attached.",
                    "Attach a least-privilege policy instead, or get explicit sign-off.", approval=True)
            else:
                add("TF-005", "IAM change", Severity.LOW, address,
                    f"{rtype}: {', '.join(actions)}.",
                    "Have someone who owns access review this change.", approval=True)

        # --- network exposure --------------------------------------------
        for from_port, to_port in _open_ingress(rtype, after):
            ports = range(from_port, to_port + 1)
            exposed = [name for port, name in SENSITIVE_PORTS.items() if port in ports]
            if exposed or (to_port - from_port) > 1000:
                what = ", ".join(exposed) if exposed else f"ports {from_port}-{to_port}"
                add("TF-006", "Sensitive port open to the internet", Severity.CRITICAL, address,
                    f"Ingress from 0.0.0.0/0 reaches {what}.",
                    "Restrict the source to a VPN, bastion or specific CIDR range.")
            elif not set(ports) <= WEB_PORTS:
                add("TF-006", "Port open to the internet", Severity.HIGH, address,
                    f"Ingress from 0.0.0.0/0 on port {from_port}"
                    + (f"-{to_port}" if to_port != from_port else "") + ".",
                    "Restrict the source CIDR unless this is a public endpoint.")

        if rtype == "aws_s3_bucket_public_access_block":
            disabled = [k for k in ("block_public_acls", "block_public_policy",
                                    "ignore_public_acls", "restrict_public_buckets")
                        if after.get(k) is False]
            if disabled:
                add("TF-007", "S3 public access block weakened", Severity.HIGH, address,
                    f"Disabled: {', '.join(disabled)}.",
                    "Keep all four public access block settings enabled; serve public content through CloudFront.")
        if rtype in ("aws_s3_bucket", "aws_s3_bucket_acl") and after.get("acl") in ("public-read", "public-read-write"):
            add("TF-007", "S3 bucket ACL is public", Severity.HIGH, address,
                f"ACL is {after.get('acl')}.", "Use a private ACL and grant access through a bucket policy.")

        if rtype in ("aws_db_instance", "aws_rds_cluster_instance") and after.get("publicly_accessible") is True:
            add("TF-008", "Database is publicly accessible", Severity.CRITICAL, address,
                "publicly_accessible is true.", "Place the database in private subnets and set publicly_accessible = false.")

        # --- data protection ---------------------------------------------
        if rtype in ("aws_db_instance", "aws_rds_cluster") and after.get("storage_encrypted") is False:
            add("TF-009", "Storage is not encrypted", Severity.MEDIUM, address,
                "storage_encrypted is false.", "Enable storage_encrypted and set a KMS key.")
        if rtype == "aws_ebs_volume" and after.get("encrypted") is False:
            add("TF-009", "Storage is not encrypted", Severity.MEDIUM, address,
                "encrypted is false.", "Enable encryption on the volume or turn on EBS encryption by default.")

        if before.get("deletion_protection") is True and after.get("deletion_protection") is False:
            add("TF-010", "Deletion protection is being turned off", Severity.HIGH, address,
                "deletion_protection changes from true to false.",
                "This is usually the step before a destroy; confirm that is the intent.", approval=True)

    if deletes > max_deletes:
        add("TF-003", "Plan deletes an unusually large number of resources", Severity.HIGH, "(whole plan)",
            f"{deletes} resources are destroyed; the policy threshold is {max_deletes}.",
            "Check the workspace, variables and state backend are the ones you expect.", approval=True)
    return findings


def analyze_plan_file(path: str, max_deletes: int = 5) -> List[Finding]:
    return analyze_plan(load_plan(path), max_deletes=max_deletes, source_file=path)
