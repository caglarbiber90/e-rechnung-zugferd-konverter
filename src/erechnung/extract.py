"""Read invoice fields from the PDF text.

Pluggable: an extractor is a callable (text) -> (Invoice, list[str] notes). The first extractor
whose `matches(text)` returns True is used. Add new templates by appending to EXTRACTORS.
Whatever is extracted is only a proposal; the user always reviews it in the form.
"""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pypdf import PdfReader

from .model import Invoice, Line, Seller, money

MONTHS = {m: i for i, m in enumerate(
    ["januar", "februar", "märz", "april", "mai", "juni", "juli", "august",
     "september", "oktober", "november", "dezember"], 1)}
MONTHS["maerz"] = 3


def pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def de_amount(s: str) -> Decimal | None:
    s = s.strip().replace("€", "").replace("EUR", "").replace(" ", "")
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return money(Decimal(s))
    except InvalidOperation:
        return None


def de_date(s: str) -> date | None:
    try:
        return datetime.strptime(s.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


LABEL_LINE = re.compile(r"^\s*[A-Za-zÄÖÜäöüß][\wÄÖÜäöüß .\-/]{1,30}:\s*$")


def _field(text: str, label: str) -> str:
    """Value after 'Label:' on the same line, or on the next non-empty line
    (PDF text extraction often splits label and value into separate lines)."""
    lines = text.splitlines()
    rx = re.compile(rf"^\s*{label}\s*:[ \t]*(.*?)\s*$", re.I)
    for i, line in enumerate(lines):
        m = rx.match(line)
        if not m:
            continue
        if m.group(1):
            return m.group(1)
        for nxt in lines[i + 1:i + 4]:
            if nxt.strip():
                return "" if LABEL_LINE.match(nxt) else nxt.strip()
        return ""
    return ""


def _period(s: str):
    s = s.strip()
    m = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})\s*(?:-|–|bis)\s*(\d{1,2}\.\d{1,2}\.\d{4})", s)
    if m:
        return de_date(m.group(1)), de_date(m.group(2))
    m = re.search(r"([A-Za-zäÄ]+)\s+(\d{4})", s)
    if m and m.group(1).lower() in MONTHS:
        y, mo = int(m.group(2)), MONTHS[m.group(1).lower()]
        return date(y, mo, 1), date(y, mo, calendar.monthrange(y, mo)[1])
    return None, None


AMOUNT = r"(-?[\d.]+,\d{2})\s*(?:€|EUR)"


class WordHonorarTemplate:
    """Word template 'HONORARRECHNUNG Nr. ..., Projekt: ...' (one service line, one VAT rate)."""

    name = "Honorarrechnung (Word-Vorlage)"

    @staticmethod
    def matches(text: str) -> bool:
        return bool(re.search(r"RECHNUNG\s+Nr\.", text, re.I))

    @staticmethod
    def extract(text: str) -> tuple[Invoice, list[str]]:
        inv, notes = Invoice(), []
        m = re.search(r"RECHNUNG\s+Nr\.\s*(\S+?),?\s+Projekt:\s*(\S+)\s*\n\s*(\S[^\n]*)", text, re.I)
        if m:
            inv.number, inv.project_id, inv.project_name = m.group(1), m.group(2), m.group(3).strip()
        else:
            m = re.search(r"RECHNUNG\s+Nr\.\s*(\S+)", text, re.I)
            inv.number = m.group(1).rstrip(",") if m else ""
        m = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", text)
        inv.issue_date = de_date(m.group(1)) if m else None

        inv.order_ref = _field(text, "Bestellnummer")
        inv.accounting_ref = _field(text, r"(?:PSP|PSP-Element|Kostenstelle)")
        inv.buyer_reference = _field(text, r"(?:Käuferreferenz|Leitweg-ID|Ihr Zeichen)")
        measure = _field(text, "Maßnahme")
        call_off = _field(text, "Leistungsabruf")

        rec = _field(text, "Leistungsempfänger")
        parts = [p.strip() for p in rec.split(",") if p.strip()]
        if parts:
            inv.buyer.name = parts[0]
        if len(parts) >= 3:
            inv.buyer.street = parts[1]
            zm = re.match(r"(\d{5})\s+(.*)", parts[2])
            if zm:
                inv.buyer.zip, inv.buyer.city = zm.groups()
        em = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", call_off)
        if em:
            inv.buyer.email = em.group(0)

        kind = _field(text, "Leistungsart")
        billing = _field(text, "Abrechnung")
        inv.period_start, inv.period_end = _period(_field(text, r"(?:Bearbeitungszeitraum|Leistungszeitraum)"))

        sums = re.findall(rf"Rechnungssumme\s+{AMOUNT}", text)
        if sums:
            inv.net_total = de_amount(sums[0])
            inv.gross_total = de_amount(sums[-1]) if len(sums) > 1 else Decimal(0)
        m = re.search(rf"(\d+(?:,\d+)?)\s*%\s*MwSt\.?\s+{AMOUNT}", text, re.I)
        rate = Decimal("19")
        if m:
            rate = Decimal(m.group(1).replace(",", "."))
            inv.vat_total = de_amount(m.group(2))
        inv.lines = [Line(name=kind or "Leistung", description=billing, quantity=Decimal(1),
                          unit="C62", price=inv.net_total, vat_rate=rate)]

        low = text.lower()
        if "sofort zahlbar" in low:
            inv.payment_terms = "Sofort zahlbar ohne Abzug."
            inv.due_date = inv.issue_date
        else:
            m = re.search(r"innerhalb\s+von\s+(\d+)\s+Tagen", text, re.I)
            if m and inv.issue_date:
                inv.payment_terms = f"Zahlbar innerhalb von {m.group(1)} Tagen ohne Abzug."
                inv.due_date = inv.issue_date + timedelta(days=int(m.group(1)))

        note = []
        if measure:
            note.append(f"Maßnahme: {measure}.")
        if call_off:
            note.append(f"Leistungsabruf: {call_off}.")
        inv.note = " ".join(note)

        return inv, notes


EXTRACTORS = [WordHonorarTemplate]


EMAIL = r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"


def extract_seller(text: str, buyer_email: str = "") -> Seller:
    """Seller data that usually appears on any German invoice (letterhead, footer, bank line)."""
    s = Seller()
    m = re.search(r"Steuer\s*[-–]?\s*Nr\.?\s*:?\s*(\d{2,3}/\d{3}/\d{4,5})", text, re.I)
    if m:
        s.tax_no = m.group(1)
    m = re.search(r"\b(DE\s?\d{3}\s?\d{3}\s?\d{3})\b", text)
    if m:
        s.vat_id = m.group(1).replace(" ", "")
    m = re.search(r"IBAN:?\s*([A-Z]{2}\d{2}(?:\s?[\dA-Z]{4}){3,7}(?:\s?[\dA-Z]{1,3})?)", text)
    if m:
        s.iban = m.group(1).replace(" ", "")
    m = re.search(r"BIC:?\s*([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b", text)
    if m:
        s.bic = m.group(1)
    m = re.search(r"\b(HRB|HRA)\s?(\d{3,6})", text)
    if m:
        s.register_id = f"{m.group(1)} {m.group(2)}"
    for em in re.findall(EMAIL, text):
        if em.lower() != (buyer_email or "").lower():
            s.contact_email = em
            break
    m = re.search(r"(?:Tel\.?|Telefon|Fon)?\s*:?\s*((?:\+|00)49[\d /-]{6,20}\d)", text)
    if m:
        s.phone = " ".join(m.group(1).split())
    # sender line of a DIN 5008 letter: "Name · Street 1 · 12345 City" (also with | or -)
    for line in text.splitlines()[:15]:
        parts = [x.strip() for x in re.split(r"\s[·|•–-]\s", line) if x.strip()]
        if len(parts) >= 3:
            zm = re.match(r"(\d{5})\s+(.+)", parts[-1])
            if zm and re.search(r"\d", parts[-2]):
                s.name, s.street = parts[0], parts[-2]
                s.zip, s.city = zm.groups()
                break
    if s.name:
        s.account_name = s.name
    return s


def extract(path: Path) -> tuple[Invoice, list[str], str]:
    """Returns (invoice proposal, notes for the user, extractor name)."""
    text = pdf_text(path)
    if not text.strip():
        return Invoice(), ["Das PDF enthält keinen lesbaren Text (Scan?). Bitte alle Felder von Hand ausfüllen."], "-"
    for ex in EXTRACTORS:
        if ex.matches(text):
            inv, notes = ex.extract(text)
            inv.seller = extract_seller(text, inv.buyer.email)
            return inv, notes, ex.name
    inv = Invoice()
    inv.seller = extract_seller(text)
    return inv, ["Unbekanntes Rechnungslayout: bitte alle Felder von Hand ausfüllen."], "-"


def iban_in_pdf(path: Path) -> str:
    m = re.search(r"IBAN:?\s*([A-Z]{2}\d{2}[\d ]{10,40})", pdf_text(path))
    return m.group(1).replace(" ", "") if m else ""
