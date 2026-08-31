"""Staging: access control fails closed (CASA 3.1.3). Does not run the cron tick."""
from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.3")
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def request(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(f"{API}{path}", method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="replace")[:90]
            return resp.status, body.replace("\n", " ")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:90]
        return exc.code, body.replace("\n", " ")


def render(rows: list[tuple[str, int, str]]) -> None:
    W, H = 1400, 820
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "3.1.3  Staging access control fails closed",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Missing auth is 401. Bad JWT is 401. Cron tick without secret is 403. Tick was not run.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for label, status, body in rows:
        ok = status in (401, 403)
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=(80, 80, 80))
        d.text((900, y), f"HTTP {status}", font=font(15, True), fill=color)
        y += 28
        d.text((48, y), body[:110], font=font(13), fill=(80, 80, 80))
        y += 56
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_3_1_3_fail  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_3_1_3_fail.png"
    im.save(out, "PNG")
    print("wrote", out)
    for label, status, _body in rows:
        print(f"  {status} {label}")


if __name__ == "__main__":
    rows = [
        ("GET /users/me  (no Authorization)", *request("GET", "/api/v1/users/me")),
        (
            "GET /users/me  Bearer not-a-jwt",
            *request("GET", "/api/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"}),
        ),
        (
            "POST /internal/schedules/tick  (no cron secret)",
            *request("POST", "/api/v1/internal/schedules/tick"),
        ),
    ]
    render(rows)
    if rows[0][1] != 401 or rows[1][1] != 401:
        raise SystemExit(1)
    if rows[2][1] not in (401, 403):
        raise SystemExit(1)
    # A 200 here would mean the tick ran without a secret — fail closed was broken.
    if rows[2][1] == 200:
        raise SystemExit(1)
