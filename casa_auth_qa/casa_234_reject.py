"""Staging: /users/me rejects missing or garbage Bearer (CASA 2.3.4). No forged JWTs."""
from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.3.4")
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def request(headers: dict[str, str]) -> tuple[int, str]:
    req = urllib.request.Request(
        f"{API}/api/v1/users/me",
        method="GET",
        headers={"Accept": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")[:80]
            return resp.status, body.replace("\n", " ")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:80]
        return exc.code, body.replace("\n", " ")


def render(rows: list[tuple[str, int, str]]) -> None:
    W, H = 1400, 720
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text((48, 32), "2.3.4  Staging /users/me rejects unsigned callers", font=font(22, True), fill=(24, 24, 24))
    d.text(
        (48, 68),
        "Missing Authorization, then Bearer not-a-jwt. No forged JWT. Bodies truncated.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for label, status, body in rows:
        color = (20, 90, 50) if status == 401 else (140, 40, 40)
        d.text((48, y), label, font=font(15, True), fill=(80, 80, 80))
        d.text((520, y), f"HTTP {status}", font=font(15, True), fill=color)
        d.text((700, y), body[:50], font=font(13), fill=(80, 80, 80))
        y += 52
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_2_3_4_reject  |  28 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_2_3_4_reject.png"
    im.save(out, "PNG")
    print("wrote", out)
    for label, status, _body in rows:
        print(f"  {status} {label}")


if __name__ == "__main__":
    rows = [
        ("GET /users/me  (no Authorization)", *request({})),
        ("GET /users/me  Authorization: Bearer not-a-jwt", *request({"Authorization": "Bearer not-a-jwt"})),
    ]
    render(rows)
    if any(status != 401 for _label, status, _body in rows):
        raise SystemExit(1)
