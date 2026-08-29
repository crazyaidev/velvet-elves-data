"""Render CASA 2.2.3 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.2.3")
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


F_H = font(22, True)
F_SUB = font(14)
F_SEC = font(16, True)
F_BODY = font(15)
F_SMALL = font(13)
F_FOOT = font(12)
F_MONO = mono(13)


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
    d.text((W - MARGIN - 280, H - 42), "CASA_2_2_3_stateless_expiry", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("2.2.3 Stateless access JWT expiry", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 3.3.4. AL1 is code, screenshot, or documentation of the validity period. Verification: expire within 24 hours of issue.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Access JWT is the stateless token", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Login returns an access JWT and a refresh token. The access JWT is stateless: the API verifies the signature and the exp claim. That is the object ADA 2.2.3 covers. The refresh token is a stateful GoTrue session (revoked on logout and password change) and is not this row.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Staging lifetime is 8 hours", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "On 28 Aug 2026, POST /users/login on api.stage.velvetelves.com issued an ES256 access JWT. exp minus iat is 28800 seconds (8.00 hours). The ADA cap is 86400 seconds (24 hours). The issued lifetime is 8 hours, still under the cap. The token itself is not shown.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Expiry is enforced at API and SPA", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "decode_access_token verifies the JWT. jose raises JWTError on expired or tampered tokens, and the API returns 401. The SPA reads exp and silent-refreshes about 60 seconds before expiry. Invite links, reset links, and Gmail or Calendar mailbox tokens are not the session JWT.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_2_3_page1.png", "PNG")
    print("wrote", OUT / "CASA_2_2_3_page1.png")


def page2():
    im, d, y = new_page("2.2.3 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Token is stateless",
            "Access JWT. Signature and exp are checked on each API call. No server session row is required to reject an expired JWT.",
            True,
        ),
        (
            "Expires within 24 hours of issue",
            "Staging 28 Aug 2026: exp minus iat = 28800 seconds (8.00 hours).",
            True,
        ),
        (
            "Refresh token is out of this row",
            "Stateful and revocable (2.2.1 / 2.2.2). ADA 2.2.3 applies to non-revocable stateless tokens.",
            True,
        ),
        (
            "Validity period documented",
            "Live iat/exp decode (token not shown) plus decode_access_token and SPA exp handling.",
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
                "The Velvet Elves session access token is a signed JWT that expires 8 hours after issue on staging, under ADA’s 24-hour cap. Expired tokens are rejected by JWT verification. This was measured from a live staging login without pasting the token.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_2_3_page2.png", "PNG")
    print("wrote", OUT / "CASA_2_2_3_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 980), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.2.3 API and SPA honor JWT exp", font=F_H, fill=INK)
    snippet = """# app/utils/security.py
def decode_access_token(token: str) -> dict:
    \"\"\"Raises JWTError on invalid, expired, or tampered tokens.
    Payload includes exp (unix timestamp).\"\"\"
    return jwt.decode(...)  # jose verifies exp

# src/utils/jwt.ts
export function getTokenExpirationMs(token: string): number | null {
  const claims = decodeJwtPayload(token)
  if (!claims || typeof claims.exp !== 'number') return null
  return claims.exp * 1000
}

# AuthContext.tsx  (silent refresh ~60s before exp)
const remainingUntilRefresh = expMs - Date.now() - TOKEN_REFRESH_LEAD_MS
# TOKEN_REFRESH_LEAD_MS = 60 * 1000"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_2_2_3_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_2_2_3_code.png", "PNG")
    print("wrote", OUT / "CASA_2_2_3_code.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
