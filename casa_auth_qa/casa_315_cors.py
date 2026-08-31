"""Staging CORS: SPA origin allowed, foreign origin not (CASA 3.1.5)."""
from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
PATH = "/api/v1/users/me"
SPA = "https://app.stage.velvetelves.com"
EVIL = "https://evil.example"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.5")
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def header(headers: dict[str, str], name: str) -> str:
    lower = name.lower()
    for key, value in headers.items():
        if key.lower() == lower:
            return value
    return "(absent)"


def request(
    method: str,
    *,
    origin: str,
    extra: dict[str, str] | None = None,
) -> tuple[int, str]:
    h = {
        "Accept": "application/json",
        "Origin": origin,
    }
    if extra:
        h.update(extra)
    req = urllib.request.Request(f"{API}{PATH}", method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            acao = header({k: v for k, v in resp.headers.items()}, "Access-Control-Allow-Origin")
            return resp.status, acao
    except urllib.error.HTTPError as exc:
        acao = header({k: v for k, v in exc.headers.items()}, "Access-Control-Allow-Origin")
        return exc.code, acao


def render(rows: list[tuple[str, int, str]]) -> None:
    W, H = 1400, 860
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "3.1.5  Staging CORS does not echo a foreign Origin",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "SPA origin is allowlisted. evil.example is not. No Authorization sent.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for label, status, acao in rows:
        spa_ok = "app.stage.velvetelves.com" in acao
        evil_ok = acao == "(absent)" and "evil" in label
        color = (20, 90, 50) if (spa_ok or evil_ok) else (140, 40, 40)
        d.text((48, y), label, font=font(14, True), fill=(80, 80, 80))
        d.text((48, y + 26), f"HTTP {status}   Access-Control-Allow-Origin: {acao[:70]}", font=font(14), fill=color)
        y += 78
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_3_1_5_cors  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_3_1_5_cors.png"
    im.save(out, "PNG")
    print("wrote", out)
    for label, status, acao in rows:
        print(f"  {status} {acao}  {label}")


if __name__ == "__main__":
    preflight = {
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization",
    }
    rows = [
        (
            f"OPTIONS /users/me  Origin {SPA}",
            *request("OPTIONS", origin=SPA, extra=preflight),
        ),
        (
            f"OPTIONS /users/me  Origin {EVIL}",
            *request("OPTIONS", origin=EVIL, extra=preflight),
        ),
        (
            f"GET /users/me  Origin {EVIL}  (no Authorization)",
            *request("GET", origin=EVIL),
        ),
    ]
    render(rows)
    spa_status, spa_acao = rows[0][1], rows[0][2]
    evil_opt_acao = rows[1][2]
    evil_get_status, evil_get_acao = rows[2][1], rows[2][2]
    if SPA not in spa_acao:
        raise SystemExit("SPA origin was not allowlisted")
    if evil_opt_acao != "(absent)" and EVIL in evil_opt_acao:
        raise SystemExit("foreign origin was echoed")
    if evil_get_status != 401:
        raise SystemExit("unsigned GET was not 401")
    if EVIL in evil_get_acao:
        raise SystemExit("foreign origin echoed on GET")
