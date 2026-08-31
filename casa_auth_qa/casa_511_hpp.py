"""CASA 5.1.1: staging duplicate query keys bind as one typed value."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.1.1")
OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.stage.velvetelves.com"
LONG_Q = "x" * 161


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def request(path: str) -> tuple[int, str]:
    req = urllib.request.Request(
        f"{API}{path}",
        method="GET",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body[:240]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body[:240]


def compact(text: str, limit: int = 88) -> str:
    return " ".join(text.split())[:limit]


def render(rows: list[tuple[str, int, str, bool]]) -> None:
    W, H = 1400, 980
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "5.1.1  Staging duplicate query keys bind as one typed value",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Public help search max_length=160. Last duplicate is bound. Concatenation would fail the short-last case.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 118
    for label, status, detail, ok in rows:
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=(80, 80, 80))
        y += 26
        d.text((48, y), f"HTTP {status}  {detail}", font=font(15), fill=color)
        y += 48
    d.text((48, H - 48), "staging  |  CASA_5_1_1_hpp  |  31 Aug 2026", font=font(12), fill=(80, 80, 80))
    out = OUT / "CASA_5_1_1_hpp.png"
    im.save(out, "PNG")
    print("wrote", out)


if __name__ == "__main__":
    long_q = urllib.parse.quote(LONG_Q, safe="")
    health_status, health_body = request("/api/v1/health?x=1&x=2")
    last_long_status, last_long_body = request(f"/api/v1/public/help/search?q=ok&q={long_q}")
    last_short_status, last_short_body = request(f"/api/v1/public/help/search?q={long_q}&q=ok")
    page_status, page_body = request("/api/v1/teams?page=1&page=2")
    pay_status, pay_body = request(
        "/api/v1/public/pay/invoices/00000000-0000-0000-0000-000000000000?token=aaa&token=bbb"
    )

    try:
        health_ok = health_status == 200 and isinstance(json.loads(health_body), dict)
    except json.JSONDecodeError:
        health_ok = False
    last_long_ok = last_long_status == 422 and "string_too_long" in last_long_body
    last_short_ok = last_short_status == 200 and last_short_body.lstrip().startswith("[")
    page_ok = page_status == 401
    pay_ok = pay_status == 403 and "Invalid or expired payment link" in pay_body

    rows = [
        (
            "GET /health?x=1&x=2  extra keys ignored",
            health_status,
            compact(health_body),
            health_ok,
        ),
        (
            "GET /public/help/search?q=ok&q=<161 chars>  last value too long",
            last_long_status,
            compact(last_long_body),
            last_long_ok,
        ),
        (
            "GET /public/help/search?q=<161 chars>&q=ok  last value accepted (not concatenated)",
            last_short_status,
            "JSON array of published help hits" if last_short_ok else compact(last_short_body),
            last_short_ok,
        ),
        (
            "GET /teams?page=1&page=2  unsigned; last page is a valid int",
            page_status,
            compact(page_body),
            page_ok,
        ),
        (
            "GET /public/pay/invoices/{id}?token=aaa&token=bbb  last token only",
            pay_status,
            compact(pay_body),
            pay_ok,
        ),
    ]
    for label, status, detail, ok in rows:
        print(("OK " if ok else "!! "), label, status, detail)
    render(rows)
    if not (health_ok and last_long_ok and last_short_ok and page_ok and pay_ok):
        raise SystemExit("5.1.1 probe failed")
