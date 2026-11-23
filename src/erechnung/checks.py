"""Plausibility checks before XML generation (German messages for the user)."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from .model import Invoice, money

TOL = Decimal("0.01")


def vat_breakdown(inv: Invoice) -> dict[Decimal, tuple[Decimal, Decimal]]:
    """rate -> (basis, tax) computed from the lines."""
    basis: dict[Decimal, Decimal] = defaultdict(Decimal)
    for ln in inv.lines:
        basis[Decimal(ln.vat_rate)] += ln.net
    return {r: (money(b), money(b * r / 100)) for r, b in basis.items()}


def computed_totals(inv: Invoice) -> tuple[Decimal, Decimal, Decimal]:
    br = vat_breakdown(inv)
    net = money(sum((b for b, _ in br.values()), Decimal(0)))
    vat = money(sum((t for _, t in br.values()), Decimal(0)))
    return net, vat, net + vat


def check(inv: Invoice) -> list[str]:
    """Returns a list of problems; empty list = ok."""
    p: list[str] = []
    req = [
        (inv.number, "Rechnungsnummer fehlt."),
        (inv.issue_date, "Rechnungsdatum fehlt."),
        (inv.seller.name, "Name des Rechnungsstellers fehlt (Stammdaten)."),
        (inv.seller.street and inv.seller.zip and inv.seller.city,
         "Anschrift des Rechnungsstellers unvollständig (Stammdaten)."),
        (inv.seller.vat_id or inv.seller.tax_no,
         "USt-IdNr. oder Steuernummer des Rechnungsstellers fehlt (Stammdaten)."),
        (inv.seller.iban, "IBAN fehlt (Stammdaten)."),
        (inv.buyer.name, "Name des Rechnungsempfängers fehlt."),
        (inv.buyer.street and inv.buyer.zip and inv.buyer.city,
         "Anschrift des Rechnungsempfängers unvollständig."),
        (inv.lines, "Keine Rechnungsposition vorhanden."),
    ]
    p += [msg for ok, msg in req if not ok]
    if inv.period_start and inv.period_end and inv.period_end < inv.period_start:
        p.append("Leistungszeitraum: Ende liegt vor dem Beginn.")
    for i, ln in enumerate(inv.lines, 1):
        if not ln.name.strip():
            p.append(f"Position {i}: Bezeichnung fehlt.")
        if Decimal(ln.vat_rate) <= 0:
            p.append(f"Position {i}: Steuersatz 0 % (steuerfrei / Reverse Charge) "
                     "wird von diesem Werkzeug noch nicht unterstützt.")
    net, vat, gross = computed_totals(inv)
    if abs(net - money(inv.net_total)) > TOL:
        p.append(f"Nettosumme passt nicht: Summe der Positionen {fmt(net)}, eingetragen {fmt(inv.net_total)}.")
    if abs(vat - money(inv.vat_total)) > TOL:
        p.append(f"Umsatzsteuer passt nicht: berechnet {fmt(vat)}, eingetragen {fmt(inv.vat_total)}.")
    if abs(money(inv.net_total) + money(inv.vat_total) - money(inv.gross_total)) > TOL:
        p.append(f"Netto + USt ergibt {fmt(money(inv.net_total) + money(inv.vat_total))}, "
                 f"Bruttosumme eingetragen {fmt(inv.gross_total)}.")
    return p


def fmt(d) -> str:
    s = f"{money(d):,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".") + " €"
