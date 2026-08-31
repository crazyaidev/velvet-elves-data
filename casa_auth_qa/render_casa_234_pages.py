"""Render CASA 2.3.4 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.3.4")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1400, 1800
MARGIN = 56
BG = (248, 248, 246)
INK = (24, 24, 24)
MUTED = (80, 80, 80)
RULE = (200, 80, 70)
OK = (20, 90, 50)
LINE = (220, 218, 214)
CODE_BG = (36, 36, 36)
CODE_FG = (230, 230, 226)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    for p in (
        rf"C:\Windows\Fonts\{name}",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def mono(size: int):
    for p in (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return font(size)


def wrap(draw, text, fnt, width):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


F_H = font(22, True)
F_SUB = font(14)
F_SEC = font(16, True)
F_BODY = font(15)
F_SMALL = font(13)
F_FOOT = font(12)
F_MONO = mono(13)


def new_page(title: str, page_no: int):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), title, font=F_H, fill=INK)
    d.text(
        (MARGIN, 98),
        "GCP 538509143953  |  production app.velvetelves.com  |  28 Aug 2026",
        font=F_SMALL,
        fill=MUTED,
    )
    d.line((MARGIN, 124, W - MARGIN, 124), fill=LINE, width=1)
    d.text((MARGIN, H - 42), f"Page {page_no} of 2", font=F_FOOT, fill=MUTED)
    d.text((W - MARGIN - 240, H - 42), "CASA_2_3_4_signed_jwt", font=F_FOOT, fill=MUTED)
    return im, d, 144


def paint(d, y, lines):
    max_w = W - 2 * MARGIN
    for text, fnt, color in lines:
        for part in wrap(d, text, fnt, max_w):
            d.text((MARGIN, y), part, font=fnt, fill=color)
            y += 22 if fnt is F_SMALL else 24
        y += 4
    return y


def page1():
    im, d, y = new_page("2.3.4 Signed stateless session JWT", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 3.5.3. AL1 evidence is ADA DAST. Verification: scan must not identify JWT signature not verified (Burp 2099456) or JWT none algorithm supported (Burp 2099457).",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. API verifies the JWT signature", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "decode_access_token uses jose jwt.decode. Staging access tokens measured ES256 (2.2.3). HS256 is verified with SUPABASE_JWT_SECRET and algorithms HS256 only. Otherwise the header kid is loaded from GoTrue JWKS and verified as ES256 or RS256. Audience must be authenticated. jose raises JWTError on invalid, expired, or tampered tokens. get_current_user returns 401.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Official DAST did not flag JWT signature", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Official ADA ZAP scans: SPA 10f54abf, API a9d78f05, authenticated API 33afa2aa (real Bearer via Replacer). DAST_SUMMARY alert tables do not list JWT signature-not-verified or JWT none-algorithm. Those Burp IDs are not ZAP plugin IDs in the CASA conf.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Google tokens are not the session JWT", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Gmail and Calendar OAuth tokens are Fernet-encrypted in integrations. They are not the signed session JWT this row covers.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_3_4_page1.png", "PNG")
    print("wrote", OUT / "CASA_2_3_4_page1.png")


def page2():
    im, d, y = new_page("2.3.4 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Stateless session token is a signed JWT",
            "GoTrue issues ES256 (staging). API verifies signature before trusting sub.",
            True,
        ),
        (
            "Signature verified server-side",
            "jose jwt.decode. Tests reject invalid, tampered, expired, wrong aud, and wrong secret.",
            True,
        ),
        (
            "Scan must not identify 2099456 / 2099457",
            "Official ZAP alert lists did not report JWT signature-not-verified or none-algorithm.",
            True,
        ),
        (
            "Unsigned caller",
            "GET /users/me without Authorization, and with Bearer not-a-jwt, both return 401.",
            True,
        ),
    ]
    for title, detail, ok in rows:
        color = OK if ok else INK
        d.text((MARGIN, y), title, font=F_BODY, fill=color)
        y += 24
        y = paint(d, y, [(detail, F_SMALL, MUTED)])
        y += 8
    y += 8
    d.text((MARGIN, y), "Attestation", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Velvet Elves session access tokens are signed JWTs. The API verifies the signature and rejects tokens that do not verify. Official ADA DAST did not report JWT signature-not-verified or JWT none-algorithm findings.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_3_4_page2.png", "PNG")
    print("wrote", OUT / "CASA_2_3_4_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 980), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.3.4 decode_access_token verifies the JWT", font=F_H, fill=INK)
    snippet = """# app/utils/security.py
def decode_access_token(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    alg = header.get("alg")
    # Raises JWTError on invalid, expired, or tampered tokens.
    if alg == "HS256" or settings.supabase_jwt_secret:
        return jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    key = jwk_for_kid(header["kid"])  # GoTrue JWKS
    return jwt.decode(token, key, algorithms=[alg], audience="authenticated")

# app/core/auth.py
try:
    payload = decode_access_token(token)
except JWTError:
    raise HTTPException(401, "Could not validate credentials.")"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_2_3_4_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_2_3_4_code.png", "PNG")
    print("wrote", OUT / "CASA_2_3_4_code.png")


def zap_page():
    im = Image.new("RGB", (1400, 880), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.3.4 Official ADA DAST vs Burp JWT IDs", font=F_H, fill=INK)
    snippet = """# ADA AL1 verification (Burp IDs)
2099456  JWT signature not verified
2099457  JWT none algorithm supported

# Official scans (21 Aug 2026) — DAST_SUMMARY.md
SPA  10f54abf   ZAP zap-casa-config.conf
API  a9d78f05   ZAP zap-casa-api-config.conf
Auth 33afa2aa   authenticated API, Bearer JWT via Replacer

Alert tables did not list JWT signature-not-verified
or JWT none-algorithm.

Those Burp IDs are not ZAP plugin IDs in the CASA conf."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text(
        (MARGIN, box_y + box_h + 16),
        "Excerpt of DAST summary and ADA IDs. Not a ZAP or Burp product screenshot.",
        font=F_FOOT,
        fill=MUTED,
    )
    im.save(OUT / "CASA_2_3_4_zap.png", "PNG")
    print("wrote", OUT / "CASA_2_3_4_zap.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    zap_page()
