"""GUI-independent workflow: propose -> (user review) -> check -> build -> validate -> embed."""
from __future__ import annotations

import copy
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import pdf as pdfmod
from .checks import check
from .cii import GUIDELINE_EN16931, GUIDELINE_XRECHNUNG, build_cii
from .extract import extract, iban_in_pdf
from .model import Invoice
from .settings import Settings
from .validator import Result, report_html, validate


def propose(pdf_path: Path, settings: Settings) -> tuple[Invoice, list[str]]:
    inv, notes, ex_name = extract(pdf_path)
    notes = [f"Erkanntes Layout: {ex_name}"] + notes
    inv.seller = copy.deepcopy(settings.seller)
    known = settings.find_buyer(inv.buyer.name)
    if known:
        for f in ("street", "zip", "city", "country", "vat_id", "email"):
            if not getattr(inv.buyer, f) or f == "email" and known.email:
                setattr(inv.buyer, f, getattr(known, f))
        inv.buyer.buyer_reference = known.buyer_reference
        if not inv.buyer_reference:
            inv.buyer_reference = known.buyer_reference
        notes.append(f"Kundenstammdaten für '{known.name}' übernommen.")
    elif inv.buyer.name:
        notes.append(f"Kunde '{inv.buyer.name}' ist noch nicht in den Stammdaten.")
    if not inv.buyer_reference:
        notes.append("Käuferreferenz (Leitweg-ID oder Bestellzeichen des Kunden) weder im PDF noch in den "
                     "Kundenstammdaten gefunden. Für ZUGFeRD freiwillig, für XRechnung Pflicht.")
    pdf_iban = iban_in_pdf(pdf_path)
    if pdf_iban and settings.seller.iban and pdf_iban != settings.seller.iban.replace(" ", ""):
        notes.append("ACHTUNG: Die IBAN im PDF weicht von der IBAN in den Stammdaten ab.")
    part = pdfmod.pdfa_part(pdf_path)
    if not part:
        notes.append("Das PDF ist kein PDF/A. Empfehlung: in Word 'Speichern unter > PDF > Optionen > "
                     "PDF/A-kompatibel' wählen und dieses PDF verwenden.")
    elif not part.startswith("3"):
        notes.append(f"Das PDF ist PDF/A-{part}. Für ZUGFeRD wird PDF/A-3 erwartet; die Ausgabe wird als "
                     "PDF/A-3 gekennzeichnet, die Konformität wird aber nicht geprüft.")
    return inv, notes


@dataclass
class Outcome:
    ok: bool
    problems: list[str] = field(default_factory=list)
    result: Result | None = None
    result_xr: Result | None = None
    pdf_out: Path | None = None
    report_out: Path | None = None
    xr_out: Path | None = None
    notes: list[str] = field(default_factory=list)


def output_paths(pdf_path: Path) -> tuple[Path, Path, Path]:
    stem = pdf_path.with_suffix("")
    return (Path(f"{stem}_E-Rechnung.pdf"), Path(f"{stem}_E-Rechnung_Pruefbericht.html"),
            Path(f"{stem}_XRechnung.xml"))


def finalize(inv: Invoice, pdf_path: Path, write_xrechnung: bool = False) -> Outcome:
    problems = check(inv)
    if problems:
        return Outcome(False, problems)
    xml = build_cii(inv, GUIDELINE_EN16931)
    res = validate(xml)
    out_pdf, out_rep, out_xr = output_paths(pdf_path)
    if not res.accepted:
        return Outcome(False, [], res)
    oc = Outcome(True, [], res)
    if write_xrechnung:
        xr = build_cii(inv, GUIDELINE_XRECHNUNG)
        oc.result_xr = validate(xr)
        if oc.result_xr.accepted:
            out_xr.write_bytes(xr)
            oc.xr_out = out_xr
        else:
            oc.notes.append("XRechnung-Datei wurde NICHT geschrieben (Prüfung nicht bestanden, siehe Bericht). "
                            "Die ZUGFeRD-Rechnung ist davon nicht betroffen.")
    fd, tmp = tempfile.mkstemp(suffix=".pdf", dir=str(out_pdf.parent))
    os.close(fd)
    try:
        pdfmod.embed(pdf_path, xml, Path(tmp))
        if pdfmod.read_back(Path(tmp)) != xml:
            raise RuntimeError("Rücklesetest fehlgeschlagen: eingebettetes XML weicht ab.")
        os.replace(tmp, out_pdf)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    oc.pdf_out = out_pdf
    if not pdfmod.pdfa_part(pdf_path):
        oc.notes.append("Hinweis PDF/A: Das Ausgangs-PDF war kein PDF/A. Die Ausgabe enthält die ZUGFeRD-"
                        "Struktur und trägt die PDF/A-3-Kennzeichnung, ist aber NICHT als PDF/A geprüft. "
                        "Das eingebettete XML ist davon nicht betroffen und gültig.")
    sections = [(f"ZUGFeRD / Factur-X EN 16931 ({out_pdf.name})", res)]
    if oc.result_xr is not None:
        sections.append((f"XRechnung 3.0 ({out_xr.name})", oc.result_xr))
    html = report_html(sections, oc.notes)
    out_rep.write_text(html, encoding="utf-8")
    oc.report_out = out_rep
    return oc
