"""Staging: unsigned object-ID paths deny (CASA 3.1.4). No other tenant queried."""
from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
# Synthetic UUID — not taken from any tenant. Proves ID-in-path still needs auth.
FAKE = "00000000-0000-4000-8000-000000000314"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.4")
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def request(method: str, path: str) -> tuple[int, str]:
    h = {"Accept": "application/json"}
    req = urllib.request.Request(f"{API}{path}", method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="replace")[:160]
            return resp.status, body.replace("\n", " ")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:160]
        return exc.code, body.replace("\n", " ")


def render(rows: list[tuple[str, int, str]]) -> None:
    W, H = 1400, 900
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "3.1.4  Staging unsigned object IDs return 401",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Placeholder UUID only. No Authorization. No other tenant was queried.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for label, status, body in rows:
        ok = status == 401
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=(80, 80, 80))
        d.text((980, y), f"HTTP {status}", font=font(15, True), fill=color)
        y += 28
        d.text((48, y), body[:110], font=font(13), fill=(80, 80, 80))
        y += 52
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_3_1_4_deny  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_3_1_4_deny.png"
    im.save(out, "PNG")
    print("wrote", out)
    for label, status, _body in rows:
        print(f"  {status} {label}")


if __name__ == "__main__":
    paths = [
        f"/api/v1/transactions/{FAKE}",
        f"/api/v1/users/{FAKE}",
        f"/api/v1/tenants/{FAKE}",
        f"/api/v1/documents/{FAKE}",
        f"/api/v1/invoices/{FAKE}",
    ]
    rows = [(f"GET {p}", *request("GET", p)) for p in paths]
    render(rows)
    if any(status != 401 for _label, status, _body in rows):
        raise SystemExit(1)
