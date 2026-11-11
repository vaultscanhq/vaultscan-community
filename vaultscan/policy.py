"""Policy file handling (.vaultscan.yml).

The policy lets a team tune the gate without forking the rules:

    block_on: critical          # severity that fails the gate
    warn_on: medium             # severity that produces a warning
    ignore_rules: [K8S-006]     # switch individual rules off
    severity_overrides:
      TF-005: critical          # treat a rule as more (or less) serious
    max_deletes: 5              # bulk-delete threshold for Terraform plans
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List

import yaml

from vaultscan.models import Severity

DEFAULT_POLICY_FILE = ".vaultscan.yml"


@dataclass
class Policy:
    block_on: Severity = Severity.CRITICAL
    warn_on: Severity = Severity.MEDIUM
    ignore_rules: List[str] = field(default_factory=list)
    severity_overrides: Dict[str, Severity] = field(default_factory=dict)
    max_deletes: int = 5

    @classmethod
    def from_dict(cls, raw: dict) -> "Policy":
        policy = cls()
        if "block_on" in raw:
            policy.block_on = Severity.parse(str(raw["block_on"]))
        if "warn_on" in raw:
            policy.warn_on = Severity.parse(str(raw["warn_on"]))
        if policy.warn_on > policy.block_on:
            raise ValueError("warn_on cannot be stricter than block_on")
        policy.ignore_rules = [str(r).upper() for r in raw.get("ignore_rules") or []]
        policy.severity_overrides = {
            str(rule).upper(): Severity.parse(str(level))
            for rule, level in (raw.get("severity_overrides") or {}).items()
        }
        policy.max_deletes = int(raw.get("max_deletes", policy.max_deletes))
        return policy

    @classmethod
    def load(cls, path: str | None = None, search_dir: str = ".") -> "Policy":
        """Load an explicit policy file, or .vaultscan.yml if one exists."""
        if path is None:
            candidate = os.path.join(search_dir, DEFAULT_POLICY_FILE)
            if not os.path.isfile(candidate):
                return cls()
            path = candidate
        with open(path, "r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: policy must be a mapping")
        return cls.from_dict(raw)
