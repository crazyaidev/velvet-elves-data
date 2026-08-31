"""Render CASA 3.1.5 write-up pages as portal-ready PNGs."""
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.5")
OUT.mkdir(parents=True, exist_ok=True)
SRC_429 = Path(
    r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\1.1.1\CASA_1_1_1_register_429.png"
)

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
F_MONO = mono(12)


def new_page(title: str, page_no: int):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), title, font=F_H, fill=INK)
    d.text(
        (MARGIN, 98),
        "GCP 538509143953  |  production app.velvetelves.com  |  31 Aug 2026",
        font=F_SMALL,
        fill=MUTED,
    )
    d.line((MARGIN, 124, W - MARGIN, 124), fill=LINE, width=1)
    d.text((MARGIN, H - 42), f"Page {page_no} of 2", font=F_FOOT, fill=MUTED)
    d.text((W - MARGIN - 200, H - 42), "CASA_3_1_5_csrf", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("3.1.5 CSRF: Bearer session, CORS, rate limits", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 4.2.2. AL1 evidence is ADA DAST. Verification: the scan must not identify Cross-site request forgery (Burp 2098944; ZAP 10202 / 20012 on the SPA conf).",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Authenticated APIs are not cookie CSRF", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "The session is Authorization Bearer from localStorage, not a cookie. Login returns JWTs in JSON and sets no Set-Cookie. A cross-site form cannot attach the Bearer header. CORS allowlists exact SPA origins; a foreign Origin does not receive Access-Control-Allow-Origin. There is no synchronizer CSRF cookie.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Unauthenticated anti-automation", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/register is JSON (CORS preflight) and limited to 5 requests per 60 seconds per IP. POST /users/login is limited to 10 per 60 seconds per IP. Staging register already returned 429 on the sixth call (1.1.1 capture reused here). No new staging user was registered this session.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Official DAST", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Official ADA ZAP scans SPA 10f54abf, API a9d78f05, and authenticated API 33afa2aa did not list Absence of Anti-CSRF Tokens. We did not run Burp. We did not recapture ZAP UI.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_5_page1.png", "PNG")
    print("wrote", OUT / "CASA_3_1_5_page1.png")


def page2():
    im, d, y = new_page("3.1.5 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Authenticated CSRF",
            "Bearer header, not a cookie. CORS origin allowlist. Foreign Origin is not echoed.",
            True,
        ),
        (
            "Unauthenticated anti-automation",
            "Register 5/min/IP. Login 10/min/IP. Staging register sixth call 429.",
            True,
        ),
        (
            "DAST",
            "ZAP SPA/API/auth scans did not report 10202 or 20012. Burp 2098944 was not run.",
            True,
        ),
        (
            "Staging CORS",
            "OPTIONS /users/me from app.stage.velvetelves.com is allowed; evil.example is not.",
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
                "Velvet Elves authenticated APIs are not cookie CSRF. The SPA origin is CORS-allowlisted. Unauthenticated register is rate-limited. Official ADA ZAP did not report missing anti-CSRF tokens.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_5_page2.png", "PNG")
    print("wrote", OUT / "CASA_3_1_5_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.5 Bearer auth, CORS origins, rate limits", font=F_H, fill=INK)
    snippet = """# app/main.py
CORSMiddleware(
    allow_origins=settings.cors_origins_list,  # exact hosts, not *
    allow_credentials=True,
)

# src/utils/api.ts
if (token) headers['Authorization'] = `Bearer ${token}`
# stored in localStorage — not a cookie, not auto-sent cross-site

# app/api/v1/users.py
_register_limiter = build_rate_limiter(max_requests=5, window_seconds=60)
_login_limiter    = build_rate_limiter(max_requests=10, window_seconds=60)"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_5_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_5_code.png", "PNG")
    print("wrote", OUT / "CASA_3_1_5_code.png")


def zap_page():
    im = Image.new("RGB", (1400, 920), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.5 Official ADA ZAP CSRF rules", font=F_H, fill=INK)
    snippet = """# zap-casa-config.conf  (SPA — FAIL)
10202    FAIL    (Absence of Anti-CSRF Tokens)
20012    FAIL    (Anti-CSRF Tokens Check)

# Official scans (21 Aug 2026) — DAST_SUMMARY.md
SPA  10f54abf   https://app.stage.velvetelves.com
API  a9d78f05   https://api.stage.velvetelves.com
Auth 33afa2aa   authenticated API, Bearer JWT (not a cookie)

Alert lists did not include 10202 or 20012.

ADA AL1: scan shall not identify Burp 2098944
(Cross-site request forgery). Burp was not run."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_5_zap", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_5_zap.png", "PNG")
    print("wrote", OUT / "CASA_3_1_5_zap.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    zap_page()
    dest = OUT / "CASA_3_1_5_register_429.png"
    shutil.copyfile(SRC_429, dest)
    im = Image.open(dest).convert("RGB")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, im.width, 36), fill=(200, 80, 70))
    d.text(
        (16, 8),
        "3.1.5  Unauthenticated anti-automation  |  same staging capture as 1.1.1  |  no new users minted",
        font=F_SMALL,
        fill=(255, 255, 255),
    )
    im.save(dest, "PNG")
    print("copied", dest)
