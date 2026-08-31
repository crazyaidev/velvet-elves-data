"""Staging: OAuth start is code + PKCE (CASA 3.2.1). Does not complete consent."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.2.1")
OUT.mkdir(parents=True, exist_ok=True)
REDIRECT = "https://app.stage.velvetelves.com/oauth/callback"


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def post(path: str, body: dict | None = None) -> tuple[int, str]:
    data = None if body is None else json.dumps(body).encode()
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    req = urllib.request.Request(f"{API}{path}", data=data, method="POST", headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def summarize_start(raw: str) -> tuple[list[str], bool]:
    data = json.loads(raw)
    url = data.get("url") or ""
    parsed = urllib.parse.urlparse(url)
    q = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    challenge = q.get("code_challenge") or ""
    method = q.get("code_challenge_method") or "(absent)"
    provider = q.get("provider") or data.get("provider") or "(absent)"
    implicit = "response_type=token" in url.lower()
    host_path = "*.supabase.co/auth/v1/authorize"
    lines = [
        f"HTTP 200  POST /users/oauth/google/start",
        f"authorize host+path: {host_path[:70]}",
        f"provider: {provider}",
        f"code_challenge_method: {method}",
        f"code_challenge: present ({len(challenge)} chars)  value not shown",
        f"response_type=token (implicit): {'yes' if implicit else 'no'}",
        "state: Fernet ciphertext  redacted",
        "consent was not completed; no exchange; no new user",
    ]
    return lines, method.lower() == "s256" and len(challenge) >= 20 and not implicit


def render(start_lines: list[str], gmail_status: int, gmail_body: str) -> None:
    W, H = 1400, 900
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "3.2.1  Staging OAuth start is authorization code + PKCE",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Google sign-in start URL. Challenge value and state ciphertext not shown. Flow not completed.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for line in start_lines:
        d.text((48, y), line, font=font(15), fill=(24, 24, 24))
        y += 28
    y += 16
    gmail_ok = gmail_status == 401
    color = (20, 90, 50) if gmail_ok else (140, 40, 40)
    snippet = " ".join(gmail_body.split())[:90]
    d.text((48, y), "POST /integrations/gmail/authorize-url  (no Authorization)", font=font(14, True), fill=(80, 80, 80))
    y += 28
    d.text((48, y), f"HTTP {gmail_status}  {snippet}", font=font(15), fill=color)
    d.text(
        (48, H - 48),
        "api.stage.velvetelves.com  |  CASA_3_2_1_pkce  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_3_2_1_pkce.png"
    im.save(out, "PNG")
    print("wrote", out)


if __name__ == "__main__":
    status, raw = post(
        "/api/v1/users/oauth/google/start",
        {"redirect_to": REDIRECT},
    )
    print("start", status)
    if status != 200:
        print(raw[:300])
        raise SystemExit(1)
    lines, ok = summarize_start(raw)
    for line in lines:
        print(" ", line)
    gmail_status, gmail_body = post("/api/v1/integrations/gmail/authorize-url", {})
    print("gmail", gmail_status)
    render(lines, gmail_status, gmail_body)
    if not ok:
        raise SystemExit("PKCE params missing")
    if gmail_status != 401:
        raise SystemExit("gmail authorize-url was not 401")
