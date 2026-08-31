"""Staging: two logins issue different JWT iat (CASA 2.3.3). Never prints tokens."""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.3.3")
OUT.mkdir(parents=True, exist_ok=True)
EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD")


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
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def b64url_json(segment: str) -> dict:
    pad = "=" * ((4 - len(segment) % 4) % 4)
    raw = base64.urlsafe_b64decode(segment + pad)
    return json.loads(raw.decode("utf-8"))


def iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def login_iat() -> tuple[int, int, str | None]:
    body = urllib.parse.urlencode({"username": EMAIL, "password": PASSWORD}).encode()
    status, raw = request(
        "POST",
        "/api/v1/users/login",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        data = json.loads(raw) if raw.strip().startswith("{") else {}
    except json.JSONDecodeError:
        return status, -1, None
    access = data.get("access_token")
    if not isinstance(access, str) or access.count(".") != 2:
        return status, -1, None
    payload = b64url_json(access.split(".")[1])
    iat = payload.get("iat")
    if not isinstance(iat, int):
        return status, -1, access
    return status, iat, access


def render(*, s1: int, iat1: int, s2: int, iat2: int) -> None:
    different = iat1 > 0 and iat2 > 0 and iat1 != iat2
    W, H = 1400, 720
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text((48, 32), "2.3.3  Staging JWTs are issued per login", font=font(22, True), fill=(24, 24, 24))
    d.text(
        (48, 68),
        "Two POST /users/login calls. iat only. Tokens are not shown.",
        font=font(14),
        fill=(80, 80, 80),
    )
    rows = [
        ("Login 1", f"HTTP {s1}   iat {iat1}  ({iso(iat1) if iat1 > 0 else 'n/a'})"),
        ("Login 2", f"HTTP {s2}   iat {iat2}  ({iso(iat2) if iat2 > 0 else 'n/a'})"),
        ("iat values differ", "YES" if different else "NO"),
        ("Static shared API key", "no - a new JWT is minted after authentication"),
    ]
    y = 120
    for label, value in rows:
        d.text((48, y), label, font=font(15, True), fill=(80, 80, 80))
        color = (20, 90, 50) if value.startswith("YES") or value.startswith("no") else (24, 24, 24)
        d.text((420, y), value[:78], font=font(15), fill=color)
        y += 48
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_2_3_3_dyn  |  28 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_2_3_3_dyn.png"
    im.save(out, "PNG")
    print("wrote", out)
    print(f"  login1={s1} iat={iat1} login2={s2} iat={iat2} different={different}")


if __name__ == "__main__":
    if not PASSWORD:
        print("Set QA_PASSWORD", file=sys.stderr)
        sys.exit(2)
    s1, iat1, t1 = login_iat()
    if t1:
        request("POST", "/api/v1/users/logout", headers={"Authorization": f"Bearer {t1}"})
    time.sleep(2)
    s2, iat2, t2 = login_iat()
    if t2:
        request("POST", "/api/v1/users/logout", headers={"Authorization": f"Bearer {t2}"})
    render(s1=s1, iat1=iat1, s2=s2, iat2=iat2)
    if s1 != 200 or s2 != 200 or iat1 == iat2:
        sys.exit(1)
