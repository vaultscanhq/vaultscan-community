import os
from rich.console import Console
from rich.table import Table
from vaultscan.utils import find_secrets_in_line, ALLOWED_EXTENSIONS

console = Console()

def load_ignore_patterns(base_path):
    """
    Load ignore patterns from .vaultscanignore file if present.
    """
    ignore_file = os.path.join(base_path, ".vaultscanignore")
    patterns = []
    if os.path.isfile(ignore_file):
        with open(ignore_file, 'r') as f:
            for line in f:
                cleaned = line.strip()
                if cleaned and not cleaned.startswith('#'):
                    patterns.append(cleaned)
    return patterns

def is_ignored(file_path, ignore_patterns):
    """
    Check if a file path matches any ignore pattern.
    Supports wildcards and folder ignoring.
    """
    for pattern in ignore_patterns:
        if pattern.startswith("*") and file_path.endswith(pattern[1:]):
            return True
        elif pattern.endswith("/") and f"/{pattern[:-1]}/" in file_path.replace("\\", "/"):
            return True
        elif pattern in file_path:
            return True
    return False

def scan_repository(base_path, verbose=False):
    """
    Recursively scan a repository or folder for secrets.
    """
    findings = []
    ignore_patterns = load_ignore_patterns(base_path)

    for root, dirs, files in os.walk(base_path):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_path)

            if is_ignored(rel_path, ignore_patterns):
                if verbose:
                    console.print(f"[yellow]Skipping (ignored)[/yellow]: {rel_path}")
                continue

            if not file.lower().endswith(ALLOWED_EXTENSIONS):
                continue

            if verbose:
                console.print(f"[cyan]Scanning[/cyan]: {rel_path}")

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, start=1):
                        secrets = find_secrets_in_line(line)
                        for secret_type, secret_value in secrets:
                            findings.append({
                                "file": rel_path,
                                "line": i,
                                "risk": secret_type,
                                "secret": secret_value
                            })
            except Exception as e:
                if verbose:
                    console.print(f"[red]Failed to read[/red]: {rel_path} ({str(e)})")

    return findings

def display_findings(findings):
    """
    Display detected secrets in a table using Rich.
    """
    if not findings:
        console.print("\n[bold green]No secrets found. All clear![/bold green]\n")
        return

    table = Table(title="Secrets Detected", show_lines=True)
    table.add_column("File", style="magenta")
    table.add_column("Line", style="cyan")
    table.add_column("Risk Type", style="red")
    table.add_column("Secret Snippet", style="yellow")

    for finding in findings:
        table.add_row(
            finding['file'],
            str(finding['line']),
            finding['risk'],
            finding['secret'][:30] + ("..." if len(finding['secret']) > 30 else "")
        )

    console.print(table)