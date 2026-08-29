"""Staging: access JWT lifetime from iat/exp (CASA 2.2.3). Never prints tokens."""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.2.3")
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
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body


def b64url_json(segment: str) -> dict:
    pad = "=" * ((4 - len(segment) % 4) % 4)
    raw = base64.urlsafe_b64decode(segment + pad)
    return json.loads(raw.decode("utf-8"))


def iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def render(*, alg: str, iat: int, exp: int, lifetime_s: int, login_status: int) -> None:
    hours = lifetime_s / 3600
    under = lifetime_s > 0 and lifetime_s < 86400
    W, H = 1400, 780
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text((48, 32), "2.2.3  Staging access JWT lifetime", font=font(22, True), fill=(24, 24, 24))
    d.text(
        (48, 68),
        "POST /users/login then decode iat and exp from the JWT payload. Token not shown.",
        font=font(14),
        fill=(80, 80, 80),
    )
    rows = [
        ("Login", f"HTTP {login_status}"),
        ("JWT alg", alg),
        ("iat", f"{iat}  ({iso(iat)})"),
        ("exp", f"{exp}  ({iso(exp)})"),
        ("Lifetime (exp - iat)", f"{lifetime_s} seconds  ({hours:.2f} hours)"),
        ("ADA 2.2.3 cap", "24 hours (86400 seconds)"),
        ("Under 24 hours", "YES" if under else "NO"),
    ]
    y = 120
    for label, value in rows:
        d.text((48, y), label, font=font(15, True), fill=(80, 80, 80))
        color = (20, 90, 50) if label == "Under 24 hours" and under else (24, 24, 24)
        d.text((420, y), value, font=font(15), fill=color)
        y += 44
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_2_2_3_exp  |  28 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_2_2_3_exp.png"
    im.save(out, "PNG")
    print("wrote", out)
    print(f"  login={login_status} alg={alg} lifetime_s={lifetime_s} hours={hours:.2f} under_24h={under}")


if __name__ == "__main__":
    if not PASSWORD:
        print("Set QA_PASSWORD", file=sys.stderr)
        sys.exit(2)
    login_body = urllib.parse.urlencode({"username": EMAIL, "password": PASSWORD}).encode()
    status, raw = request(
        "POST",
        "/api/v1/users/login",
        data=login_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        data = json.loads(raw) if raw.strip().startswith("{") else {}
    except json.JSONDecodeError:
        print(f"login failed http={status}", file=sys.stderr)
        sys.exit(1)
    access = data.get("access_token")
    if status != 200 or not access or not isinstance(access, str):
        print(
            f"login failed http={status} mfa_required={data.get('mfa_required')}",
            file=sys.stderr,
        )
        sys.exit(1)
    parts = access.split(".")
    if len(parts) != 3:
        print("access token is not a JWT", file=sys.stderr)
        sys.exit(1)
    header = b64url_json(parts[0])
    payload = b64url_json(parts[1])
    iat = payload.get("iat")
    exp = payload.get("exp")
    if not isinstance(iat, int) or not isinstance(exp, int):
        print("JWT missing iat or exp", file=sys.stderr)
        sys.exit(1)
    alg = str(header.get("alg") or "?")
    render(alg=alg, iat=iat, exp=exp, lifetime_s=exp - iat, login_status=status)
    request(
        "POST",
        "/api/v1/users/logout",
        headers={"Authorization": f"Bearer {access}"},
    )
    if (exp - iat) >= 86400:
        sys.exit(1)
