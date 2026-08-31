"""Staging: account-change routes reject unsigned callers (CASA 2.4.1)."""
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
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.4.1")
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
    limit: int = 80,
) -> tuple[int, str]:
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body.replace("\n", " ")[:limit]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body.replace("\n", " ")[:limit]


def render(rows: list[tuple[str, int, str]]) -> None:
    W, H = 1400, 820
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "2.4.1  Staging account APIs require a valid session",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Unsigned PATCH /users/me is rejected. A valid JWT is accepted. Bodies truncated; no tokens.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for label, status, body in rows:
        ok = status in (200, 401)
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), label, font=font(15, True), fill=(80, 80, 80))
        d.text((640, y), f"HTTP {status}", font=font(15, True), fill=color)
        shown = "JSON user (email redacted)" if status == 200 else body[:42]
        d.text((800, y), shown, font=font(13), fill=(80, 80, 80))
        y += 48
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_2_4_1_reject  |  28 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_2_4_1_reject.png"
    im.save(out, "PNG")
    print("wrote", out)
    for label, status, _body in rows:
        print(f"  {status} {label}")


if __name__ == "__main__":
    patch_body = b"{}"
    json_headers = {"Content-Type": "application/json"}
    rows = [
        (
            "PATCH /users/me  (no Authorization)",
            *request("PATCH", "/api/v1/users/me", data=patch_body, headers=json_headers),
        ),
        (
            "PATCH /users/me  Bearer not-a-jwt",
            *request(
                "PATCH",
                "/api/v1/users/me",
                data=patch_body,
                headers={**json_headers, "Authorization": "Bearer not-a-jwt"},
            ),
        ),
        ("GET /users/me  (no Authorization)", *request("GET", "/api/v1/users/me")),
    ]
    access = None
    if PASSWORD:
        login_body = urllib.parse.urlencode(
            {"username": EMAIL, "password": PASSWORD}
        ).encode()
        status, raw = request(
            "POST",
            "/api/v1/users/login",
            data=login_body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            limit=200_000,
        )
        try:
            data = json.loads(raw) if raw.strip().startswith("{") else {}
        except json.JSONDecodeError:
            data = {}
        access = data.get("access_token") if status == 200 else None
        if isinstance(access, str) and access:
            me_status, _me_body = request(
                "GET",
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access}"},
            )
            rows.append(("GET /users/me  (valid session JWT)", me_status, "redacted"))
            request(
                "POST",
                "/api/v1/users/logout",
                headers={"Authorization": f"Bearer {access}"},
            )
        else:
            print(
                f"login skipped authenticated GET http={status} mfa={data.get('mfa_required')}",
                file=sys.stderr,
            )
    render(rows)
    unsigned = rows[:3]
    if any(status != 401 for _label, status, _body in unsigned):
        raise SystemExit(1)
    if len(rows) == 4 and rows[3][1] != 200:
        raise SystemExit(1)
