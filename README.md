# VaultScan – Community Edition (v1.2)

<p align="center">
  <img src="vaultscan-logo.png" alt="VaultScan Logo" width="300"/>
</p>

![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)

> ⭐ Star / 👀 Watch / 🍴 Fork this project if you find it useful!

---

👉 Try VaultScan now → [vaultscanhq/vaultscan-community](https://github.com/vaultscanhq/vaultscan-community)

---

## 🚀 About VaultScan

**VaultScan** is a fast, lightweight, privacy-first secrets and credential leak detection tool for code repositories.

Designed for DevOps, Cloud Security, and Development teams to **prevent accidental secret exposures** before they become million-dollar breaches.

Built for local, offline-first scanning with modular design for future cloud expansion.

---

## ✨ What's New in v1.2

- Added --help support for the CLI.
- Improved .vaultscanignore edge case handling.
- Added verbose logging for skipped files and directories.
- Refactored CLI code for better error messages and structure.
- Polished CLI alignment and Rich output formatting.
- Enhanced GitHub Actions support with workflow templates.
- Added support for new secret patterns:  
  GCP API Keys, Azure Keys, JWT Tokens, Database URIs, Basic Auth URLs, and Twilio Auth Tokens

---

## 🎯 Key Features

- 🔍 Scans local code repositories for leaked credentials.
- 🔒 100% Privacy-first: No data leaves your machine.
- 🎨 Beautiful Rich CLI output for better visibility.
- ⚡ Lightweight and fast scanning.
- 📂 Supports ignore patterns via `.vaultscanignore`.
- 🛡️ Risk scoring for better secret prioritization.
- 🧠 High-entropy secret detection (coming soon).
- 🔎 Supports both file and directory input scanning.

---
## 📸 Screenshots

### 🖥️ CLI Output
![CLI Output](.github/assets/cli-output.png)

### ⚙️ GitHub Action Logs
![GitHub Action](.github/assets/github-action.png)

### 🛒 GitHub Marketplace Listing
![Marketplace](.github/assets/marketplace.png)
---

---

## 🔗 Integrations

- 🔧 GitHub Action: [vaultscanhq/vaultscan-action](https://github.com/vaultscanhq/vaultscan-action)  
- 🛒 Marketplace: [VaultScan GitHub Action](https://github.com/marketplace/actions/vaultscan-action)

---

## 🛠️ Installation

Clone the repository:

```bash
git clone https://github.com/vaultscanhq/vaultscan-community.git
cd vaultscan-community
```

Install dependencies:

```bash
pip install -r requirements.txt
```

📄 [Download User Guide (v1.2)](./docs/VaultScan_User_Guide_v1.2.pdf)

---

## 🚀 Usage

```bash
python -m vaultscan.main --path ./path/to/your/codebase
```

Example:

```bash
python -m vaultscan.main --path "D:/simple-java-maven-app-master"
```
---
> **Need GitHub Actions integration?**  
> Use the provided [scan-template.yml](.github/workflows/scan-template.yml) to get started quickly.
---

## 🧪 GitLab CI/CD Integration

To use VaultScan in GitLab CI/CD pipelines, add the following to your `.gitlab-ci.yml`:

```yaml
stages:
  - scan

vaultscan:
  stage: scan
  image: python:3.11
  before_script:
    - pip install rich
    - git clone https://github.com/vaultscanhq/vaultscan-community.git
  script:
    - cd vaultscan-community
    - python -m vaultscan.main --path ../ --verbose
```
---

## 🛡️ Supported Secret Patterns (MVP)

- AWS Access Keys  
- AWS Secret Keys  
- Slack Tokens  
- GitHub Tokens  
- Google Cloud API Keys  
- Azure Keys  
- Stripe Secret Keys  
- Twilio Auth Tokens  
- Private SSH Keys  
- JWT Tokens  
- Database Connection Strings  
- Basic Auth in URLs  
- Generic API Keys

*(The Community Edition now supports 13+ patterns. Pro version will include even more advanced detection.)*

---

## 📂 Example `.vaultscanignore`

Create a `.vaultscanignore` in your repo root to skip scanning certain files or folders:

```
node_modules/
tests/
*.jpg
*.png
*.pdf
```

---

## 🚀 Coming Soon: VaultScan Pro

*VaultScan Pro is the upcoming advanced edition built for teams and enterprises.*

**🔐 Highlights:**
- Visual Web Dashboard
- REST API Access
- Team-based Scan Reports
- GitHub Org-wide Scanning
- Custom Ruleset Engine
- Slack, Jira, Email Alerts
- Scheduled Scans
- Multi-language Support
- Obfuscated Secret Detection
- Severity Scoring in CI/CD
- Exportable Reports

📬 [**Join the Pro Waitlist**](https://docs.google.com/forms/d/e/1FAIpQLSdKnjmm-qyHQoqp6gFu7k0wkNJ1Nt1DIx4BVMYxyWSfWLJWVQ/viewform?usp=header)

---

## 🤝 Community Contributions

This is a community edition. Contributions, suggestions, and improvements are welcome!

---

## 📜 License

Licensed under the [Apache 2.0 License](LICENSE).  
Attribution required. Unauthorized removal of author credit is prohibited.

---

## ✍️ Author
Maintained under: [vaultscanhq](https://github.com/vaultscanhq)

Developed by **Pavan Gajjala**  
*Focused on building privacy-first, security-focused DevOps tools.*

---

## 🚨 Report Misuse

If you find VaultScan being copied or misused without attribution, please report it here: [GitHub Issues](https://github.com/vaultscanhq/vaultscan-community/issues)

---
## VaultScan Pro Roadmap

- Visual Web Dashboard – View scans, risks, and history in one place
- REST API Access – Integrate scan data with your own dashboards/tools
- Team-based Scan Reports – Share and view reports by user or repo group
- GitHub Org-wide Scanning – Scan all repositories in one go
- Custom Ruleset Engine – Define your own regex patterns and ignore logic
- Slack, Jira, Email Alerts – Get notified instantly when secrets are found
- Scheduled Scans – Automate daily/weekly secret detection
- Multi-language Support – Java, Python, JS, and more
- Obfuscated Secret Detection – Catch base64, hex, or string-split secrets
- Severity Scoring in CI/CD – Classify secrets by impact in pipelines
- Exportable Reports – PDF/CSV formats for teams and audits

---

## VaultScan Enterprise Roadmap

- Centralized Dashboard for Teams
- Role-based Access Control (RBAC)
- SAML/SSO Login Support (SAML, LDAP)
- Audit Logs and Compliance Reports
- On-prem Deployment (optional)
- GitHub/GitLab/Bitbucket API Integrations
- AWS/GCP/Kubernetes Secret Scanning
- AST/Static Analysis for Code Logic
- Custom Scanning Rules
- Centralized Policy Enforcement Across Teams
- Data Retention Controls
- Advanced Dashboard Views & Audit Filters
- Full Audit Trail & Compliance Traceability
- SLA-backed Enterprise Support
- Multi-language Support (Java, Python, JS)
- Integration with SIEM/SOC Systems
- IDE Plugin Support (VS Code, JetBrains)

---

# 📢 DISCLAIMER

> This is the **VaultScan – Community Edition (v1.2)** built for open-source collaboration, personal learning, and DevOps community support.  
>  
> **VaultScan Pro and Enterprise Editions** are under private development for future commercial release.

---

## 📦 Project Summary

**vaultscan-community** is a privacy-first secret leak detection tool for DevOps, Cloud, and Security teams.  
Built for scalable, offline-first scanning, future-proofed for multi-cloud and enterprise environments.

**© 2025 [Pavan Gajjala](https://github.com/pavangajjala) - All rights reserved**