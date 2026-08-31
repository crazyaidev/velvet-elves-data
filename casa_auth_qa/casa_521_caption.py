"""Stamp staging deal URL onto the 5.2.1 picker shot. Deletes the raw frame."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.2.1")
RAW = OUT / "CASA_5_2_1_picker_raw.png"
FINAL = OUT / "CASA_5_2_1_picker.png"


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def main() -> None:
    url_file = OUT / "_picker_url.txt"
    url = (
        url_file.read_text(encoding="utf-8").strip()
        if url_file.exists()
        else "https://app.stage.velvetelves.com/transactions/?tab=compliance"
    )
    src = Image.open(RAW).convert("RGB")
    w, h = src.size
    bar = 72
    canvas_w = max(w, 1080)
    im = Image.new("RGB", (canvas_w, h + bar), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, canvas_w, 8), fill=(200, 80, 70))
    d.text((20, 16), "5.2.1  Upload picker lists allowed types (no malware uploaded)", font=font(15, True), fill=(24, 24, 24))
    d.text((20, 40), f"{url}  |  31 Aug 2026", font=font(12), fill=(80, 80, 80))
    im.paste(src, ((canvas_w - w) // 2, bar))
    im.save(FINAL, "PNG")
    RAW.unlink(missing_ok=True)
    url_file.unlink(missing_ok=True)
    print("wrote", FINAL)


if __name__ == "__main__":
    main()
