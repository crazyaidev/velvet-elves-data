"""Staging: OAuth redirect_to allowlist and forged state (CASA 3.2.2).

Does not complete consent. Does not print Fernet state or PKCE values.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.2.2")
OUT.mkdir(parents=True, exist_ok=True)
ALLOWED = "https://app.stage.velvetelves.com/oauth/callback"
EVIL = "https://evil.example/steal"


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def post(path: str, body: dict) -> tuple[int, str]:
    data = json.dumps(body).encode()
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    req = urllib.request.Request(f"{API}{path}", data=data, method="POST", headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def snippet(raw: str, limit: int = 110) -> str:
    return " ".join(raw.split())[:limit]


def allowed_redirect_origin(raw: str) -> str:
    data = json.loads(raw)
    url = data.get("url") or ""
    q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query, keep_blank_values=True))
    redirect_to = q.get("redirect_to") or ""
    parsed = urllib.parse.urlparse(redirect_to)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "(absent)"
    return origin


def render(rows: list[tuple[str, int, str, bool]]) -> None:
    W, H = 1400, 980
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "3.2.2  Staging rejects foreign redirect_to and forged state",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Fernet ciphertext and PKCE values not shown. Consent was not completed.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for label, status, detail, ok in rows:
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=(80, 80, 80))
        y += 26
        d.text((48, y), f"HTTP {status}  {detail}", font=font(15), fill=color)
        y += 48
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_3_2_2_deny  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_3_2_2_deny.png"
    im.save(out, "PNG")
    print("wrote", out)


if __name__ == "__main__":
    evil_status, evil_body = post(
        "/api/v1/users/oauth/google/start",
        {"redirect_to": EVIL},
    )
    print("evil start", evil_status, snippet(evil_body, 160))

    ok_status, ok_body = post(
        "/api/v1/users/oauth/google/start",
        {"redirect_to": ALLOWED},
    )
    origin = "(parse failed)"
    if ok_status == 200:
        origin = allowed_redirect_origin(ok_body)
    print("allowed start", ok_status, "redirect_to origin", origin)

    exch_status, exch_body = post(
        "/api/v1/users/oauth/google/exchange",
        {"code": "placeholder-not-exchanged", "state": "not-a-real-fernet-token"},
    )
    print("exchange", exch_status, snippet(exch_body, 160))

    rows = [
        (
            "POST /users/oauth/google/start  redirect_to=https://evil.example/steal",
            evil_status,
            snippet(evil_body),
            evil_status == 400,
        ),
        (
            "POST /users/oauth/google/start  redirect_to=https://app.stage.velvetelves.com/oauth/callback",
            ok_status,
            f"redirect_to origin {origin}  (allowlisted; state redacted; flow not completed)",
            ok_status == 200 and "app.stage.velvetelves.com" in origin,
        ),
        (
            "POST /users/oauth/google/exchange  state=not-a-real-fernet-token",
            exch_status,
            snippet(exch_body),
            exch_status == 400 and "Invalid or expired OAuth state" in exch_body,
        ),
    ]
    render(rows)
    if evil_status != 400:
        raise SystemExit("foreign redirect_to was not 400")
    if ok_status != 200:
        raise SystemExit("allowlisted redirect_to was not 200")
    if exch_status != 400 or "Invalid or expired OAuth state" not in exch_body:
        raise SystemExit("forged state was not 400 Invalid or expired OAuth state")
