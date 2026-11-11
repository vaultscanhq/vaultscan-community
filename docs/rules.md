# Rules

Every rule has a stable ID that can be used in `ignore_rules` and `severity_overrides`.
Rules marked *approval* return ASK HUMAN even when their severity is below the blocking threshold.

## Secrets

| ID | Detects | Severity |
| --- | --- | --- |
| SEC-001 | AWS access key ID | Critical |
| SEC-002 | AWS secret access key | Critical |
| SEC-003 | GitHub token | Critical |
| SEC-004 | Slack token | High |
| SEC-005 | Stripe live secret key | Critical |
| SEC-006 | Google API key | High |
| SEC-007 | Azure key or token | High |
| SEC-008 | JSON Web Token | Medium |
| SEC-009 | Database connection string with password | High |
| SEC-010 | Credentials embedded in URL | High |
| SEC-011 | Twilio auth token | High |
| SEC-012 | Private key | Critical |
| SEC-013 | Hard-coded API key or secret | Medium |
| SEC-100 | High-entropy value assigned to a secret-like name | Medium |

## Terraform plans

| ID | Detects | Severity | |
| --- | --- | --- | --- |
| TF-001 | Stateful resource (database, bucket, KMS key, ...) will be destroyed | Critical |  |
| TF-002 | Stateful resource will be replaced (destroy and recreate) | Critical |  |
| TF-003 | Plan deletes more resources than `max_deletes` | High | approval |
| TF-004 | IAM policy allows `*` on `*` | Critical |  |
| TF-005 | IAM resource created or changed; AdministratorAccess attached | Low / High | approval |
| TF-006 | Ingress open to 0.0.0.0/0 (sensitive ports are critical, other non-web ports high) | Critical / High |  |
| TF-007 | S3 public access block weakened or public ACL | High |  |
| TF-008 | Database is publicly accessible | Critical |  |
| TF-009 | RDS or EBS storage not encrypted | Medium |  |
| TF-010 | Deletion protection turned off | High | approval |
| TF-011 | Non-stateful resource will be destroyed | Low |  |

## Kubernetes

| ID | Detects | Severity | |
| --- | --- | --- | --- |
| K8S-001 | Privileged container | Critical |  |
| K8S-002 | hostNetwork, hostPID or hostIPC | High |  |
| K8S-003 | hostPath volume (node system paths and docker.sock are critical) | High / Critical |  |
| K8S-004 | Container may run as root | Medium |  |
| K8S-005 | Image uses `latest` or no tag | Medium |  |
| K8S-006 | No memory limit | Low |  |
| K8S-007 | cluster-admin binding or wildcard role | High | approval |
| K8S-008 | Dangerous capabilities added (SYS_ADMIN, NET_ADMIN, ALL, ...) | High |  |
| K8S-009 | Secret values committed in a manifest | High |  |
| K8S-010 | LoadBalancer open to any source | Medium |  |

## GitHub Actions

| ID | Detects | Severity |
| --- | --- | --- |
| GHA-001 | `pull_request_target` workflow checks out the pull request's code | Critical |
| GHA-002 | Untrusted event data expanded inside a `run` script | High |
| GHA-003 | Third-party action pinned to a tag or branch instead of a commit SHA | Medium |
| GHA-004 | `permissions: write-all`, or no permissions block | High / Low |
| GHA-005 | Script downloaded and piped into a shell | Medium |

## Commands

Severity goes up one level when the command mentions `prod`, `production` or `live`.

| ID | Detects | Severity | |
| --- | --- | --- | --- |
| CMD-001 | Terraform destroy | Critical |  |
| CMD-002 | Terraform apply without review | High | approval |
| CMD-003 | Terraform state surgery | High | approval |
| CMD-010 | Kubernetes namespace or cluster-wide delete | Critical |  |
| CMD-011 | Kubernetes delete | Medium | approval |
| CMD-012 | Helm release removal | High | approval |
| CMD-020 | Force push | High | approval |
| CMD-021 | Git history or working tree wipe | Medium | approval |
| CMD-030 | Recursive delete of a root or home path | Critical |  |
| CMD-040 | AWS data deletion | Critical |  |
| CMD-041 | AWS IAM change | High | approval |
| CMD-050 | Destructive SQL | Critical |  |
| CMD-060 | Remote script piped into a shell | High |  |
| CMD-061 | World-writable permissions | Medium |  |
