"""Staging: unsigned platform admin APIs (CASA 3.3.1). No tokens printed."""
from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.3.1")
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def get(path: str) -> tuple[int, str]:
    req = urllib.request.Request(
        f"{API}{path}",
        method="GET",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, " ".join(body.split())[:110]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, " ".join(body.split())[:110]


def render(rows: list[tuple[str, int, str]]) -> None:
    W, H = 1400, 780
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "3.3.1  Staging platform APIs deny unsigned callers",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "No Authorization sent. aal1-vs-aal2 not replayed (QA_PASSWORD unset).",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for label, status, body in rows:
        color = (20, 90, 50) if status == 401 else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=(80, 80, 80))
        y += 26
        d.text((48, y), f"HTTP {status}  {body}", font=font(15), fill=color)
        y += 48
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_3_3_1_deny  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_3_3_1_deny.png"
    im.save(out, "PNG")
    print("wrote", out)


if __name__ == "__main__":
    rows = [
        ("GET /api/v1/platform/users  (no Authorization)", *get("/api/v1/platform/users")),
        ("GET /api/v1/platform/registrations  (no Authorization)", *get("/api/v1/platform/registrations")),
        ("GET /api/v1/users/mfa/factors  (no Authorization)", *get("/api/v1/users/mfa/factors")),
    ]
    render(rows)
    for label, status, body in rows:
        print(f"  {status} {label}  {body[:80]}")
    if any(status != 401 for _, status, _ in rows):
        raise SystemExit("expected 401 on all unsigned platform/MFA GETs")
