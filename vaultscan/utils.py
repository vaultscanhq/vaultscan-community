# VaultScan Community Edition - Developed by PAVAN GAJJALA
# vaultscan/utils.py

import re

# Tool version
__version__ = "1.1"

# Regular expression patterns for detecting secrets
SECRET_PATTERNS = {    
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "AWS Secret Key": r"(?i)aws_secret_access_key[^a-zA-Z0-9]*[0-9a-zA-Z\/+]{40}",
    "Slack Token": r"xox[baprs]-[0-9a-zA-Z]{10,48}",
    "Stripe Secret Key": r"sk_live_[0-9a-zA-Z]{24,}",
    "GitHub Token": r"ghp_[0-9a-zA-Z]{36}",
    "Private Key": r"-----BEGIN PRIVATE KEY-----",
    "Generic API Key": r"(?i)(api|apikey|token|secret)[^a-zA-Z0-9]*[0-9a-zA-Z]{16,}"
}

# File types we will scan
ALLOWED_EXTENSIONS = (
    '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.tf', '.env', '.sh', '.php', '.java'
)

def find_secrets_in_line(line):
    """
    Check a single line against all secret patterns.
    Returns list of (secret_type, matched_text)
    """
    findings = []
    for secret_type, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, line)
        for match in matches:
            findings.append((secret_type, match))
    return findings

# Developed by Pavan Gajjala – https://github.com/pavangajjala
# Licensed under Apache 2.0. Unauthorized removal of attribution is prohibited.