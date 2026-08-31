"""Render CASA 3.1.6 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.6")
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
    d.text((W - MARGIN - 240, H - 42), "CASA_3_1_6_directory", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("3.1.6 Directory browsing is disabled", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 4.3.2. AL1 evidence is ADA DAST. Verification: the scan must not identify Directory Listing (Burp 6291712; ZAP plugin 0 on the SPA conf).",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. SPA is hashed CloudFront objects", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "The app is a Vite SPA on CloudFront with an S3 origin via Origin Access Control. There is no Apache or nginx autoindex. Production bucket velvet-elves-prod-frontend-388482955098 has Block all public access On (all four settings). Staging GET /assets/, /static/, and a missing hashed JS file return the SPA HTML shell, not Index of / and not an S3 ListBucketResult.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. The API has no static directory index", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "FastAPI on ECS does not mount StaticFiles. Staging GET /, /api/v1/, and /static/ return JSON 404. Staging still serves /api/docs (OpenAPI UI); that is a documented page, not a filesystem listing. Production /api/docs is 404.",
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
                "Official ADA ZAP scans SPA 10f54abf, API a9d78f05, and authenticated API 33afa2aa did not list Directory Browsing. We did not run Burp. We did not recapture ZAP UI.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_6_page1.png", "PNG")
    print("wrote", OUT / "CASA_3_1_6_page1.png")


def page2():
    im, d, y = new_page("3.1.6 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "No directory listing on the SPA",
            "Prefix GETs return the HTML shell, not Index of / or ListBucketResult. S3 Block all public access is On.",
            True,
        ),
        (
            "No directory listing on the API",
            "GET /, /api/v1/, /static/ return JSON 404. No StaticFiles mount.",
            True,
        ),
        (
            "DAST",
            "ZAP SPA/API/auth scans did not report plugin 0. Burp 6291712 was not run.",
            True,
        ),
        (
            "Staging",
            "Measured 31 Aug 2026 on app.stage and api.stage.velvetelves.com.",
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
                "Velvet Elves does not expose directory browsing. The production frontend S3 bucket blocks all public access. The SPA is hashed CloudFront objects. The API returns JSON 404 for directory-like paths. Official ADA ZAP did not report Directory Browsing.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_6_page2.png", "PNG")
    print("wrote", OUT / "CASA_3_1_6_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.6 CloudFront SPA rewrite; API has no static mount", font=F_H, fill=INK)
    snippet = """# CloudFront Function (viewer-request)  spa-rewrite.js
# extensionless routes -> /index.html
# /assets/* is left to the S3 origin (hashed Vite files)
if (uri === '/assets' || uri.indexOf('/assets/') === 0) {
    return request;
}
if (!hasExtension) {
    request.uri = '/index.html';
}

# app/main.py  create_app()
# include_router(api_router) only — no StaticFiles, no autoindex
# unknown API paths: JSON 404  {"message": "Not Found"}"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_6_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_6_code.png", "PNG")
    print("wrote", OUT / "CASA_3_1_6_code.png")


def zap_page():
    im = Image.new("RGB", (1400, 920), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.6 Official ADA ZAP directory-browsing rule", font=F_H, fill=INK)
    snippet = """# zap-casa-config.conf  (SPA — FAIL)
0    FAIL    (Directory Browsing)

# Official scans (21 Aug 2026) — DAST_SUMMARY.md
SPA  10f54abf   https://app.stage.velvetelves.com
API  a9d78f05   https://api.stage.velvetelves.com
Auth 33afa2aa   authenticated API

Alert lists did not include Directory Browsing.

ADA AL1: scan shall not identify Burp 6291712
(Directory Listing). Burp was not run."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_6_zap", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_6_zap.png", "PNG")
    print("wrote", OUT / "CASA_3_1_6_zap.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    zap_page()
