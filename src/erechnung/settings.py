"""Master data (seller + known buyers) stored as JSON in %APPDATA%\\E-Rechnung-Konverter."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .model import Buyer, Seller, party_from_dict, party_to_dict


def settings_path() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home() / ".config")
    return base / "E-Rechnung-Konverter" / "stammdaten.json"


class Settings:
    def __init__(self, seller: Seller | None = None, buyers: list[Buyer] | None = None,
                 write_xrechnung: bool = False):
        self.seller = seller or Seller()
        self.buyers = buyers or []
        self.write_xrechnung = write_xrechnung

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        path = path or settings_path()
        if not path.exists():
            return cls()
        d = json.loads(path.read_text(encoding="utf-8"))
        return cls(party_from_dict(Seller, d.get("seller")),
                   [party_from_dict(Buyer, b) for b in d.get("buyers", [])],
                   bool(d.get("write_xrechnung", False)))

    def save(self, path: Path | None = None) -> Path:
        path = path or settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        d = {"seller": party_to_dict(self.seller),
             "buyers": [party_to_dict(b) for b in self.buyers],
             "write_xrechnung": self.write_xrechnung}
        path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def find_buyer(self, name: str) -> Buyer | None:
        key = (name or "").strip().lower()
        return next((b for b in self.buyers if b.name.strip().lower() == key), None) if key else None

    def upsert_buyer(self, buyer: Buyer):
        old = self.find_buyer(buyer.name)
        if old:
            self.buyers[self.buyers.index(old)] = buyer
        else:
            self.buyers.append(buyer)
