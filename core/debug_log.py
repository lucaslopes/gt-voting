"""Optional destination for temporary development diagnostics."""

from io import StringIO
import os
from pathlib import Path
from typing import TextIO


def open_debug_log() -> TextIO:
    """Open the configured diagnostic log, or discard entries by default.

    ``GTIV_DEBUG_LOG`` can point to a writable file when local diagnostics are
    needed. The default avoids writing to a developer-specific checkout path.
    """
    destination = os.environ.get("GTIV_DEBUG_LOG")
    if not destination:
        return StringIO()

    path = Path(destination).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("a", encoding="utf-8")
