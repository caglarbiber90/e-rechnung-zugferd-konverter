"""Locate bundled files both from source and from a PyInstaller one-file exe."""
import sys
from pathlib import Path

_FROZEN = hasattr(sys, "_MEIPASS")
_ROOT = Path(sys._MEIPASS) if _FROZEN else Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    return _ROOT.joinpath("resources", *parts)


def branding_path(*parts: str) -> Path:
    """Optional office branding (logo, icon, wordmark); missing in the public repo."""
    return _ROOT.joinpath("branding", *parts)
