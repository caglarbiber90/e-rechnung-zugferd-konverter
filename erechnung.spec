# PyInstaller spec: one-file Windows exe. Build: py -3 -m PyInstaller --noconfirm erechnung.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

root = Path(SPECPATH)
datas = [(str(root / "src" / "erechnung" / "daten"), "erechnung/daten")]
for pkg in ("facturx", "iso4217", "stdnum"):
    datas += collect_data_files(pkg)
icon = str(root / "src" / "erechnung" / "daten" / "icon" / "app.ico")

a = Analysis(
    [str(root / "src" / "launcher.py")],
    pathex=[str(root / "src")],
    binaries=collect_dynamic_libs("saxonche"),
    datas=datas,
    hiddenimports=["saxonche", "windnd"],
    excludes=["PIL", "fitz", "pymupdf", "numpy", "matplotlib", "pytest", "reportlab"],
)
pyz = PYZ(a.pure)
# shown immediately on double-click while the one-file exe unpacks; closed by the program
splash = Splash(str(root / "src" / "erechnung" / "daten" / "icon" / "splash.png"),
                binaries=a.binaries, datas=a.datas, text_pos=None, always_on_top=False)
exe = EXE(
    pyz, a.scripts, splash, splash.binaries, a.binaries, a.datas, [],
    name="E-Rechnung-Konverter",
    console=False,
    icon=icon,
    upx=False,
    version=None,
)
