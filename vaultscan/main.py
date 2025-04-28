# VaultScan Community Edition - Developed by PAVAN GAJJALA

# vaultscan/main.py

import argparse
from vaultscan.scanner import scan_repository, display_findings
from rich.console import Console

console = Console()

def main():
    """
    Main entry point for VaultScan CLI.
    Parses arguments and triggers scanning.
    """
    parser = argparse.ArgumentParser(
        description="VaultScan Community Edition v1.1 – Privacy-first secrets detection tool"
    )
    parser.add_argument(
        "--path", required=True,
        help="Path to the code repository or folder to scan"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose mode for detailed scanning logs"
    )
    args = parser.parse_args()

    console.print(f"\n[bold blue]VaultScan Community Edition v1.1[/bold blue]\n")
    console.print(f"[green]Scanning path:[/green] {args.path}\n")

    # Perform scanning
    findings = scan_repository(args.path, verbose=args.verbose)

    # Display findings
    display_findings(findings)

if __name__ == "__main__":
    main()