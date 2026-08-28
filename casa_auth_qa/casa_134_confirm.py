"""Staging: guessed recovery tokens cannot set a password (CASA 1.3.4)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\1.3.4")
OUT.mkdir(parents=True, exist_ok=True)
PASSWORD = "CasaReset9x"


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def post_confirm(token: str) -> tuple[int, str]:
    payload = json.dumps({"token": token, "new_password": PASSWORD}).encode()
    req = urllib.request.Request(
        f"{API}/api/v1/users/password-reset/confirm",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")[:200]
            return resp.status, body.replace("\n", " ")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:200]
        return exc.code, body.replace("\n", " ")


def render(rows: list[tuple[int, str, int, str]]) -> None:
    W, H = 1400, 820
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text((48, 32), "1.3.4  POST /users/password-reset/confirm  (staging)", font=font(22, True), fill=(24, 24, 24))
    d.text(
        (48, 66),
        "Five guessed recovery tokens. None set a password.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 110
    d.text((48, y), "#", font=font(13, True), fill=(80, 80, 80))
    d.text((90, y), "HTTP", font=font(13, True), fill=(80, 80, 80))
    d.text((180, y), "Guessed token", font=font(13, True), fill=(80, 80, 80))
    d.text((520, y), "Response", font=font(13, True), fill=(80, 80, 80))
    y = 138
    d.line((48, y, W - 48, y), fill=(220, 218, 214), width=1)
    y = 156
    for n, token, status, body in rows:
        color = (20, 90, 50) if status == 400 else (24, 24, 24)
        d.text((48, y), str(n), font=font(15), fill=color)
        d.text((90, y), str(status), font=font(15, True), fill=color)
        d.text((180, y), token[:28], font=font(13), fill=(80, 80, 80))
        d.text((520, y), body[:70], font=font(13), fill=(80, 80, 80))
        y += 36
    d.text((48, H - 40), "api.stage.velvetelves.com  |  CASA 1.3.4", font=font(12), fill=(80, 80, 80))
    out = OUT / "CASA_1_3_4_confirm_guesses.png"
    im.save(out, "PNG")
    print("wrote", out)
    for n, token, status, body in rows:
        print(f"  {n} {status} {token} {body[:120]}")


if __name__ == "__main__":
    guesses = [
        "00000000",
        "12345678",
        "aaaaaaaaaaaaaaaa",
        "guessed-recovery-token",
        "00000000-0000-0000-0000-000000000000",
    ]
    rows = []
    for i, token in enumerate(guesses, start=1):
        status, body = post_confirm(token)
        rows.append((i, token, status, body))
    render(rows)
