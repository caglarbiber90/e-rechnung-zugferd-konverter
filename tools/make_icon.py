"""Draw the neutral app icon (white invoice sheet with euro lines on a terracotta tile).
Writes src/erechnung/daten/icon/app.ico and resources/icon/logo.png (36 px, sidebar).
Usage: py -3 tools/make_icon.py   (needs pillow)"""
from pathlib import Path

from PIL import Image, ImageDraw

ACCENT = (189, 90, 49, 255)
OUT = Path(__file__).resolve().parents[1] / "src" / "erechnung" / "daten" / "icon"


def draw(size: int) -> Image.Image:
    s = 512
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, s - 1, s - 1), 112, fill=ACCENT)
    # sheet with folded corner
    x0, y0, x1, y1, f = 150, 96, 362, 416, 64
    d.polygon([(x0, y0), (x1 - f, y0), (x1, y0 + f), (x1, y1), (x0, y1)], fill="white")
    d.polygon([(x1 - f, y0), (x1 - f, y0 + f), (x1, y0 + f)], fill=(232, 196, 178, 255))
    for i, w in enumerate((150, 120, 150, 90)):
        y = 190 + i * 46
        d.rounded_rectangle((x0 + 30, y, x0 + 30 + w, y + 18), 9, fill=(189, 90, 49, 200))
    # check mark badge
    d.ellipse((300, 316, 432, 448), fill=(47, 112, 69, 255), outline="white", width=12)
    d.line([(334, 384), (360, 410), (402, 356)], fill="white", width=20, joint="curve")
    return im.resize((size, size), Image.LANCZOS)


def splash() -> Image.Image:
    """Start-up picture shown by the exe while it unpacks (PyInstaller splash screen)."""
    from PIL import ImageFont
    w, h = 460, 150
    im = Image.new("RGB", (w, h), (250, 250, 248))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), outline=(230, 229, 225), width=2)
    im.paste(draw(84), (32, 33), draw(84))

    def font(name, size):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            return ImageFont.load_default()
    d.text((140, 44), "E-Rechnung-Konverter", fill=(30, 33, 38), font=font("segoeuib.ttf", 24))
    d.text((140, 84), "Programm wird gestartet …", fill=(106, 111, 119), font=font("segoeui.ttf", 16))
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    splash().save(OUT / "splash.png")
    draw(36).save(OUT / "logo.png")
    draw(256).save(OUT / "app.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)])
    draw(256).save(OUT / "app-256.png")
    print("written:", OUT)


if __name__ == "__main__":
    main()
