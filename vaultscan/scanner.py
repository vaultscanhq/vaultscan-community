# VaultScan Community Edition - Developed by PAVAN GAJJALA

# Import necessary modules
import os
import re

# Define secret patterns with their regex and risk level
patterns = {
    "AWS Access Key": (r"AKIA[0-9A-Z]{16}", "High"),
    "Slack Token": (r"xox[baprs]-([0-9a-zA-Z]{10,48})", "High"),
    "Generic API Key": (r"[A-Za-z0-9_\-]{20,50}", "Medium")
}

def load_ignore_list(base_path):
    """
    Load ignore patterns from a .vaultscanignore file if it exists.
    """
    ignore_file = os.path.join(base_path, '.vaultscanignore')
    ignore_list = []

    if os.path.isfile(ignore_file):
        with open(ignore_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    ignore_list.append(line)
    return ignore_list

def should_ignore(file_path, ignore_list):
    """
    Check if the current file should be ignored based on ignore list.
    """
    for pattern in ignore_list:
        if pattern in file_path:
            return True
    return False

def scan_repository(base_path):
    """
    Walk through the directory, scan files, and detect secrets.
    """
    findings = []
    ignore_list = load_ignore_list(base_path)

    for root, _, files in os.walk(base_path):
        for filename in files:
            file_path = os.path.join(root, filename)

            if should_ignore(file_path, ignore_list):
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for idx, line in enumerate(lines, start=1):
                    for name, (regex, risk) in patterns.items():
                        matches = re.findall(regex, line)
                        if matches:
                            for match in matches:
                                findings.append({
                                    "file": file_path,
                                    "line": idx,
                                    "risk": risk,
                                    "secret": redact_secret(match)
                                })
            except Exception as e:
                # Skip unreadable files
                pass

    return findings

def redact_secret(secret):
    """
    Redact (partially mask) secrets before displaying.
    """
    if len(secret) <= 8:
        return "*" * len(secret)
    return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]