# PyInstaller spec: one-file Windows exe. Build: py -3 -m PyInstaller --noconfirm erechnung.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

root = Path(SPECPATH)
datas = [(str(root / "resources" / "kosit"), "resources/kosit")]
for pkg in ("facturx", "iso4217", "stdnum"):
    datas += collect_data_files(pkg)
branding = root / "branding"
icon = None
if branding.exists():
    datas.append((str(branding), "branding"))
    if (branding / "app.ico").exists():
        icon = str(branding / "app.ico")

a = Analysis(
    [str(root / "src" / "launcher.py")],
    pathex=[str(root / "src")],
    binaries=collect_dynamic_libs("saxonche"),
    datas=datas,
    hiddenimports=["saxonche", "windnd"],
    excludes=["fitz", "pymupdf", "numpy", "PIL", "matplotlib", "pytest", "reportlab"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="E-Rechnung-Konverter",
    console=False,
    icon=icon,
    upx=False,
    version=None,
)
