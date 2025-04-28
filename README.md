<p align="center">
  <img src="vaultscan-logo.png" alt="VaultScan Logo" width="300"/>
</p>

# VaultScan – Community Edition

![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)

---

## 🚀 About VaultScan

**VaultScan** is a fast, lightweight, privacy-first secrets and credential leak detection tool for code repositories.

Designed for DevOps, Cloud Security, and Development teams to **prevent accidental secret exposures** before they become million-dollar breaches.

Built for local, offline-first scanning with modular design for future cloud expansion.

---

## 🎯 Key Features

- 🔍 Scans local code repositories for leaked credentials.
- 🔒 100% Privacy-first: No data leaves your machine.
- 🎨 Beautiful Rich CLI output for better visibility.
- ⚡ Lightweight and fast scanning.
- 📂 Supports ignore patterns via `.vaultscanignore`.
- 🛡️ Risk scoring for better secret prioritization.

---

## 🛠️ Installation

Clone the repository:

```bash
git clone https://github.com/[your-username]/vaultscan-prototype-community-edition.git
cd vaultscan-prototype-community-edition
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
python -m vaultscan.main --path ./path/to/your/repo
```

Example:

```bash
python -m vaultscan.main --path ./tests/dummy_repo
```

---

## 🛡️ Supported Secret Patterns (MVP)

- AWS Access Keys
- Slack Tokens
- Generic API Keys

*(More patterns can be added easily in future versions.)*

---

## 📂 Example `.vaultscanignore`

Create a `.vaultscanignore` in your repo root to skip scanning certain files or folders:

```
node_modules/
*.jpg
*.png
*.pdf
```

---

## 📜 License

This project is licensed under the [Apache 2.0 License](LICENSE).

---

## ✍️ Author

Developed by **Pavan Gajjala**  
*Focused on building privacy-first, security-focused DevOps tools.*

---

## 🛠️ Future Roadmap (Private Advanced Version)

- GitHub/GitLab/Bitbucket API integrations
- AWS/GCP/Kubernetes secret scanning
- Automated Slack/Email alerts
- Cloud dashboard and scheduling
- SaaS enterprise version

---

# 📢 Note

> This is the **VaultScan – Community Edition (Prototype)** built for learning, personal branding, and open-source contribution.  
>  
> **Advanced Private Enterprise Version** is under development for future commercialization.
=======
# vaultscan-prototype
Privacy-first secret leak detection tool for DevOps and security teams. Built for scalable, offline-first scanning with future enterprise expansion plans.
