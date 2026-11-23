"""Shared test helpers: sample invoice and deliberately broken XML variants."""
from pathlib import Path

from lxml import etree

from erechnung.cii import NS, GUIDELINE_EN16931, GUIDELINE_XRECHNUNG, build_cii
from erechnung.core import propose
from erechnung.settings import Settings

SAMPLE = Path(__file__).resolve().parent / "sample"


def sample_invoice():
    st = Settings.load(SAMPLE / "stammdaten.json")
    inv, notes = propose(SAMPLE / "Musterrechnung.pdf", st)
    return inv, notes, st


def broken_variants(guideline=GUIDELINE_XRECHNUNG) -> dict[str, bytes]:
    inv, _, _ = sample_invoice()
    good = build_cii(inv, guideline)
    out = {"valid": good}

    def mutate(fn):
        root = etree.fromstring(good)
        fn(root)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")

    def wrong_gross(r):
        r.find(".//ram:GrandTotalAmount", NS).text = "2985.00"

    def empty_iban(r):
        r.find(".//ram:IBANID", NS).text = ""

    def no_buyer_ref(r):
        el = r.find(".//ram:BuyerReference", NS)
        el.getparent().remove(el)

    out["wrong_gross"] = mutate(wrong_gross)
    out["empty_iban"] = mutate(empty_iban)
    out["no_buyer_reference"] = mutate(no_buyer_ref)
    def schema_error(r):
        el = r.find(".//ram:BuyerReference", NS)
        parent = el.getparent(); parent.remove(el); parent.append(el)  # wrong position -> XSD error

    out["schema_error"] = mutate(schema_error)
    out["all_three"] = mutate(lambda r: (wrong_gross(r), empty_iban(r), no_buyer_ref(r)))
    return out
