"""Kept so `python -m vaultscan.main --path DIR` from v1.x still works."""

import sys

from vaultscan.cli import main

if __name__ == "__main__":
    sys.exit(main())
