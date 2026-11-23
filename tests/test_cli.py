import json
import shutil
import subprocess
import sys
from pathlib import Path

from helpers import SAMPLE

SRC = Path(__file__).resolve().parents[1] / "src"


def run(*args):
    r = subprocess.run([sys.executable, "-m", "erechnung", *map(str, args)], cwd=SRC,
                       capture_output=True)
    return r.returncode, json.loads(r.stdout.decode("utf-8"))


def test_cli_roundtrip(tmp_path):
    pdf = tmp_path / "Musterrechnung.pdf"
    shutil.copy(SAMPLE / "Musterrechnung.pdf", pdf)
    code, prop = run("auslesen", pdf, "--stammdaten", SAMPLE / "stammdaten.json")
    assert code == 0 and prop["daten"]["rechnungsnummer"] == "2026-0815/01"
    assert prop["daten"]["bruttosumme"] == "2975.00"
    daten = tmp_path / "daten.json"
    daten.write_text(json.dumps(prop, ensure_ascii=False), encoding="utf-8")
    code, res = run("erstellen", pdf, "--daten", daten, "--xrechnung")
    assert code == 0 and res["erfolg"] and res["kosit"]["bestanden"] and res["xrechnung"]["bestanden"]
    code, chk = run("pruefen", res["dateien"]["e_rechnung"])
    assert code == 0 and chk["bestanden"]


def test_cli_rejects_wrong_total(tmp_path):
    pdf = tmp_path / "Musterrechnung.pdf"
    shutil.copy(SAMPLE / "Musterrechnung.pdf", pdf)
    _, prop = run("auslesen", pdf, "--stammdaten", SAMPLE / "stammdaten.json")
    prop["daten"]["bruttosumme"] = "2985.00"
    daten = tmp_path / "daten.json"
    daten.write_text(json.dumps(prop, ensure_ascii=False), encoding="utf-8")
    code, res = run("erstellen", pdf, "--daten", daten)
    assert code == 1 and not res["erfolg"] and res["rechenpruefung"]
    assert not (tmp_path / "Musterrechnung_E-Rechnung.pdf").exists()
