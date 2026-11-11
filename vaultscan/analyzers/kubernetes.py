"""Checks for Kubernetes manifests (plain YAML, or `helm template` output)."""

from __future__ import annotations

import os
from typing import Any, Iterable, List

import yaml

from vaultscan.models import Finding, Severity

WORKLOAD_KINDS = {"Pod", "Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob"}
DANGEROUS_CAPS = {"ALL", "SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE", "SYS_MODULE"}
SENSITIVE_HOST_PATHS = ("/var/run/docker.sock", "/run/containerd", "/etc", "/root", "/var/lib/kubelet", "/proc")


def _pod_spec(doc: dict) -> dict:
    kind = doc.get("kind")
    spec = doc.get("spec") or {}
    if kind == "Pod":
        return spec
    if kind == "CronJob":
        spec = ((spec.get("jobTemplate") or {}).get("spec")) or {}
    return ((spec.get("template") or {}).get("spec")) or {}


def _name(doc: dict) -> str:
    meta = doc.get("metadata") or {}
    namespace = meta.get("namespace")
    name = meta.get("name", "unnamed")
    return f"{doc.get('kind', '?')}/{namespace}/{name}" if namespace else f"{doc.get('kind', '?')}/{name}"


def _image_is_unpinned(image: str) -> bool:
    if "@sha256:" in image:
        return False
    last = image.rsplit("/", 1)[-1]
    return ":" not in last or last.endswith(":latest")


def analyze_document(doc: Any, source_file: str = "") -> List[Finding]:
    if not isinstance(doc, dict) or "kind" not in doc:
        return []
    findings: List[Finding] = []
    kind = doc["kind"]
    resource = _name(doc)

    def add(rule_id, title, severity, detail, remediation, approval=False):
        findings.append(Finding(rule_id=rule_id, title=title, severity=severity, source="kubernetes",
                                file=source_file, resource=resource, detail=detail,
                                remediation=remediation, needs_approval=approval))

    if kind in WORKLOAD_KINDS:
        spec = _pod_spec(doc)
        for flag in ("hostNetwork", "hostPID", "hostIPC"):
            if spec.get(flag) is True:
                add("K8S-002", f"Pod shares the node's {flag[4:].lower()} namespace", Severity.HIGH,
                    f"{flag}: true lets the pod see or reach node-level resources.",
                    f"Remove {flag} unless this is a node agent that needs it.")
        for volume in spec.get("volumes") or []:
            host_path = ((volume or {}).get("hostPath") or {}).get("path")
            if not host_path:
                continue
            sensitive = host_path == "/" or host_path.startswith(SENSITIVE_HOST_PATHS)
            add("K8S-003", "hostPath volume mounts the node filesystem",
                Severity.CRITICAL if sensitive else Severity.HIGH,
                f"Volume '{volume.get('name')}' mounts {host_path} from the node.",
                "Use a PersistentVolumeClaim, ConfigMap or emptyDir instead of hostPath.")

        pod_ctx = spec.get("securityContext") or {}
        containers = (spec.get("containers") or []) + (spec.get("initContainers") or [])
        for container in containers:
            cname = container.get("name", "?")
            ctx = container.get("securityContext") or {}
            if ctx.get("privileged") is True:
                add("K8S-001", "Privileged container", Severity.CRITICAL,
                    f"Container '{cname}' runs privileged, which is root on the node.",
                    "Drop privileged and add only the specific capabilities needed.")
            added = {str(c).upper() for c in ((ctx.get("capabilities") or {}).get("add") or [])}
            if added & DANGEROUS_CAPS:
                add("K8S-008", "Dangerous Linux capabilities added", Severity.HIGH,
                    f"Container '{cname}' adds {', '.join(sorted(added & DANGEROUS_CAPS))}.",
                    "Remove these capabilities; drop ALL and add back the minimum.")
            non_root = ctx.get("runAsNonRoot", pod_ctx.get("runAsNonRoot"))
            run_as = ctx.get("runAsUser", pod_ctx.get("runAsUser"))
            if run_as == 0 or (non_root is not True and run_as is None):
                add("K8S-004", "Container may run as root", Severity.MEDIUM,
                    f"Container '{cname}' does not set runAsNonRoot or a non-zero runAsUser.",
                    "Set runAsNonRoot: true and allowPrivilegeEscalation: false.")
            image = str(container.get("image", ""))
            if image and _image_is_unpinned(image):
                add("K8S-005", "Image is not pinned to a version", Severity.MEDIUM,
                    f"Container '{cname}' uses '{image}'.",
                    "Pin to an immutable tag or digest so rollouts are reproducible.")
            limits = (container.get("resources") or {}).get("limits") or {}
            if "memory" not in limits:
                add("K8S-006", "No memory limit", Severity.LOW,
                    f"Container '{cname}' has no memory limit and can starve the node.",
                    "Set resources.requests and resources.limits.")

    elif kind in ("ClusterRoleBinding", "RoleBinding"):
        role = (doc.get("roleRef") or {}).get("name")
        if role == "cluster-admin":
            subjects = ", ".join(f"{s.get('kind')}:{s.get('name')}" for s in doc.get("subjects") or [])
            add("K8S-007", "Binding grants cluster-admin", Severity.HIGH,
                f"cluster-admin is bound to {subjects or 'no subjects'}.",
                "Bind a narrower role scoped to the namespaces and verbs required.", approval=True)

    elif kind in ("ClusterRole", "Role"):
        for rule in doc.get("rules") or []:
            if "*" in (rule.get("verbs") or []) and "*" in (rule.get("resources") or []):
                add("K8S-007", "Role allows every verb on every resource", Severity.HIGH,
                    "A rule uses '*' for both verbs and resources.",
                    "List the specific resources and verbs the workload needs.", approval=True)
                break

    elif kind == "Secret":
        if doc.get("data") or doc.get("stringData"):
            add("K8S-009", "Secret values committed in a manifest", Severity.HIGH,
                "Secret data in Git is only base64-encoded, not encrypted.",
                "Use External Secrets, Sealed Secrets or SOPS and rotate these values.")

    elif kind == "Service":
        spec = doc.get("spec") or {}
        if spec.get("type") == "LoadBalancer" and not spec.get("loadBalancerSourceRanges"):
            annotations = (doc.get("metadata") or {}).get("annotations") or {}
            internal = any("internal" in str(k).lower() or str(v).lower() == "internal"
                           for k, v in annotations.items())
            if not internal:
                add("K8S-010", "LoadBalancer is open to any source", Severity.MEDIUM,
                    "No loadBalancerSourceRanges and no internal-scheme annotation.",
                    "Restrict source ranges or expose the service through an ingress.")
    return findings


def analyze_manifest_text(text: str, source_file: str = "") -> List[Finding]:
    findings: List[Finding] = []
    for doc in yaml.safe_load_all(text):
        if isinstance(doc, dict) and doc.get("kind") == "List":
            for item in doc.get("items") or []:
                findings.extend(analyze_document(item, source_file))
        else:
            findings.extend(analyze_document(doc, source_file))
    return findings


def iter_manifest_files(path: str) -> Iterable[str]:
    if os.path.isfile(path):
        yield path
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in {".git", "node_modules", ".terraform", ".github"})
        for name in sorted(files):
            if name.endswith((".yaml", ".yml")):
                yield os.path.join(root, name)


def analyze_manifests(path: str) -> List[Finding]:
    findings: List[Finding] = []
    for file_path in iter_manifest_files(path):
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                findings.extend(analyze_manifest_text(handle.read(), file_path))
        except yaml.YAMLError:
            # Helm templates and other non-plain YAML are skipped, not fatal.
            continue
    return findings
