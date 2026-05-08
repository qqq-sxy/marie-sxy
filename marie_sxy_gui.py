"""Standalone entry point for flet pack / PyInstaller."""
import sys
from pathlib import Path

# Ensure src/ is on the path when running as a frozen bundle
_here = Path(__file__).parent
_src = _here / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from marie_sxy.gui.app import run_app  # noqa: E402

if __name__ == "__main__":
    run_app()
