"""Staging: password GET and session token in query are rejected (CASA 2.1.1)."""
from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.1.1")
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def request(method: str, path: str) -> tuple[int, str]:
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")[:180]
            return resp.status, body.replace("\n", " ")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:180]
        return exc.code, body.replace("\n", " ")


def render(rows: list[tuple[str, str, int, str]]) -> None:
    W, H = 1400, 820
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text((48, 32), "2.1.1  Staging API — secrets are not accepted from the URL", font=font(22, True), fill=(24, 24, 24))
    d.text(
        (48, 66),
        "GET login with a password query, and GET /users/me with access_token in the query. None of these authenticate.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 110
    d.text((48, y), "Method", font=font(13, True), fill=(80, 80, 80))
    d.text((140, y), "HTTP", font=font(13, True), fill=(80, 80, 80))
    d.text((220, y), "Request", font=font(13, True), fill=(80, 80, 80))
    y = 138
    d.line((48, y, W - 48, y), fill=(220, 218, 214), width=1)
    y = 156
    for method, path, status, body in rows:
        color = (20, 90, 50) if status in (401, 403, 405) else (24, 24, 24)
        d.text((48, y), method, font=font(15, True), fill=color)
        d.text((140, y), str(status), font=font(15, True), fill=color)
        d.text((220, y), path[:42], font=font(13), fill=(80, 80, 80))
        y += 28
        d.text((220, y), body[:95], font=font(12), fill=(80, 80, 80))
        y += 40
    d.text((48, H - 40), "api.stage.velvetelves.com  |  CASA 2.1.1", font=font(12), fill=(80, 80, 80))
    out = OUT / "CASA_2_1_1_query_rejected.png"
    im.save(out, "PNG")
    print("wrote", out)
    for method, path, status, body in rows:
        print(f"  {method} {status} {path} {body[:100]}")


if __name__ == "__main__":
    qs = urllib.parse.urlencode(
        {"username": "casa.evidence@example.com", "password": "WouldBeVisibleIfGet"}
    )
    rows = [
        ("GET", f"/api/v1/users/login?{qs}", *request("GET", f"/api/v1/users/login?{qs}")),
        (
            "GET",
            "/api/v1/users/me?access_token=not-a-session",
            *request("GET", "/api/v1/users/me?access_token=not-a-session"),
        ),
        ("GET", "/api/v1/users/me", *request("GET", "/api/v1/users/me")),
    ]
    render(rows)
