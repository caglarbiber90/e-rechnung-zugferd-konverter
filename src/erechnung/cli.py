"""Entry point. Without arguments (or with a PDF path) the GUI opens.

Headless self-test for builds:  E-Rechnung-Konverter.exe --selftest <pdf> <stammdaten.json>
writes <pdf>_E-Rechnung.pdf like the GUI would, using the extracted values unchanged.
"""
import sys
from pathlib import Path


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--selftest":
        from .core import finalize, propose
        from .settings import Settings
        import traceback
        pdf, st = Path(sys.argv[2]), Settings.load(Path(sys.argv[3]))
        try:
            inv, notes = propose(pdf, st)
            oc = finalize(inv, pdf, write_xrechnung=True)
            lines = notes + oc.problems + [f"{m.code}: {m.text}" for m in (oc.result.errors if oc.result else [])]
            lines.append(f"OK={oc.ok} PDF={oc.pdf_out} REPORT={oc.report_out} XR={oc.xr_out}")
            ok = oc.ok
        except Exception:
            lines, ok = [traceback.format_exc()], False
        (pdf.parent / "selftest.log").write_text("\n".join(lines), encoding="utf-8")
        sys.exit(0 if ok else 1)
    from .gui import main as gui_main
    gui_main()
