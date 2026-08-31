"""Add a hostname caption above SSL Labs protocol screenshots (does not cover Qualys UI)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.1")
BANNER = 64
BG = (248, 248, 246)
INK = (24, 24, 24)
MUTED = (80, 80, 80)
RULE = (200, 80, 70)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def caption(name: str, title: str) -> None:
    src = OUT / name
    im = Image.open(src).convert("RGB")
    out = Image.new("RGB", (im.width, im.height + BANNER), BG)
    d = ImageDraw.Draw(out)
    d.rectangle((0, 0, im.width, 8), fill=RULE)
    d.text((24, 18), title, font=font(16, True), fill=INK)
    d.text((24, 40), "Qualys SSL Labs configuration  |  31 Aug 2026", font=font(12), fill=MUTED)
    out.paste(im, (0, BANNER))
    out.save(src, "PNG")
    print("captioned", src)


if __name__ == "__main__":
    caption("CASA_4_1_1_ssllabs_app_protocols.png", "app.velvetelves.com  (endpoint 65.8.20.108)")
    caption("CASA_4_1_1_ssllabs_api_protocols.png", "api.prod.velvetelves.com  (endpoint 3.148.31.71)")
