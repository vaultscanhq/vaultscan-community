# VaultScan Community Edition - Developed by PAVAN GAJJALA

# vaultscan/utils.py

import re

# Tool version
__version__ = "1.1"

# Regular expression patterns for detecting secrets
SECRET_PATTERNS = {
    "AWS Access Key": r'AKIA[0-9A-Z]{16}',
    "Slack Token": r'xox[baprs]-[0-9a-zA-Z]{10,48}',
    "Generic API Key": r'(?i)(api_key|apikey|api-key|secret)[\'"\s:=]+[0-9a-zA-Z]{16,45}',
}

# File types we will scan
ALLOWED_EXTENSIONS = (
    '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.tf', '.env', '.sh', '.php'
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