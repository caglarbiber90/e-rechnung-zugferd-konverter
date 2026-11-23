"""PDF/A detection and ZUGFeRD / Factur-X embedding."""
from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader


def pdfa_part(path: Path) -> str:
    """Return the PDF/A claim from the XMP metadata, e.g. '3B', or '' if none.

    This only reads the claim; it does not verify conformance (that needs veraPDF)."""
    reader = PdfReader(str(path))
    try:
        meta = reader.trailer["/Root"].get("/Metadata")
        if meta is None:
            return ""
        xmp = meta.get_object().get_data().decode("utf-8", "ignore")
    except Exception:
        return ""
    part = re.search(r"pdfaid:part(?:>|=\")\s*(\d)", xmp)
    conf = re.search(r"pdfaid:conformance(?:>|=\")\s*([A-Za-z])", xmp)
    if not part:
        return ""
    return part.group(1) + (conf.group(1).upper() if conf else "")


def embed(pdf_in: Path, xml: bytes, pdf_out: Path, level: str = "en16931") -> None:
    from facturx import generate_from_file
    generate_from_file(str(pdf_in), xml, flavor="factur-x", level=level,
                       check_xsd=True, output_pdf_file=str(pdf_out),
                       lang="de-DE")


def read_back(pdf: Path) -> bytes:
    from facturx import get_xml_from_pdf
    with open(pdf, "rb") as f:
        _name, xml = get_xml_from_pdf(f.read(), check_xsd=False)
    return xml
