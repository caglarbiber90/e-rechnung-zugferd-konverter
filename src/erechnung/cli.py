"""Entry point. Without arguments (or with only a PDF path) the window opens.

Command line (German, for automation and AI agents; output is JSON on stdout):

  e-rechnung auslesen  RECHNUNG.pdf [--stammdaten S.json]            -> proposal as JSON
  e-rechnung erstellen RECHNUNG.pdf --daten DATEN.json [--xrechnung] -> writes the e-invoice
  e-rechnung pruefen   DATEI.xml|DATEI.pdf                           -> KoSIT validation

The review step stays mandatory: `erstellen` only accepts data that has been checked and saved
as JSON; it never converts blindly. Exit code 0 = success, 1 = check failed, 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def _attach_console():
    """The exe is a windowed program; reconnect stdout/stderr to the calling console."""
    if sys.platform != "win32" or (sys.stdout is not None and sys.stdout.isatty()):
        return
    if sys.stdout is not None:  # redirected to a file or pipe: keep it
        return
    try:
        import ctypes
        if ctypes.windll.kernel32.AttachConsole(-1):
            sys.stdout = open("CONOUT$", "w", encoding="utf-8")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8")
    except Exception:
        pass


def _out(obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    if sys.stdout is None:
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # JSON is always UTF-8, also when redirected
    except (AttributeError, ValueError):
        pass
    sys.stdout.write(text)
    sys.stdout.flush()


def _messages(res):
    from .messages_de import explain
    stufe = {"error": "fehler", "warning": "warnung", "information": "information"}
    return [{"stufe": stufe.get(m.level, m.level), "regel": m.code, "erklaerung": explain(m.code, m.text),
             "originaltext": m.text} for m in res.messages]


def cmd_auslesen(a) -> int:
    from .core import propose
    from .model import invoice_to_dict
    from .settings import Settings
    st = Settings.load(Path(a.stammdaten) if a.stammdaten else None)
    inv, notes = propose(Path(a.pdf), st)
    _out({"daten": invoice_to_dict(inv), "hinweise": notes})
    return 0


def cmd_erstellen(a) -> int:
    from .core import finalize
    from .model import invoice_from_dict
    d = json.loads(Path(a.daten).read_text(encoding="utf-8-sig"))
    inv = invoice_from_dict(d.get("daten", d))
    oc = finalize(inv, Path(a.pdf), write_xrechnung=a.xrechnung)
    files = (("e_rechnung", oc.pdf_out), ("pruefbericht", oc.report_out), ("xrechnung", oc.xr_out))
    _out({
        "erfolg": oc.ok,
        "rechenpruefung": oc.problems,
        "kosit": None if oc.result is None else {
            "bestanden": oc.result.accepted, "szenario": oc.result.scenario,
            "meldungen": _messages(oc.result)},
        "xrechnung": None if oc.result_xr is None else {
            "bestanden": oc.result_xr.accepted, "meldungen": _messages(oc.result_xr)},
        "dateien": {k: str(v) for k, v in files if v},
        "hinweise": oc.notes,
    })
    return 0 if oc.ok else 1


def cmd_pruefen(a) -> int:
    from .pdf import read_back
    from .validator import validate
    p = Path(a.datei)
    xml = read_back(p) if p.suffix.lower() == ".pdf" else p.read_bytes()
    res = validate(xml)
    _out({"bestanden": res.accepted, "szenario": res.scenario, "meldungen": _messages(res)})
    return 0 if res.accepted else 1


def cmd_selftest(argv) -> int:
    """Build check: --selftest PDF STAMMDATEN (uses the proposal unchanged, writes selftest.log)."""
    import traceback
    from .core import finalize, propose
    from .settings import Settings
    pdf, st = Path(argv[0]), Settings.load(Path(argv[1]))
    try:
        inv, notes = propose(pdf, st)
        oc = finalize(inv, pdf, write_xrechnung=True)
        lines = notes + oc.problems + [f"{m.code}: {m.text}" for m in (oc.result.errors if oc.result else [])]
        lines.append(f"OK={oc.ok} PDF={oc.pdf_out} REPORT={oc.report_out} XR={oc.xr_out}")
        ok = oc.ok
    except Exception:
        lines, ok = [traceback.format_exc()], False
    (pdf.parent / "selftest.log").write_text("\n".join(lines), encoding="utf-8")
    return 0 if ok else 1


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="e-rechnung",
        description="PDF-Rechnung in eine E-Rechnung (ZUGFeRD 2.x, Profil EN 16931) umwandeln und nach "
                    "dem KoSIT-Regelwerk prüfen. Ohne Argumente öffnet sich das Programmfenster.")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="befehl", required=True, metavar="BEFEHL")
    p = sub.add_parser("auslesen", help="Felder aus einer PDF-Rechnung lesen (Vorschlag als JSON)")
    p.add_argument("pdf")
    p.add_argument("--stammdaten", help="JSON mit Rechnungssteller und Kunden (Standard: %%APPDATA%%)")
    p.set_defaults(fn=cmd_auslesen)
    p = sub.add_parser("erstellen", help="E-Rechnung aus geprüften Daten (JSON) erzeugen")
    p.add_argument("pdf")
    p.add_argument("--daten", required=True, help="geprüfte Rechnungsdaten (Ausgabe von 'auslesen')")
    p.add_argument("--xrechnung", action="store_true", help="zusätzlich XRechnung-XML schreiben")
    p.set_defaults(fn=cmd_erstellen)
    p = sub.add_parser("pruefen", help="XML oder ZUGFeRD-PDF nach dem KoSIT-Regelwerk prüfen")
    p.add_argument("datei")
    p.set_defaults(fn=cmd_pruefen)
    return ap


def main():
    argv = sys.argv[1:]
    if argv:  # command line use: no start-up picture
        try:
            import pyi_splash
            pyi_splash.close()
        except Exception:
            pass
    if argv[:1] == ["--selftest"]:
        sys.exit(cmd_selftest(argv[1:]))
    if not argv or (len(argv) == 1 and argv[0].lower().endswith(".pdf")):
        from .gui import main as gui_main
        gui_main()
        return
    _attach_console()
    a = parser().parse_args(argv)
    try:
        sys.exit(a.fn(a))
    except FileNotFoundError as e:
        _out({"erfolg": False, "fehler": f"Datei nicht gefunden: {e.filename}"})
        sys.exit(2)
