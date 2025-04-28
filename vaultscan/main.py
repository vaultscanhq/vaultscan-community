# VaultScan Community Edition - Developed by PAVAN GAJJALA

# vaultscan/main.py

import argparse
from .scanner import scan_repository, display_findings  # Relative import to avoid module errors
from rich.console import Console  # For beautiful CLI output

console = Console()

def main():
    """
    Main entry point for VaultScan CLI.
    Parses arguments and triggers scanning.
    """
    # Setup argument parser
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

    # Display banner
    console.print(f"\n[bold blue]VaultScan Community Edition v1.1[/bold blue]\n")
    console.print(f"[green]Scanning path:[/green] {args.path}\n")

    # Perform scanning
    findings = scan_repository(args.path, verbose=args.verbose)

    # Display findings
    display_findings(findings)

# Standard Python entry point check
if __name__ == "__main__":
    main()