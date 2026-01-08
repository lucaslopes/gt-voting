"""Main CLI entry point for ranking tools."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cli.rankings_cli import main

if __name__ == "__main__":
    main()
