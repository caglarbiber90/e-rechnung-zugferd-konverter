"""Drive the GUI through all three steps on the fictitious sample and save screenshots.
Uses a temporary APPDATA so real master data is never touched.
Usage: py -3 tools/gui_shots.py <out_dir> [--erststart]
  --erststart  start without master data: shows the welcome page, the missing-field
               message, then fills in the fictitious seller and continues."""
import os, shutil, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
appdata = Path(tempfile.mkdtemp()); os.environ["APPDATA"] = str(appdata)
FIRST = "--erststart" in sys.argv
(appdata / "E-Rechnung-Konverter").mkdir()
if not FIRST:
    shutil.copy(ROOT / "tests/sample/stammdaten.json", appdata / "E-Rechnung-Konverter/stammdaten.json")
work = Path(tempfile.mkdtemp()); pdf = work / "Musterrechnung.pdf"
shutil.copy(ROOT / "tests/sample/Musterrechnung.pdf", pdf)
sys.path.insert(0, str(ROOT / "src"))
import ctypes; ctypes.windll.shcore.SetProcessDpiAwareness(1)
from erechnung import gui
app = gui.App(); app.geometry("+20+20")
SHOWN = r"C:\Rechnungen"


def neutral_paths(widget):
    """Replace the real temp folder by a neutral example path in all visible labels."""
    for w in widget.winfo_children():
        try:
            t = w.cget("text")
            if isinstance(t, str) and str(work) in t:
                w.configure(text=t.replace(str(work), SHOWN))
        except Exception:
            pass
        neutral_paths(w)


def shot(name):
    """PrintWindow: captures the window even when other windows cover it."""
    from ctypes import wintypes, windll, byref, create_string_buffer, sizeof, c_uint32, Structure, c_long, c_ushort
    from PIL import Image
    neutral_paths(app); app.update()
    hwnd = windll.user32.GetParent(app.winfo_id())
    r = wintypes.RECT(); windll.user32.GetWindowRect(hwnd, byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = windll.user32.GetWindowDC(hwnd); mdc = windll.gdi32.CreateCompatibleDC(hdc)
    bmp = windll.gdi32.CreateCompatibleBitmap(hdc, w, h); windll.gdi32.SelectObject(mdc, bmp)
    windll.user32.PrintWindow(hwnd, mdc, 2)
    class BIH(Structure):
        _fields_ = [("biSize", c_uint32), ("biWidth", c_long), ("biHeight", c_long), ("biPlanes", c_ushort),
                    ("biBitCount", c_ushort), ("biCompression", c_uint32), ("biSizeImage", c_uint32),
                    ("a", c_long), ("b", c_long), ("c", c_uint32), ("d", c_uint32)]
    bi = BIH(sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = create_string_buffer(w * h * 4)
    windll.gdi32.GetDIBits(mdc, bmp, 0, h, buf, byref(bi), 0)
    Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1).save(out / name)
    windll.gdi32.DeleteObject(bmp); windll.gdi32.DeleteDC(mdc); windll.user32.ReleaseDC(hwnd, hdc)
def fill_seller():
    from erechnung.settings import Settings
    sample = Settings.load(ROOT / "tests/sample/stammdaten.json").seller
    for f in app.set_forms:
        for k in f.vars:
            f.set(k, getattr(sample, k))
    app.settings.buyers = Settings.load(ROOT / "tests/sample/stammdaten.json").buyers


first = [lambda: shot("0_willkommen.png"), lambda: app.save_settings(), lambda: shot("0b_fehlt.png"),
         fill_seller, lambda: app.save_settings()] if FIRST else []
seq = first + [lambda: shot("1_waehlen.png"), lambda: app.load_pdf(pdf), lambda: shot("2_pruefen.png"),
       lambda: app.review_nb.select(2), lambda: shot("2b_positionen.png"), lambda: app.review_nb.select(1), lambda: shot("2c_empfaenger.png"),
       lambda: app.generate()]
def step(i=0):
    if i < len(seq): seq[i](); app.after(700, lambda: step(i + 1))
    else: wait_result()
def wait_result():
    if str(app.go_btn["state"]) == "disabled": app.after(300, wait_result); return
    app.after(500, lambda: (shot("3_ergebnis.png"), print(sorted(p.name for p in work.iterdir())), app.destroy()))
app.after(800, step); app.mainloop()
