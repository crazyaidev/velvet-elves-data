"""Stamp staging URL onto the 5.1.7 stored-XSS UI shot. Deletes the raw frame."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.1.7")
RAW = OUT / "CASA_5_1_7_stored_raw.png"
FINAL = OUT / "CASA_5_1_7_stored.png"
URL = "https://app.stage.velvetelves.com/contacts"


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def main() -> None:
    src = Image.open(RAW).convert("RGB")
    w, h = src.size
    bar = 72
    im = Image.new("RGB", (w, h + bar), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 8), fill=(200, 80, 70))
    d.text((20, 16), "5.1.7  Stored name is text (not a running script)", font=font(16, True), fill=(24, 24, 24))
    d.text((20, 40), f"{URL}  |  no alert dialog  |  31 Aug 2026", font=font(13), fill=(80, 80, 80))
    im.paste(src, (0, bar))
    im.save(FINAL, "PNG")
    RAW.unlink(missing_ok=True)
    print("wrote", FINAL)


if __name__ == "__main__":
    main()
