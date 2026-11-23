"""Write the sample XML variants (valid + deliberately broken) for the Java cross-check.
Usage: py -3 tools/write_variants.py <out_dir>"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from erechnung.cii import GUIDELINE_EN16931, GUIDELINE_XRECHNUNG
from helpers import broken_variants
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for tag, g in (("xr", GUIDELINE_XRECHNUNG), ("en", GUIDELINE_EN16931)):
    for k, xml in broken_variants(g).items():
        if tag == "en" and k == "no_buyer_reference":
            continue  # identical to valid for EN16931 (BuyerReference optional there)
        (out / f"{tag}_{k}.xml").write_bytes(xml)
print("written:", out)
