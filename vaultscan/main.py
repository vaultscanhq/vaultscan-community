# VaultScan Community Edition - Developed by PAVAN GAJJALA

# Importing required modules
import argparse
from vaultscan.scanner import scan_repository
from rich.table import Table
from rich.console import Console

def main():
    # Setup command line argument parser
    parser = argparse.ArgumentParser(description="VaultScan - Secrets Detection Tool")
    parser.add_argument("--path", required=True, help="Path to the repository/folder to scan")
    args = parser.parse_args()

    # Initialize rich console
    console = Console()

    # Call the scanner function and get findings
    findings = scan_repository(args.path)

    if findings:
        # Create a rich table
        table = Table(title="VaultScan - Secrets Found", show_lines=True)

        # Define table columns
        table.add_column("File", style="cyan", overflow="fold")
        table.add_column("Line", style="magenta")
        table.add_column("Risk", style="red")
        table.add_column("Secret (Masked)", style="yellow")

        # Add findings to the table
        for finding in findings:
            table.add_row(
                finding["file"],
                str(finding["line"]),
                finding["risk"],
                finding["secret"]
            )

        # Print the table
        console.print(table)

    else:
        console.print("\n[+] No secrets found! All clear.\n", style="bold green")

# Entry point of the script
if __name__ == "__main__":
    main()