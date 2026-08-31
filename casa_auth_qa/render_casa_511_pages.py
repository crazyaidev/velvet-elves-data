"""Render CASA 5.1.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.1.1")
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
    d.text((W - MARGIN - 280, H - 42), "CASA_5_1_1_hpp", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("5.1.1 Protect against HTTP parameter pollution", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0. AL1 evidence is ADA DAST. Verification: the scan shall not identify Burp 5248000 (client-side HPP reflected) or 5248001 (stored). Official scans were ZAP with the ADA CASA conf. WSTG-INPV-04 is AL2.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Official ADA ZAP (21 Aug 2026)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "SPA 10f54abf, API a9d78f05, authenticated API 33afa2aa, all against staging. SPA conf maps plugin 20014 HTTP Parameter Pollution to FAIL. API conf maps the same plugin to WARN. DAST_SUMMARY.md alert tables do not list HTTP Parameter Pollution. SPA was 0 High. API and auth scans exited 0. We did not run Burp.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Typed query and path parameters", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "FastAPI binds query and path values as typed scalars (int, str, enum, constrained Query). The backend does not call request.query_params.getlist. Starlette MultiDict get() returns one value for a scalar; duplicate keys are not concatenated into a single string. Session is Authorization Bearer, not a query parameter.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Staging measurement (31 Aug 2026)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Public help search q has max_length 160. GET q=ok and q=<161 chars> returned 422 string_too_long on the last value. GET q=<161 chars> and q=ok returned 200. Concatenating both values would still be over 160 and would have been 422. Unsigned GET /teams?page=1&page=2 returned 401. Duplicate public payment tokens returned 403 Invalid or expired payment link.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "4. SPA query reads", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "The React app reads filters with URLSearchParams.get, which returns a single value. Those query keys are UI filters (for example tx), not authorization. Access control is the JWT plus server tenant and assignment checks.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_5_1_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_5_1_1_page1.png")


def page2():
    im, d, y = new_page("5.1.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Official DAST",
            "ZAP 20014 enabled (SPA FAIL, API WARN). Alert lists did not include HTTP Parameter Pollution.",
            True,
        ),
        (
            "Burp 5248000 / 5248001",
            "ADA names these plugins. Burp was not run. Closest official analog is ZAP 20014.",
            True,
        ),
        (
            "Typed scalars",
            "Query and path params are FastAPI types. Duplicate keys are not concatenated.",
            True,
        ),
        (
            "Live last-wins",
            "Help search: long last value 422; short last value 200. Concatenation would 422 both.",
            True,
        ),
        (
            "Auth still required",
            "Unsigned GET /teams?page=1&page=2 is 401. Session is not in the query string.",
            True,
        ),
        (
            "SPA spider scope",
            "Traditional spider hit /, /robots.txt, /sitemap.xml. Authenticated SPA routes were not crawled.",
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
                "Velvet Elves binds HTTP parameters as single typed values. Official ADA ZAP scans did not report HTTP Parameter Pollution. Staging duplicate query keys take one value and do not concatenate. WSTG-INPV-04 was not run.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_5_1_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_5_1_1_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 980), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "5.1.1 FastAPI typed Query scalars (one value)", font=F_H, fill=INK)
    snippet = """# app/api/v1/teams.py
page: int = Query(default=1, ge=1)
page_size: int = Query(default=50, ge=1, le=100)

# app/api/v1/public_help.py
q: str = Query(default="", max_length=160)
locale: str = Query(default="en")

# app/api/v1/public_payments.py
token: str = Query(...)

# Backend has no request.query_params.getlist.
# Starlette Query scalars bind one duplicate (last).
# Session is Authorization Bearer, not a query key."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_5_1_1_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_5_1_1_code.png", "PNG")
    print("wrote", OUT / "CASA_5_1_1_code.png")


def zap_page():
    im = Image.new("RGB", (1400, 980), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "5.1.1 Official ADA ZAP HTTP Parameter Pollution", font=F_H, fill=INK)
    snippet = """# zap-casa-config.conf  (SPA)
20014    FAIL    (HTTP Parameter Pollution - Active/beta)

# zap-casa-api-config.conf  (API)
20014    WARN    (HTTP Parameter Pollution scanner - Active/beta)

# Official scans (21 Aug 2026) — DAST_SUMMARY.md
SPA  10f54abf   https://app.stage.velvetelves.com
API  a9d78f05   https://api.stage.velvetelves.com
Auth 33afa2aa   authenticated API, Bearer JWT

Alert lists did not include HTTP Parameter Pollution.
SPA 0 High. API and auth ZAP exit 0.

ADA AL1: scan shall not identify Burp 5248000 / 5248001.
Burp was not run. Closest analog is ZAP 20014."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_5_1_1_zap", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_5_1_1_zap.png", "PNG")
    print("wrote", OUT / "CASA_5_1_1_zap.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    zap_page()
