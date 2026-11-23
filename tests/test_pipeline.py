import shutil
from decimal import Decimal

from erechnung import pdf as pdfmod
from erechnung.cii import GUIDELINE_EN16931, build_cii
from erechnung.core import finalize
from erechnung.validator import validate

from helpers import SAMPLE, broken_variants, sample_invoice


def test_extraction():
    inv, notes, _ = sample_invoice()
    assert inv.number == "2026-0815/01"
    assert inv.issue_date.isoformat() == "2026-11-15"
    assert (inv.period_start.isoformat(), inv.period_end.isoformat()) == ("2026-10-01", "2026-10-31")
    assert inv.due_date.isoformat() == "2026-12-15"
    assert inv.order_ref == "PO-2026-000123"
    assert inv.accounting_ref == "PSP-4711-001"
    assert inv.project_id == "4711" and inv.project_name == "4711-BIA-Umbau-Buero-3OG"
    assert inv.buyer.name == "Beispiel Immobilien AG" and inv.buyer.zip == "60528"
    assert inv.buyer_reference == "BI-4711"  # from buyer master data
    assert (inv.net_total, inv.vat_total, inv.gross_total) == (Decimal("2500.00"), Decimal("475.00"), Decimal("2975.00"))
    assert inv.lines[0].name == "Entwurfsplanung LPH 3"
    assert any("kein PDF/A" in n for n in notes)


def test_end_to_end(tmp_path):
    src = tmp_path / "Musterrechnung.pdf"
    shutil.copy(SAMPLE / "Musterrechnung.pdf", src)
    inv, _, _ = sample_invoice()
    oc = finalize(inv, src, write_xrechnung=True)
    assert oc.ok, (oc.problems, oc.result and [m.code for m in oc.result.errors])
    assert oc.pdf_out.name == "Musterrechnung_E-Rechnung.pdf" and oc.pdf_out.exists()
    assert oc.report_out.exists() and oc.xr_out.exists()
    xml = pdfmod.read_back(oc.pdf_out)
    assert validate(xml).accepted
    assert validate(oc.xr_out.read_bytes()).accepted
    assert pdfmod.pdfa_part(oc.pdf_out).startswith("3")


def test_arithmetic_check_blocks(tmp_path):
    inv, _, _ = sample_invoice()
    inv.gross_total = Decimal("2985.00")
    oc = finalize(inv, tmp_path / "x.pdf")
    assert not oc.ok and any("Bruttosumme" in p for p in oc.problems)
    assert not (tmp_path / "x_E-Rechnung.pdf").exists()


def test_broken_rule_codes():
    v = broken_variants()
    assert validate(v["valid"]).accepted
    codes = lambda k: {m.code for m in validate(v[k]).errors}
    assert {"BR-CO-15", "BR-CO-16"} <= codes("wrong_gross")
    assert {"BR-50", "PEPPOL-EN16931-R008"} <= codes("empty_iban")
    assert "BR-DE-15" in codes("no_buyer_reference")
    assert "XSD" in codes("schema_error")
    for k in ("schema_error", "wrong_gross", "empty_iban", "no_buyer_reference", "all_three"):
        assert not validate(v[k]).accepted


def test_en16931_without_buyer_reference_is_ok():
    inv, _, _ = sample_invoice()
    inv.buyer_reference = ""
    assert validate(build_cii(inv, GUIDELINE_EN16931)).accepted
