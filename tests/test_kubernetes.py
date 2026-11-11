import os

from vaultscan.analyzers.kubernetes import analyze_manifest_text, analyze_manifests
from vaultscan.engine import decide
from vaultscan.models import Severity, Verdict

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_risky_manifest():
    findings = analyze_manifests(os.path.join(FIXTURES, "k8s_risky.yaml"))
    rules = {f.rule_id for f in findings}
    assert {"K8S-001", "K8S-002", "K8S-003", "K8S-005", "K8S-007", "K8S-008"} <= rules
    docker_sock = next(f for f in findings if f.rule_id == "K8S-003")
    assert docker_sock.severity is Severity.CRITICAL
    assert docker_sock.resource == "Deployment/platform/log-shipper"
    assert decide(findings).verdict is Verdict.BLOCK


def test_hardened_manifest_is_clean():
    findings = analyze_manifests(os.path.join(FIXTURES, "k8s_safe.yaml"))
    assert findings == []


def test_cronjob_pod_spec_is_found():
    text = """
apiVersion: batch/v1
kind: CronJob
metadata: {name: backup}
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres
              securityContext: {privileged: true}
"""
    rules = {f.rule_id for f in analyze_manifest_text(text)}
    assert {"K8S-001", "K8S-005"} <= rules


def test_secret_and_open_loadbalancer():
    text = """
apiVersion: v1
kind: Secret
metadata: {name: db}
stringData: {password: hunter2}
---
apiVersion: v1
kind: Service
metadata: {name: web}
spec: {type: LoadBalancer, ports: [{port: 443}]}
"""
    rules = {f.rule_id for f in analyze_manifest_text(text)}
    assert rules == {"K8S-009", "K8S-010"}


def test_digest_pinned_image_is_accepted():
    text = """
apiVersion: v1
kind: Pod
metadata: {name: p}
spec:
  securityContext: {runAsNonRoot: true}
  containers:
    - name: c
      image: registry.local:5000/team/app@sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
      resources: {limits: {memory: 64Mi}}
"""
    assert analyze_manifest_text(text) == []
