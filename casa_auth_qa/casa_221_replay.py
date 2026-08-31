"""Staging: logout revokes refresh (CASA 2.2.1). Requires QA_PASSWORD. Never prints tokens."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.2.1")
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
            return resp.status, body.replace("\n", " ")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body.replace("\n", " ")


def render(rows: list[tuple[int, str, int, str]]) -> None:
    W, H = 1400, 720
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text((48, 32), "2.2.1  Staging logout then refresh replay", font=font(22, True), fill=(24, 24, 24))
    d.text(
        (48, 66),
        "Refresh token captured at login is replayed after logout. Tokens are not shown.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 110
    d.text((48, y), "#", font=font(13, True), fill=(80, 80, 80))
    d.text((90, y), "HTTP", font=font(13, True), fill=(80, 80, 80))
    d.text((180, y), "Call", font=font(13, True), fill=(80, 80, 80))
    d.text((620, y), "Response", font=font(13, True), fill=(80, 80, 80))
    y = 138
    d.line((48, y, W - 48, y), fill=(220, 218, 214), width=1)
    y = 156
    for n, label, status, body in rows:
        want = {1: 200, 2: 204, 3: 401}.get(n)
        color = (20, 90, 50) if status == want else (140, 40, 40)
        d.text((48, y), str(n), font=font(15), fill=color)
        d.text((90, y), str(status), font=font(15, True), fill=color)
        d.text((180, y), label, font=font(13), fill=(80, 80, 80))
        d.text((620, y), body[:70], font=font(13), fill=(80, 80, 80))
        y += 40
    d.text((48, H - 40), "api.stage.velvetelves.com  |  CASA 2.2.1", font=font(12), fill=(80, 80, 80))
    out = OUT / "CASA_2_2_1_refresh_replay.png"
    im.save(out, "PNG")
    print("wrote", out)
    for n, label, status, _body in rows:
        print(f"  {n} {status} {label}")


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
        print(f"login failed http={status} body={raw[:160]}", file=sys.stderr)
        sys.exit(1)
    access = data.get("access_token")
    refresh = data.get("refresh_token")
    if status != 200 or not access or not refresh:
        print(
            f"login failed http={status} mfa_required={data.get('mfa_required')} has_refresh={bool(refresh)}",
            file=sys.stderr,
        )
        sys.exit(1)
    logout_status, logout_body = request(
        "POST",
        "/api/v1/users/logout",
        headers={"Authorization": f"Bearer {access}"},
    )
    replay_status, replay_body = request(
        "POST",
        "/api/v1/users/refresh",
        data=json.dumps({"refresh_token": refresh}).encode(),
        headers={"Content-Type": "application/json"},
    )
    render(
        [
            (1, "POST /users/login  (refresh token issued, not shown)", status, "session issued"),
            (2, "POST /users/logout  Authorization Bearer", logout_status, logout_body or "204 empty"),
            (3, "POST /users/refresh  same refresh token replayed", replay_status, replay_body),
        ]
    )
    if logout_status != 204 or replay_status != 401:
        sys.exit(1)
