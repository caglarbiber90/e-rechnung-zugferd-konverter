"""Create the FICTITIOUS sample invoice tests/sample/Musterrechnung.pdf and sample master data.

All names, addresses, tax numbers and the IBAN are invented (the IBAN is a widely used
documentation example with a valid checksum). The layout imitates a typical Word invoice
template (labels like 'Bestellnummer:', 'PSP:', 'Rechnungssumme').

Usage: py -3 tools/make_sample.py
"""
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "sample"

SELLER = {
    "name": "Musterplan Architekten GmbH",
    "street": "Musterstraße 12", "zip": "60311", "city": "Frankfurt am Main", "country": "DE",
    "vat_id": "DE123456789", "email": "rechnung@musterplan.example",
    "tax_no": "012/345/67890", "register_id": "HRB 99999",
    "legal_info": "Musterplan Architekten GmbH, Geschäftsführerin: Erika Mustermann, "
                  "HRB 99999, Amtsgericht Frankfurt am Main",
    "contact": "Max Beispiel", "phone": "+49 69 1234567", "contact_email": "buchhaltung@musterplan.example",
    "iban": "DE02120300000000202051", "bic": "BYLADEM1001",
    "account_name": "Musterplan Architekten GmbH",
}
BUYER = {
    "name": "Beispiel Immobilien AG", "street": "Beispielweg 5", "zip": "60528",
    "city": "Frankfurt am Main", "country": "DE", "vat_id": "",
    "email": "eingangsrechnung@beispiel-immobilien.example", "buyer_reference": "BI-4711",
}


def pdf(path: Path):
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle("Honorarrechnung 2026-0815")
    c.setAuthor("Musterplan Architekten GmbH (fiktiv)")
    W, H = A4
    y = H - 40 * mm
    c.setFont("Helvetica", 7)
    c.drawString(25 * mm, y + 8 * mm, "Musterplan Architekten GmbH · Musterstraße 12 · 60311 Frankfurt am Main")
    c.setFont("Helvetica", 10)
    for line in ["Beispiel Immobilien AG", "z. Hd. Frau Petra Probe", "Beispielweg 5", "", "60528 Frankfurt am Main"]:
        c.drawString(25 * mm, y, line)
        y -= 5 * mm
    r = 135 * mm
    ry = H - 40 * mm
    for line in ["15.11.2026  mb", "Steuer-Nr.: 012/345/67890", "USt-IdNr.: DE123456789",
                 "buchhaltung@musterplan.example", "+49 69 1234567"]:
        c.drawString(r, ry, line)
        ry -= 5 * mm
    y = H - 100 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25 * mm, y, "HONORARRECHNUNG Nr. 2026-0815/01, Projekt: 4711")
    y -= 5.5 * mm
    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, y, "4711-BIA-Umbau-Buero-3OG")
    y -= 11 * mm
    rows = [
        ("Bestellnummer:", "PO-2026-000123"),
        ("Maßnahme:", "Umbau Büroflächen 3. OG"),
        ("PSP:", "PSP-4711-001"),
        ("Leistungsempfänger:", "Beispiel Immobilien AG, Beispielweg 5, 60528 Frankfurt am Main"),
        ("Leistungsabruf:", "Frau Petra Probe, petra.probe@beispiel-immobilien.example"),
        ("Leistungsart:", "Entwurfsplanung LPH 3"),
        ("Abrechnung:", "Architektenleistungen, Euro netto gesamt 2.500,00"),
    ]
    for k, v in rows:
        c.drawString(25 * mm, y, k)
        c.drawString(65 * mm, y, v)
        y -= 6 * mm
    y -= 6 * mm
    c.drawString(25 * mm, y, "Bearbeitungszeitraum:")
    c.drawString(65 * mm, y, "Oktober 2026")
    y -= 12 * mm
    for k, v, bold in [("Rechnungssumme", "2.500,00 €", False), ("Zzgl. 19% MwSt.", "475,00 €", False),
                       ("Rechnungssumme", "2.975,00 €", True)]:
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        c.drawString(25 * mm, y, k)
        c.drawRightString(170 * mm, y, v)
        y -= 6 * mm
    c.setFont("Helvetica", 10)
    y -= 10 * mm
    for line in ["Zahlbar innerhalb von 30 Tagen ohne Abzug auf unser Konto bei der",
                 "Beispielbank Frankfurt", "IBAN: DE02 1203 0000 0000 2020 51", "BIC: BYLADEM1001", "",
                 "Musterplan Architekten GmbH", "Erika Mustermann", "- Geschäftsführerin -"]:
        c.drawString(25 * mm, y, line)
        y -= 5 * mm
    c.setFont("Helvetica", 7)
    c.drawString(25 * mm, 15 * mm, "FIKTIVES BEISPIEL: alle Namen, Nummern und Bankdaten sind erfunden.")
    c.showPage()
    c.save()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pdf(OUT / "Musterrechnung.pdf")
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from erechnung.model import Buyer, Seller
    from erechnung.settings import Settings
    Settings(Seller(**SELLER), [Buyer(**BUYER)], write_xrechnung=True).save(OUT / "stammdaten.json")
    print("written:", OUT)


if __name__ == "__main__":
    main()
