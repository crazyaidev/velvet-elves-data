"""Render CASA 2.3.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.3.1")
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
    d.text((W - MARGIN - 260, H - 42), "CASA_2_3_1_cookie_secure", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("2.3.1 Cookie Secure attribute", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 3.4.1. The requirement applies to cookie-based session tokens. AL1 evidence is ADA DAST. Verification: the scan must not identify TLS cookie without secure flag set (Burp 5243392; ZAP plugin 10011).",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Session tokens are not cookies", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Login is POST /users/login. The API returns access_token and refresh_token in the JSON body. FastAPI OAuth2PasswordBearer reads Authorization Bearer. The SPA stores velvet_elves_token and velvet_elves_refresh_token in localStorage and sends the access JWT as a Bearer header. The API does not Set-Cookie a session token.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Staging login sets no session cookie", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "On 28 Aug 2026, POST /users/login on api.stage.velvetelves.com returned HTTP 200 over HTTPS. Set-Cookie names: none. Strict-Transport-Security was present. The session fields were in the JSON body. Token values are not shown.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Official DAST did not flag cookie Secure", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Official ADA ZAP scans: SPA 10f54abf, API a9d78f05, authenticated API 33afa2aa. The SPA CASA config maps plugin 10011 Cookie Without Secure Flag to FAIL. Those alert lists did not include Cookie Without Secure Flag. There is no session cookie for the Secure attribute to apply to. The app and API are HTTPS; the API sends HSTS.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_3_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_2_3_1_page1.png")


def page2():
    im, d, y = new_page("2.3.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Cookie-based session token",
            "No. Session is a Bearer JWT in localStorage, not a Set-Cookie session.",
            True,
        ),
        (
            "Scan must not identify TLS cookie without Secure",
            "Official ZAP SPA/API/auth scans did not report plugin 10011 Cookie Without Secure Flag.",
            True,
        ),
        (
            "Transport is HTTPS",
            "Login URL is https. API responses include Strict-Transport-Security.",
            True,
        ),
        (
            "Secure attribute on a session cookie",
            "Not applicable. There is no session cookie to mark Secure.",
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
                "ADA 2.3.1 applies to cookie-based session tokens. Velvet Elves does not issue a session cookie. Login returns a JWT in JSON; the client sends Authorization Bearer over HTTPS. Official ADA DAST did not identify a TLS cookie without the Secure flag.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_3_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_2_3_1_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 980), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.3.1 Session is Bearer plus localStorage", font=F_H, fill=INK)
    snippet = """# AuthContext.tsx
function persistTokens(token: string, refreshToken: string | null): void {
  localStorage.setItem(TOKEN_KEY, token)  // velvet_elves_token
  if (refreshToken) localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
}

# src/utils/api.ts
if (token) headers['Authorization'] = `Bearer ${token}`

# app/core/auth.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
# WWW-Authenticate: Bearer  — not Set-Cookie

# app/core/security_headers.py
"Strict-Transport-Security": "max-age=31536000; includeSubDomains" """
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_2_3_1_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_2_3_1_code.png", "PNG")
    print("wrote", OUT / "CASA_2_3_1_code.png")


def zap_page():
    im = Image.new("RGB", (1400, 920), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.3.1 Official ADA ZAP cookie-Secure rule", font=F_H, fill=INK)
    snippet = """# zap-casa-config.conf  (SPA — FAIL)
10010    FAIL    (Cookie No HttpOnly Flag)
10011    FAIL    (Cookie Without Secure Flag)

# Official scans (21 Aug 2026) — DAST_SUMMARY.md
SPA  10f54abf   https://app.stage.velvetelves.com
API  a9d78f05   https://api.stage.velvetelves.com
Auth 33afa2aa   authenticated API, Bearer JWT (not a cookie)

Alert lists did not include Cookie Without Secure Flag
or Cookie No HttpOnly Flag.

ADA AL1: scan shall not identify Burp 5243392
(TLS cookie without secure flag set)."""
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
        "Excerpt of our CASA ZAP config and DAST summary. Not a ZAP product screenshot.",
        font=F_FOOT,
        fill=MUTED,
    )
    im.save(OUT / "CASA_2_3_1_zap.png", "PNG")
    print("wrote", OUT / "CASA_2_3_1_zap.png")


F_H = font(22, True)
F_SUB = font(14)
F_SEC = font(16, True)
F_BODY = font(15)
F_SMALL = font(13)
F_FOOT = font(12)
F_MONO = mono(13)

if __name__ == "__main__":
    page1()
    page2()
    code_page()
    zap_page()
