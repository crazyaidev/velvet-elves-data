"""Shared Pillow helpers for remaining CASA TAC evidence PNGs."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (248, 248, 246)
INK = (24, 24, 24)
MUTED = (80, 80, 80)
RULE = (200, 80, 70)
OK = (20, 90, 50)
LINE = (220, 218, 214)
CODE_BG = (36, 36, 36)
CODE_FG = (230, 230, 226)
W, H = 1400, 1800
MARGIN = 56


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    for p in (
        rf"C:\Windows\Fonts\{name}",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def mono(size: int):
    for p in (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return font(size)


F_H = font(22, True)
F_SUB = font(14)
F_SEC = font(16, True)
F_BODY = font(15)
F_SMALL = font(13)
F_FOOT = font(12)
F_MONO = mono(12)


def wrap(draw, text, fnt, width):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def new_page(out_stem: str, title: str, page_no: int, pages: int = 2):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), title, font=F_H, fill=INK)
    d.text(
        (MARGIN, 98),
        "GCP 538509143953  |  production app.velvetelves.com  |  31 Aug 2026",
        font=F_SMALL,
        fill=MUTED,
    )
    d.line((MARGIN, 124, W - MARGIN, 124), fill=LINE, width=1)
    d.text((MARGIN, H - 42), f"Page {page_no} of {pages}", font=F_FOOT, fill=MUTED)
    d.text((W - MARGIN - 280, H - 42), out_stem, font=F_FOOT, fill=MUTED)
    return im, d, 144


def paint(d, y, lines):
    max_w = W - 2 * MARGIN
    for text, fnt, color in lines:
        for part in wrap(d, text, fnt, max_w):
            d.text((MARGIN, y), part, font=fnt, fill=color)
            y += 22 if fnt is F_SMALL else 24
        y += 4
    return y


def save_page1(out_dir: Path, stem: str, title: str, sections: list[tuple[str, str]]):
    im, d, y = new_page(stem, title, 1)
    for heading, body in sections:
        d.text((MARGIN, y), heading, font=F_SEC, fill=INK)
        y += 32
        y = paint(d, y, [(body, F_BODY, INK)])
        y += 10
    path = out_dir / f"{stem}_page1.png"
    im.save(path, "PNG")
    print("wrote", path)


def save_page2(out_dir: Path, stem: str, title: str, rows: list[tuple[str, str]], attest: str):
    im, d, y = new_page(stem, title, 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    for name, detail in rows:
        d.text((MARGIN, y), name, font=F_BODY, fill=OK)
        y += 24
        y = paint(d, y, [(detail, F_SMALL, MUTED)])
        y += 8
    y += 8
    d.text((MARGIN, y), "Attestation", font=F_SEC, fill=INK)
    y += 32
    paint(d, y, [(attest, F_BODY, INK)])
    path = out_dir / f"{stem}_page2.png"
    im.save(path, "PNG")
    print("wrote", path)


def save_code(out_dir: Path, stem: str, title: str, snippet: str, suffix: str = "code"):
    lines = snippet.split("\n")
    height = max(520, 160 + 24 * len(lines) + 80)
    im = Image.new("RGB", (1400, height), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), title, font=F_H, fill=INK)
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line[:108], font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), f"{stem}_{suffix}", font=F_FOOT, fill=MUTED)
    path = out_dir / f"{stem}_{suffix}.png"
    im.save(path, "PNG")
    print("wrote", path)


def save_probe(out_dir: Path, filename: str, title: str, subtitle: str, rows: list[tuple[str, str, bool]]):
    height = max(640, 180 + 70 * len(rows))
    im = Image.new("RGB", (1400, height), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((48, 32), title, font=F_H, fill=INK)
    d.text((48, 68), subtitle, font=F_SUB, fill=MUTED)
    y = 118
    for label, detail, ok in rows:
        color = OK if ok else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=MUTED)
        y += 24
        d.text((48, y), detail[:120], font=F_BODY, fill=color)
        y += 44
    d.text((48, height - 48), f"31 Aug 2026  |  {filename}", font=F_FOOT, fill=MUTED)
    path = out_dir / filename
    im.save(path, "PNG")
    print("wrote", path)
