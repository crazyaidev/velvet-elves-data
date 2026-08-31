"""Staging: extra policy fields on PATCH /users/me (CASA 3.1.2)."""
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
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.2")
OUT.mkdir(parents=True, exist_ok=True)
EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD")
ATTACK = {
    "role": "Vendor",
    "tenant_id": "00000000-0000-0000-0000-000000000001",
    "is_platform_admin": True,
    "is_active": False,
}


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
    limit: int = 100,
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


def policy_summary(raw: str) -> str:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return "unparsed"
    if not isinstance(data, dict):
        return "unparsed"
    role = data.get("role")
    active = data.get("is_active")
    platform = data.get("is_platform_admin")
    tenant = data.get("tenant_id")
    tenant_note = "uuid" if isinstance(tenant, str) and len(tenant) >= 8 else "?"
    return f"role={role} active={active} platform_admin={platform} tenant={tenant_note}"


def render(rows: list[tuple[str, int, str]]) -> None:
    W, H = 1400, 780
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "3.1.2  Staging unsigned PATCH /users/me with policy extras",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Body included role, tenant_id, is_platform_admin, is_active. No tokens. Tenant id not shown.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for label, status, body in rows:
        ok = status in (200, 401)
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=(80, 80, 80))
        d.text((520, y), f"HTTP {status}", font=font(15, True), fill=color)
        d.text((680, y), body[:52], font=font(12), fill=(80, 80, 80))
        y += 52
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_3_1_2_ignore  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_3_1_2_ignore.png"
    im.save(out, "PNG")
    print("wrote", out)
    for label, status, _body in rows:
        print(f"  {status} {label}")


if __name__ == "__main__":
    payload = json.dumps(ATTACK).encode()
    json_headers = {"Content-Type": "application/json"}
    rows = [
        (
            "PATCH /users/me extras  (no Authorization)",
            *request(
                "PATCH",
                "/api/v1/users/me",
                data=payload,
                headers=json_headers,
            ),
        ),
    ]
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
            auth = {"Authorization": f"Bearer {access}"}
            before_s, before_b = request(
                "GET", "/api/v1/users/me", headers=auth, limit=200_000
            )
            patch_s, _patch_b = request(
                "PATCH",
                "/api/v1/users/me",
                data=payload,
                headers={**json_headers, **auth},
            )
            after_s, after_b = request(
                "GET", "/api/v1/users/me", headers=auth, limit=200_000
            )
            rows.append(("GET /users/me before extras", before_s, policy_summary(before_b)))
            rows.append(("PATCH /users/me extras (session)", patch_s, "extras only; no profile fields"))
            rows.append(("GET /users/me after extras", after_s, policy_summary(after_b)))
            request("POST", "/api/v1/users/logout", headers=auth)
            if before_s == 200 and after_s == 200:
                if policy_summary(before_b) != policy_summary(after_b):
                    print("policy fields changed unexpectedly", file=sys.stderr)
                    render(rows)
                    raise SystemExit(1)
        else:
            print(
                f"login skipped http={status} mfa={data.get('mfa_required')}",
                file=sys.stderr,
            )
    render(rows)
    if rows[0][1] != 401:
        raise SystemExit(1)
