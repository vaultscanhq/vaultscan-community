# VaultScan Community Edition - Developed by PAVAN GAJJALA

# vaultscan/main.py

import argparse
import os
from vaultscan.scanner import scan_repository, display_findings

def main():
    # Setup CLI argument parser
    parser = argparse.ArgumentParser(
        description="VaultScan – Secrets Detection Tool for DevOps and Security Teams"
    )

    # Optional path argument (defaults to current directory)
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to scan (default: current directory)"
    )

    # Verbose flag for extra output
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    # Parse arguments from the command line
    args = parser.parse_args()

    # Validate path existence
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.")
        exit(1)

    # Validate that it's a directory
    if not os.path.isdir(args.path):
        print(f"Error: Path '{args.path}' is not a directory.")
        exit(1)

    try:
        # Run VaultScan with verbose control and collect results
        findings = scan_repository(args.path, args.verbose)

        # Display results (findings only, verbose handled inside scan_repository)
        display_findings(findings)

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()