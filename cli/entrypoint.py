#!/usr/bin/env python3
import sys
from pathlib import Path

# Ensure the directory containing git_check is on sys.path
cli_dir = Path(__file__).resolve().parent
if str(cli_dir) not in sys.path:
    sys.path.insert(0, str(cli_dir))

from git_check.main import cli

if __name__ == "__main__":
    cli()
