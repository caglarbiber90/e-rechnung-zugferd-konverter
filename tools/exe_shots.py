"""Start the built exe like a user would (optionally with empty master data = first start)
and save screenshots of all its windows, even if other windows cover them.

Usage: py -3 tools/exe_shots.py <exe> <out_dir> [--stammdaten FILE] [--wait SECONDS]
"""
import argparse
import ctypes
import os
import subprocess
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

from PIL import Image

user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32


def windows_of(pid):
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            found.append((hwnd, p.value, buf.value))
        return True

    user32.EnumWindows(cb, 0)
    return [(h, t) for h, p, t in found if t and any(k in t for k in pid)]


def capture(hwnd, path):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user32.GetWindowDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(hwnd, mdc, 2)

    class BIH(ctypes.Structure):
        _fields_ = [("a", ctypes.c_uint32), ("w", ctypes.c_long), ("h", ctypes.c_long), ("p", ctypes.c_ushort),
                    ("b", ctypes.c_ushort), ("c", ctypes.c_uint32), ("s", ctypes.c_uint32),
                    ("x", ctypes.c_long), ("y", ctypes.c_long), ("u", ctypes.c_uint32), ("i", ctypes.c_uint32)]
    bi = BIH(ctypes.sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1).save(path)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mdc)
    user32.ReleaseDC(hwnd, hdc)
    return w, h, (r.left, r.top)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("out")
    ap.add_argument("--stammdaten")
    ap.add_argument("--wait", type=float, default=12)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    appdata = Path(tempfile.mkdtemp())
    if a.stammdaten:
        (appdata / "E-Rechnung-Konverter").mkdir()
        (appdata / "E-Rechnung-Konverter" / "stammdaten.json").write_bytes(Path(a.stammdaten).read_bytes())
    env = dict(os.environ, APPDATA=str(appdata))
    proc = subprocess.Popen([str(Path(a.exe).resolve())], env=env)
    time.sleep(a.wait)
    # the one-file exe runs the program in a child process: find its windows by title
    for i, (h, t) in enumerate(windows_of(("E-Rechnung", "Stammdaten"))):
        size = capture(h, out / f"fenster_{i}.png")
        print(i, repr(t), size)
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)


if __name__ == "__main__":
    main()
