# Changelog

## [v2.0.0] - 2026-11-11
VaultScan grows from a secret scanner into a change gate for infrastructure.

### Added
- `vaultscan gate`: one ALLOW / WARN / ASK HUMAN / BLOCK verdict for a change
- Terraform plan review (`vaultscan plan`) for destructive, network and IAM changes
- Kubernetes manifest checks (`vaultscan k8s`)
- GitHub Actions workflow checks (`vaultscan workflows`)
- Command guard for AI agents and scripts (`vaultscan command`)
- Optional AI review (`--ai`) with Anthropic, OpenAI-compatible and Ollama providers
- Policy file `.vaultscan.yml`: thresholds, ignored rules, severity overrides
- JSON, Markdown and SARIF output
- Entropy-based secret detection, rule IDs, inline `# vaultscan:ignore`
- Installable package with a `vaultscan` command, test suite and CI

### Changed
- Secrets are redacted in all output (previously the first 30 characters were printed)
- `.vaultscanignore` uses gitignore-style matching instead of substring matching
- Docker image runs as a non-root user

### Breaking
- The process now exits with code 1 when the verdict is ASK HUMAN or BLOCK.
  v1.x always exited 0, so pipelines that ran the scanner will start failing
  on critical findings. That is the point of a gate, but check before upgrading.

---

## [v1.2] - 2025-04-30
### Added
- `--verbose` flag for detailed CLI output
- Clear logging for ignored files from `.vaultscanignore`

### Improved
- Refactored CLI structure for better readability
- Polished table UI and output formatting

### Fixed
- Edge case handling in `.vaultscanignore`
- CLI help command conflict (`--help`)

---

## [v1.1] - 2025-04-28
### Added
- GitHub Actions support
- Docker support for containerized usage
- `.vaultscanignore` support
- Initial prototype release