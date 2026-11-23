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


def party_to_dict(p) -> dict:
    return asdict(p)


def party_from_dict(cls, d: dict):
    names = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in (d or {}).items() if k in names})
