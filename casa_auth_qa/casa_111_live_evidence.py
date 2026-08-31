"""
Staging-only CASA 1.1.1 live evidence.

Hits OUR login/register routes to show 429 / 422. Uses a throwaway email
and a known-weak password so no real account is locked or created.
Never pointed at production.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\1.1.1")
OUT.mkdir(parents=True, exist_ok=True)
PROBE_EMAIL = "casa.al1.111.probe@example.com"


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def post(path: str, *, data: bytes, content_type: str) -> tuple[int, str]:
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method="POST",
        headers={"Content-Type": content_type, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")[:240]
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:240]
        return exc.code, body


def login_burst() -> list[tuple[int, int, str]]:
    rows = []
    form = f"username={PROBE_EMAIL}&password=WrongPass1!".encode()
    for i in range(1, 13):
        status, body = post(
            "/api/v1/users/login",
            data=form,
            content_type="application/x-www-form-urlencoded",
        )
        rows.append((i, status, body.replace("\n", " ")))
        time.sleep(0.15)
    return rows


def register_burst() -> list[tuple[int, int, str]]:
    rows = []
    for i in range(1, 7):
        payload = json.dumps(
            {
                "email": f"casa.al1.111.reg{i}@example.com",
                "password": "password123",
                "full_name": "CASA probe",
            }
        ).encode()
        status, body = post(
            "/api/v1/users/register",
            data=payload,
            content_type="application/json",
        )
        rows.append((i, status, body.replace("\n", " ")))
        time.sleep(0.15)
    return rows


def render(title: str, subtitle: str, rows: list[tuple[int, int, str]], outfile: str) -> None:
    W, H = 1400, 900
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text((48, 32), title, font=font(22, True), fill=(24, 24, 24))
    d.text((48, 66), subtitle, font=font(14), fill=(80, 80, 80))
    y = 110
    d.text((48, y), "#", font=font(13, True), fill=(80, 80, 80))
    d.text((90, y), "HTTP", font=font(13, True), fill=(80, 80, 80))
    d.text((180, y), "Response (truncated, no secrets)", font=font(13, True), fill=(80, 80, 80))
    y = 138
    d.line((48, y, W - 48, y), fill=(220, 218, 214), width=1)
    y = 150
    for n, status, body in rows:
        color = (20, 90, 50) if status == 429 else (24, 24, 24)
        if status == 422:
            color = (20, 90, 50)
        d.text((48, y), str(n), font=font(15), fill=color)
        d.text((90, y), str(status), font=font(15, True), fill=color)
        clip = body[:110]
        d.text((180, y), clip, font=font(13), fill=(80, 80, 80))
        y += 28
    d.text(
        (48, H - 40),
        "Staging only. Throwaway emails. No production traffic. CASA 1.1.1",
        font=font(12),
        fill=(80, 80, 80),
    )
    im.save(OUT / outfile, "PNG")
    print("wrote", OUT / outfile)
    for n, status, body in rows:
        print(f"  {n:02d} {status} {body[:120]}")


if __name__ == "__main__":
    print("--- login burst ---")
    login_rows = login_burst()
    render(
        "1.1.1 Staging login IP limiter",
        f"POST {API}/api/v1/users/login  |  12 attempts in ~2s  |  account {PROBE_EMAIL} (does not need to exist)",
        login_rows,
        "CASA_1_1_1_login_429.png",
    )
    print("--- register burst ---")
    reg_rows = register_burst()
    render(
        "1.1.1 Staging register limiter + weak-password rejection",
        f"POST {API}/api/v1/users/register  |  password123 on the denylist  |  6 attempts",
        reg_rows,
        "CASA_1_1_1_register_429.png",
    )
