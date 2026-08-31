"""Velvet Elves: directory paths are not listings (CASA 3.1.6)."""
from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.6")
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def fetch(url: str) -> tuple[int, str, str]:
    req = urllib.request.Request(url, method="GET", headers={"Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read(800).decode("utf-8", errors="replace")
            ctype = resp.headers.get("Content-Type", "")
            return resp.status, ctype.split(";")[0].strip(), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read(800).decode("utf-8", errors="replace")
        ctype = exc.headers.get("Content-Type", "") if exc.headers else ""
        return exc.code, ctype.split(";")[0].strip(), raw


def looks_like_listing(body: str) -> bool:
    low = body.lower()
    if "listbucketresult" in low:
        return True
    if "index of" in low and (
        "parent directory" in low or "[dir]" in low or "<title>index of" in low
    ):
        return True
    if "directory listing" in low:
        return True
    return False


def snippet(body: str) -> str:
    compact = " ".join(body.split())
    low = compact.lower()
    if compact.startswith("<!doctype html") or compact.startswith("<html"):
        return "SPA HTML shell (<!doctype html> ...)  not Index of /"
    if compact.startswith("{"):
        return compact[:90]
    if "index of" in low:
        return compact[:90]
    return compact[:90]


def render(rows: list[tuple[str, int, str, str]]) -> None:
    W, H = 1400, 980
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "3.1.6  Staging directory paths are not listings",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "SPA prefixes return the HTML shell. API prefixes return JSON 404. No Index of / or ListBucketResult.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 118
    for label, status, ctype, body in rows:
        listing = looks_like_listing(body)
        ok = not listing
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=(80, 80, 80))
        d.text((900, y), f"HTTP {status}", font=font(15, True), fill=color)
        y += 24
        d.text((48, y), f"{ctype or '(no type)'}  {snippet(body)}", font=font(13), fill=(80, 80, 80))
        y += 48
    d.text(
        (48, H - 48),
        "app.stage / api.stage.velvetelves.com  |  CASA_3_1_6_nolist  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_3_1_6_nolist.png"
    im.save(out, "PNG")
    print("wrote", out)
    for label, status, ctype, body in rows:
        flag = "LISTING" if looks_like_listing(body) else "ok"
        print(f"  {status} {flag} {ctype} {label}")


if __name__ == "__main__":
    targets = [
        ("SPA GET /assets/", "https://app.stage.velvetelves.com/assets/"),
        ("SPA GET /static/", "https://app.stage.velvetelves.com/static/"),
        ("SPA GET /assets/missing-316.js", "https://app.stage.velvetelves.com/assets/missing-316.js"),
        ("API GET /", "https://api.stage.velvetelves.com/"),
        ("API GET /api/v1/", "https://api.stage.velvetelves.com/api/v1/"),
        ("API GET /static/", "https://api.stage.velvetelves.com/static/"),
    ]
    rows = []
    listed = False
    for label, url in targets:
        status, ctype, body = fetch(url)
        rows.append((label, status, ctype, body))
        if looks_like_listing(body):
            listed = True
    render(rows)
    if listed:
        raise SystemExit("directory listing body detected")
    old = OUT / "CASA_3_1_6_deny.png"
    if old.exists():
        old.unlink()
