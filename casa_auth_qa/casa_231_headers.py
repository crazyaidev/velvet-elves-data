"""Staging: login does not set a session cookie (CASA 2.3.1). Never prints tokens."""
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
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.3.1")
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
) -> tuple[int, dict[str, str], str]:
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, {k: v for k, v in resp.headers.items()}, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, {k: v for k, v in exc.headers.items()}, body


def cookie_names(headers: dict[str, str]) -> list[str]:
    names: list[str] = []
    for key, value in headers.items():
        if key.lower() != "set-cookie":
            continue
        name = value.split("=", 1)[0].strip()
        if name:
            names.append(name)
    return names


def header_present(headers: dict[str, str], name: str) -> bool:
    lower = name.lower()
    return any(k.lower() == lower for k in headers)


def json_keys(raw: str) -> list[str]:
    try:
        data = json.loads(raw) if raw.strip().startswith("{") else {}
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []
    return sorted(data.keys())


def render(rows: list[tuple[str, str]]) -> None:
    W, H = 1400, 820
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text((48, 32), "2.3.1  Staging login is not a session cookie", font=font(22, True), fill=(24, 24, 24))
    d.text(
        (48, 68),
        "POST /users/login over HTTPS. Cookie names only. Token values are not shown.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for label, value in rows:
        d.text((48, y), label, font=font(15, True), fill=(80, 80, 80))
        color = (20, 90, 50) if value in {"none", "YES"} or value.startswith("HTTP 200") else (24, 24, 24)
        d.text((480, y), value[:70], font=font(15), fill=color)
        y += 44
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_2_3_1_headers  |  28 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_2_3_1_headers.png"
    im.save(out, "PNG")
    print("wrote", out)
    for label, value in rows:
        print(f"  {label}: {value}")


if __name__ == "__main__":
    if not PASSWORD:
        print("Set QA_PASSWORD", file=sys.stderr)
        sys.exit(2)
    login_body = urllib.parse.urlencode({"username": EMAIL, "password": PASSWORD}).encode()
    status, headers, raw = request(
        "POST",
        "/api/v1/users/login",
        data=login_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    names = cookie_names(headers)
    keys = json_keys(raw)
    access = None
    try:
        parsed = json.loads(raw) if raw.strip().startswith("{") else {}
        if isinstance(parsed.get("access_token"), str):
            access = parsed["access_token"]
    except json.JSONDecodeError:
        parsed = {}
    session_keys = [k for k in ("access_token", "refresh_token", "token_type", "user") if k in keys]
    rows = [
        ("URL", "https://api.stage.velvetelves.com/api/v1/users/login"),
        ("Login", f"HTTP {status}"),
        ("Set-Cookie names", ", ".join(names) if names else "none"),
        ("HSTS header", "YES" if header_present(headers, "Strict-Transport-Security") else "NO"),
        ("JSON session keys", ", ".join(session_keys) if session_keys else "(none)"),
        ("Session in JSON body", "YES" if "access_token" in keys else "NO"),
    ]
    render(rows)
    if access:
        request("POST", "/api/v1/users/logout", headers={"Authorization": f"Bearer {access}"})
    if status != 200:
        sys.exit(1)
    if names:
        sessionish = [
            n
            for n in names
            if n.lower()
            in {
                "session",
                "sessionid",
                "access_token",
                "refresh_token",
                "jwt",
                "sb-access-token",
                "sb-refresh-token",
            }
        ]
        if sessionish:
            print("session-like Set-Cookie names:", sessionish, file=sys.stderr)
            sys.exit(1)
