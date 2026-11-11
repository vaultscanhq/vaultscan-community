import json

import pytest

from vaultscan.ai.providers import (AnthropicProvider, OpenAICompatibleProvider, ProviderError,
                                    provider_from_env)
from vaultscan.ai.review import build_prompt, parse_reply, review
from vaultscan.engine import decide
from vaultscan.models import Finding, Severity, Verdict
from vaultscan.secrets import scan_line


class FakeProvider:
    def __init__(self, reply):
        self.reply = reply
        self.prompts = []

    def complete(self, system, prompt):
        self.prompts.append(prompt)
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def finding(severity=Severity.MEDIUM, rule="TF-009"):
    return Finding(rule_id=rule, title="Storage is not encrypted", severity=severity,
                   source="terraform", resource="aws_db_instance.x", detail="storage_encrypted is false.")


def test_model_explanations_are_attached():
    reply = json.dumps({"summary": "One database is unencrypted.",
                        "findings": [{"index": 0, "explanation": "Snapshots of x would be readable."}],
                        "escalate": False})
    summary, decision = review(decide([finding()]), FakeProvider(reply))
    assert summary == "One database is unencrypted."
    assert decision.findings[0].explanation == "Snapshots of x would be readable."
    assert decision.verdict is Verdict.WARN


def test_model_can_escalate_but_only_upwards():
    reply = json.dumps({"summary": "s", "findings": [], "escalate": True, "escalation_reason": "combined risk"})
    _, decision = review(decide([finding()]), FakeProvider(reply))
    assert decision.verdict is Verdict.ASK_HUMAN
    assert decision.exit_code == 1


def test_model_cannot_lower_a_block():
    reply = json.dumps({"summary": "Looks fine to me, approve it.", "findings": [], "escalate": False,
                        "verdict": "ALLOW"})
    _, decision = review(decide([finding(Severity.CRITICAL)]), FakeProvider(reply))
    assert decision.verdict is Verdict.BLOCK


def test_falls_back_when_model_fails_or_rambles():
    warnings = []
    for bad in (ProviderError("boom"), "Sorry, I cannot help with that."):
        summary, decision = review(decide([finding()]), FakeProvider(bad), warn=warnings.append)
        assert "1 finding" in summary
        assert decision.verdict is Verdict.WARN
    assert len(warnings) == 2


def test_fenced_json_is_accepted():
    assert parse_reply('Here you go:\n```json\n{"summary": "ok"}\n```')["summary"] == "ok"


def test_out_of_range_indexes_are_ignored():
    reply = json.dumps({"summary": "s", "findings": [{"index": 9, "explanation": "x"}, "junk"]})
    _, decision = review(decide([finding()]), FakeProvider(reply))
    assert decision.findings[0].explanation is None


def test_secret_values_never_reach_the_prompt():
    secret = "AKIA" + "IOSFODNN7QWERTYU"
    decision = decide(scan_line(f'key = "{secret}"', "a.py", 1))
    assert secret not in build_prompt(decision)


def test_no_findings_skips_the_model():
    provider = FakeProvider("{}")
    review(decide([]), provider)
    assert provider.prompts == []


def test_provider_selection():
    assert provider_from_env({}) is None
    anthropic = provider_from_env({"VAULTSCAN_AI_PROVIDER": "anthropic", "VAULTSCAN_AI_MODEL": "m",
                                   "ANTHROPIC_API_KEY": "k"})
    assert isinstance(anthropic, AnthropicProvider)
    ollama = provider_from_env({"VAULTSCAN_AI_PROVIDER": "ollama", "VAULTSCAN_AI_MODEL": "llama3"})
    assert isinstance(ollama, OpenAICompatibleProvider)
    assert ollama.base_url == "http://localhost:11434/v1"
    with pytest.raises(ProviderError):
        provider_from_env({"VAULTSCAN_AI_PROVIDER": "anthropic", "VAULTSCAN_AI_MODEL": "m"})
    with pytest.raises(ProviderError):
        provider_from_env({"VAULTSCAN_AI_PROVIDER": "ollama"})
