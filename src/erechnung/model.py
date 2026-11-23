"""Invoice data model. All amounts are Decimal, dates are datetime.date."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def money(v) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class Party:
    name: str = ""
    street: str = ""
    zip: str = ""
    city: str = ""
    country: str = "DE"
    vat_id: str = ""
    email: str = ""          # electronic address (BT-34 / BT-49)


@dataclass
class Seller(Party):
    tax_no: str = ""          # Steuernummer (BT-32)
    register_id: str = ""     # e.g. "HRB 12345" (BT-30)
    legal_info: str = ""      # free text: court, managing director (BT-33 as REG note)
    contact: str = ""         # BR-DE-2
    phone: str = ""
    contact_email: str = ""
    iban: str = ""
    bic: str = ""
    account_name: str = ""


@dataclass
class Buyer(Party):
    buyer_reference: str = ""  # BT-10, default for this buyer


@dataclass
class Line:
    name: str = ""
    description: str = ""
    quantity: Decimal = Decimal("1")
    unit: str = "C62"          # C62 = piece / one; HUR = hour; LS = lump sum
    price: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("19")

    @property
    def net(self) -> Decimal:
        return money(self.quantity * self.price)


@dataclass
class Invoice:
    number: str = ""
    issue_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    due_date: date | None = None
    type_code: str = "380"     # 380 invoice, 381 credit note, 875/876/877 partial/final construction
    currency: str = "EUR"
    buyer_reference: str = ""  # BT-10
    order_ref: str = ""        # BT-13
    accounting_ref: str = ""   # BT-19 (PSP / cost centre)
    project_id: str = ""       # BT-11
    project_name: str = ""
    note: str = ""             # BT-22
    payment_terms: str = ""    # BT-20
    seller: Seller = field(default_factory=Seller)
    buyer: Buyer = field(default_factory=Buyer)
    lines: list[Line] = field(default_factory=list)
    # totals as printed on the PDF (checked against the computed ones)
    net_total: Decimal = Decimal("0")
    vat_total: Decimal = Decimal("0")
    gross_total: Decimal = Decimal("0")


# German keys for JSON files (master data, CLI input/output). Internal names stay English.
PARTY_DE = {
    "name": "name", "street": "strasse", "zip": "plz", "city": "ort", "country": "land",
    "vat_id": "ust_idnr", "email": "e_rechnung_email", "tax_no": "steuernummer",
    "register_id": "handelsregister", "legal_info": "rechtliche_angaben", "contact": "ansprechpartner",
    "phone": "telefon", "contact_email": "ansprechpartner_email", "iban": "iban", "bic": "bic",
    "account_name": "kontoinhaber", "buyer_reference": "kaeuferreferenz",
}
INVOICE_DE = {
    "number": "rechnungsnummer", "issue_date": "rechnungsdatum", "period_start": "leistungszeitraum_von",
    "period_end": "leistungszeitraum_bis", "due_date": "faellig_am", "type_code": "rechnungsart_code",
    "currency": "waehrung", "buyer_reference": "kaeuferreferenz", "order_ref": "bestellnummer",
    "accounting_ref": "kostenstelle_psp", "project_id": "projektnummer", "project_name": "projektbezeichnung",
    "note": "bemerkung", "payment_terms": "zahlungsbedingung", "seller": "rechnungssteller",
    "buyer": "rechnungsempfaenger", "lines": "positionen", "net_total": "nettosumme",
    "vat_total": "umsatzsteuer", "gross_total": "bruttosumme",
}
LINE_DE = {"name": "bezeichnung", "description": "beschreibung", "quantity": "menge", "unit": "einheit",
           "price": "einzelpreis_netto", "vat_rate": "ust_satz"}


def _get(d: dict, en: str, mapping: dict, default=None):
    """Read a value by its German key, falling back to the English one (older files)."""
    if mapping.get(en, en) in d:
        return d[mapping.get(en, en)]
    return d.get(en, default)


def party_to_dict(p) -> dict:
    return {PARTY_DE[f.name]: getattr(p, f.name) for f in fields(p)}


def party_from_dict(cls, d: dict):
    d = d or {}
    vals = {}
    for f in fields(cls):
        v = _get(d, f.name, PARTY_DE)
        if v is not None:
            vals[f.name] = str(v)
    return cls(**vals)


def _plain(v):
    if isinstance(v, Decimal):
        return format(v, "f")
    if isinstance(v, date):
        return v.isoformat()
    return v


def invoice_to_dict(inv: Invoice) -> dict:
    d = {INVOICE_DE[f.name]: _plain(getattr(inv, f.name)) for f in fields(Invoice)
         if f.name not in ("seller", "buyer", "lines")}
    d[INVOICE_DE["seller"]] = party_to_dict(inv.seller)
    d[INVOICE_DE["buyer"]] = party_to_dict(inv.buyer)
    d[INVOICE_DE["lines"]] = [{LINE_DE[f.name]: _plain(getattr(ln, f.name)) for f in fields(Line)}
                              for ln in inv.lines]
    return d


def invoice_from_dict(d: dict) -> Invoice:
    def dec(v, default="0"):
        return Decimal(str(v if v not in (None, "") else default))

    inv = Invoice()
    for f in fields(Invoice):
        if f.name in ("seller", "buyer", "lines"):
            continue
        v = _get(d, f.name, INVOICE_DE)
        if f.name in ("issue_date", "period_start", "period_end", "due_date"):
            v = date.fromisoformat(v) if v else None
        elif f.name in ("net_total", "vat_total", "gross_total"):
            v = dec(v)
        elif v is None:
            continue
        setattr(inv, f.name, v)
    inv.seller = party_from_dict(Seller, _get(d, "seller", INVOICE_DE))
    inv.buyer = party_from_dict(Buyer, _get(d, "buyer", INVOICE_DE))
    inv.lines = [Line(name=_get(ln, "name", LINE_DE, ""), description=_get(ln, "description", LINE_DE, ""),
                      quantity=dec(_get(ln, "quantity", LINE_DE), "1"),
                      unit=_get(ln, "unit", LINE_DE) or "C62",
                      price=dec(_get(ln, "price", LINE_DE)), vat_rate=dec(_get(ln, "vat_rate", LINE_DE), "19"))
                 for ln in (_get(d, "lines", INVOICE_DE) or [])]
    return inv
