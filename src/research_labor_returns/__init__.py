"""Public-data pipeline for research labor returns."""

import os
from pathlib import Path

# Avoid writing library caches to a user's home directory on managed systems.
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".cache/matplotlib")
)

__version__ = "0.1.0"
