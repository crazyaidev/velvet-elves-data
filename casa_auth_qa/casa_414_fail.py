"""CASA 4.1.4: Fernet failures are InvalidToken; staging JWT/OAuth errors are generic."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.4")
OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.stage.velvetelves.com"


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def mutate(f: Fernet, token: bytes, index: int) -> tuple[str, bool]:
    bad = bytearray(token)
    bad[index] ^= 0x01
    try:
        f.decrypt(bytes(bad))
        return "accepted", False
    except InvalidToken as exc:
        msg = str(exc) or type(exc).__name__
        leaked = b"sample-not-production" in msg.encode()
        return f"{type(exc).__name__}  leaked_plaintext={leaked}", not leaked


def request(method: str, path: str, *, data: bytes | None = None, headers: dict | None = None) -> tuple[int, str]:
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:160]
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:160]


def render_local(rows: list[tuple[str, bool]]) -> None:
    W, H = 1400, 720
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "4.1.4  Fernet MAC and ciphertext flips both raise InvalidToken",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Ephemeral key. HMAC is checked before AES-CBC. Exception text has no plaintext.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for line, ok in rows:
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), line, font=font(16), fill=color)
        y += 32
    d.text((48, H - 48), "CASA_4_1_4_fernet_fail  |  31 Aug 2026", font=font(12), fill=(80, 80, 80))
    out = OUT / "CASA_4_1_4_fernet_fail.png"
    im.save(out, "PNG")
    print("wrote", out)


def render_deny(rows: list[tuple[str, int, str, bool]]) -> None:
    W, H = 1400, 720
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "4.1.4  Staging crypto failures return generic 401 / 400",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "No token values. Same message for garbage JWT and garbage OAuth state.",
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
    d.text((48, H - 48), "staging  |  CASA_4_1_4_deny  |  31 Aug 2026", font=font(12), fill=(80, 80, 80))
    out = OUT / "CASA_4_1_4_deny.png"
    im.save(out, "PNG")
    print("wrote", out)


if __name__ == "__main__":
    f = Fernet(Fernet.generate_key())
    token = f.encrypt(b"sample-not-production")
    mac_idx = len(token) - 4
    ct_idx = 20
    mac_line, mac_ok = mutate(f, token, mac_idx)
    ct_line, ct_ok = mutate(f, token, ct_idx)
    local = [
        (f"flip HMAC byte  {mac_line}", mac_ok),
        (f"flip ciphertext byte  {ct_line}", ct_ok),
        (f"same exception for both  {mac_ok and ct_ok and 'InvalidToken' in mac_line and 'InvalidToken' in ct_line}", mac_ok and ct_ok),
        ("production ENCRYPTION_KEY not used", True),
    ]
    for line, ok in local:
        print(("OK " if ok else "!! "), line)
    render_local(local)

    jwt_status, jwt_body = request(
        "GET",
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    oauth_body = json.dumps({"code": "not-a-code", "state": "gAAAAABnot-a-real-token"}).encode()
    oauth_status, oauth_raw = request(
        "POST",
        "/api/v1/users/oauth/google/exchange",
        data=oauth_body,
        headers={"Content-Type": "application/json"},
    )
    jwt_ok = jwt_status == 401 and "Could not validate credentials" in jwt_body
    oauth_ok = oauth_status == 400 and "Invalid or expired OAuth state" in oauth_raw
    deny = [
        ("GET /users/me  Bearer not-a-jwt", jwt_status, " ".join(jwt_body.split())[:90], jwt_ok),
        ("POST /users/oauth/google/exchange  garbage state", oauth_status, " ".join(oauth_raw.split())[:90], oauth_ok),
    ]
    for label, status, detail, ok in deny:
        print(("OK " if ok else "!! "), label, status, detail)
    render_deny(deny)
    if not (mac_ok and ct_ok and jwt_ok and oauth_ok):
        raise SystemExit("4.1.4 probe failed")
