"""Build the optional office branding (NOT part of the public repo, folder is git-ignored).

Takes a square logo PNG (dark mark on light background) and writes
branding/logo.png  (36 px accent tile with the mark in white, for the sidebar) and
branding/app.ico   (window and exe icon), plus branding/brand.json with the wordmark.

Usage: py -3 tools/make_branding.py <logo.png> "<WORDMARK>"
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ACCENT = (189, 90, 49, 255)
OUT = Path(__file__).resolve().parents[1] / "branding"


def mark_mask(src: Path) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    im = im.crop((int(w * .18), int(h * .18), int(w * .82), int(h * .82)))
    mask = Image.new("L", im.size, 0)
    px, mp = im.load(), mask.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            lum = (r + g + b) / 3
            mp[x, y] = max(0, min(255, int((235 - lum) * 2.2))) if a > 0 else 0
    return mask


def tile(mask: Image.Image, size: int, radius: float) -> Image.Image:
    big = size * 4
    t = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(t).rounded_rectangle((0, 0, big - 1, big - 1), int(big * radius), fill=ACCENT)
    inner = int(big * .78)
    m = mask.resize((inner, inner), Image.LANCZOS)
    white = Image.new("RGBA", (inner, inner), (255, 255, 255, 255))
    off = (big - inner) // 2
    t.paste(white, (off, off), m)
    return t.resize((size, size), Image.LANCZOS)


def main():
    src, word = Path(sys.argv[1]), sys.argv[2]
    OUT.mkdir(exist_ok=True)
    mask = mark_mask(src)
    tile(mask, 36, .25).save(OUT / "logo.png")
    tile(mask, 256, .22).save(OUT / "app.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)])
    (OUT / "brand.json").write_text(json.dumps({"wordmark": word}, ensure_ascii=False), encoding="utf-8")
    print("written:", OUT)


if __name__ == "__main__":
    main()
