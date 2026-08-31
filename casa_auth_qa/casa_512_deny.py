"""CASA 5.1.2: staging does not 302 to a user-supplied foreign URL."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.1.2")
OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.stage.velvetelves.com"
SPA = "https://app.stage.velvetelves.com"
EVIL = "https://evil.example/steal"
HOOK = "00000000-0000-0000-0000-000000000000"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def compact(text: str, limit: int = 88) -> str:
    return " ".join(text.split())[:limit]


def request(
    method: str,
    url: str,
    *,
    data: bytes | None = None,
    headers: dict | None = None,
) -> tuple[int, str, str]:
    h = {"Accept": "application/json,text/html;q=0.9"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with OPENER.open(req, timeout=25) as resp:
            location = resp.headers.get("Location") or "(none)"
            body = resp.read().decode("utf-8", errors="replace")[:200]
            return resp.status, location, body
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location") if exc.headers else None
        location = location or "(none)"
        body = exc.read().decode("utf-8", errors="replace")[:200]
        return exc.code, location, body


def render(rows: list[tuple[str, int, str, str, bool]]) -> None:
    W, H = 1400, 980
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "5.1.2  Staging does not redirect to a foreign URL",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Location is captured without following redirects. OAuth consent was not completed.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 118
    for label, status, location, detail, ok in rows:
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=(80, 80, 80))
        y += 24
        d.text((48, y), f"HTTP {status}  Location {location}", font=font(15), fill=color)
        y += 22
        d.text((48, y), detail, font=font(13), fill=(80, 80, 80))
        y += 44
    d.text((48, H - 48), "staging  |  CASA_5_1_2_deny  |  31 Aug 2026", font=font(12), fill=(80, 80, 80))
    out = OUT / "CASA_5_1_2_deny.png"
    im.save(out, "PNG")
    print("wrote", out)


if __name__ == "__main__":
    oauth_status, oauth_loc, oauth_body = request(
        "POST",
        f"{API}/api/v1/users/oauth/google/start",
        data=json.dumps({"redirect_to": EVIL}).encode(),
        headers={"Content-Type": "application/json"},
    )
    reset_status, reset_loc, reset_body = request(
        "POST",
        f"{API}/api/v1/users/password-reset/request",
        data=json.dumps(
            {
                "email": "casa512-noreply@example.com",
                "redirect_to": EVIL,
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    ads_status, ads_loc, ads_body = request(
        "GET",
        f"{API}/api/v1/ads/{HOOK}/click",
    )
    spa_status, spa_loc, spa_body = request(
        "GET",
        f"{SPA}/?next={EVIL}",
        headers={"Accept": "text/html"},
    )

    oauth_ok = oauth_status == 400 and "evil.example" not in oauth_loc
    reset_ok = (
        reset_status == 202
        and "evil.example" not in reset_loc
        and "evil.example" not in reset_body.lower()
    )
    ads_ok = ads_status in (400, 404) and "evil.example" not in ads_loc
    spa_ok = spa_status in (200, 301, 302, 304) and "evil.example" not in spa_loc.lower()

    rows = [
        (
            "POST /users/oauth/google/start  redirect_to=https://evil.example/steal",
            oauth_status,
            oauth_loc,
            compact(oauth_body),
            oauth_ok,
        ),
        (
            "POST /users/password-reset/request  disallowed redirect_to ignored",
            reset_status,
            reset_loc,
            compact(reset_body),
            reset_ok,
        ),
        (
            "GET /ads/{uuid}/click  unknown hook; no user-supplied URL",
            ads_status,
            ads_loc,
            compact(ads_body),
            ads_ok,
        ),
        (
            "SPA GET /?next=https://evil.example/steal  no Location to that host",
            spa_status,
            spa_loc,
            "HTML shell" if "<!doctype html>" in spa_body.lower() or "<html" in spa_body.lower() else compact(spa_body),
            spa_ok,
        ),
    ]
    for label, status, location, detail, ok in rows:
        print(("OK " if ok else "!! "), label, status, "Location", location, detail)
    render(rows)
    if not (oauth_ok and reset_ok and ads_ok and spa_ok):
        raise SystemExit("5.1.2 probe failed")
