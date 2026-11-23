"""Locate bundled data files (KoSIT configuration, icon) from source, pip install or the exe."""
import sys
from pathlib import Path

if hasattr(sys, "_MEIPASS"):
    _DATA = Path(sys._MEIPASS) / "erechnung" / "daten"
else:
    _DATA = Path(__file__).resolve().parent / "daten"


def resource_path(*parts: str) -> Path:
    return _DATA.joinpath(*parts)
