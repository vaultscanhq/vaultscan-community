# AI review

`--ai` adds a model-written review on top of the rule-based findings.

## How the responsibilities are split

| | Rules | Model |
| --- | --- | --- |
| Finds issues | Yes | No |
| Decides ALLOW / WARN / BLOCK | Yes | No |
| Explains impact for this specific change | No | Yes |
| Can raise the verdict to ASK HUMAN | n/a | Yes |
| Can lower the verdict | n/a | No |

Keeping the decision deterministic means the same change always gets the same
answer, results can be reproduced in an audit, and text hidden in a resource
name or commit message cannot persuade the gate to pass something.

## What is sent to the model

For each finding: rule ID, severity, area, location, title and detail. Secret
values are redacted when a finding is created, so they are not in the prompt.
Source files, plan contents and manifests are not sent.

If you do not want anything to leave your machine, use a local model.

## Providers

| `VAULTSCAN_AI_PROVIDER` | Endpoint | Key |
| --- | --- | --- |
| `ollama` | `http://localhost:11434/v1` | none |
| `anthropic` | `https://api.anthropic.com` | `ANTHROPIC_API_KEY` |
| `openai` | `https://api.openai.com/v1` | `OPENAI_API_KEY` |

`VAULTSCAN_AI_MODEL` is required. `VAULTSCAN_AI_BASE_URL` points the `openai`
provider at any OpenAI-compatible server (vLLM, LM Studio, a gateway), and
`VAULTSCAN_AI_API_KEY` overrides the provider-specific key variable.

## Failure behaviour

If no provider is configured, the model cannot be reached, or the reply is not
valid JSON, VaultScan prints a warning, falls back to a built-in summary and
returns the rule-based verdict. A model outage never changes the exit code.
