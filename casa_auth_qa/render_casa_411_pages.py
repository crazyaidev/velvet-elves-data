"""Render CASA 4.1.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.1")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1400, 1800
MARGIN = 56
BG = (248, 248, 246)
INK = (24, 24, 24)
MUTED = (80, 80, 80)
RULE = (200, 80, 70)
OK = (20, 90, 50)
WARN = (140, 70, 20)
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
    d.text((W - MARGIN - 220, H - 42), "CASA_4_1_1_tls", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("4.1.1 TLS 1.2+ on the production SPA and API", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0. AL1 named evidence is a Qualys SSL Labs PDF with grade B or higher (NIST SP.800-52r2). This page records a live TLS handshake against Velvet Elves production hosts.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Where TLS terminates", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "The SPA is CloudFront at app.velvetelves.com (MinimumProtocolVersion TLSv1.2_2021). The API is an ALB in front of ECS at api.prod.velvetelves.com (documented ssl-policy ELBSecurityPolicy-TLS13-1-2-2021-06). Browsers talk HTTPS to both. Certificates are public Amazon-issued ACM certs.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Live handshake (31 Aug 2026)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Default negotiation on both hosts was TLS 1.3, cipher TLS_AES_128_GCM_SHA256. A forced TLS 1.2 handshake succeeded (ECDHE-RSA-AES128-GCM-SHA256). TLS 1.0 and 1.1 from this client were rejected. HTTPS GET returned 200 with Strict-Transport-Security: max-age=31536000; includeSubDomains on the SPA (CloudFront SecurityHeadersPolicy) and the API (FastAPI SecurityHeadersMiddleware).",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. HTTP (port 80)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "GET http://app.velvetelves.com/ returned 301 Location https://app.velvetelves.com/. GET http://api.prod.velvetelves.com/api/v1/health returned 200 JSON from FastAPI. The API ALB HTTP listener currently forwards to the app instead of redirecting to HTTPS. That is not claimed as HTTPS-only. The JSON body is the public health payload; it is still cleartext on port 80.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "4. HSTS", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "After a browser has seen the HTTPS HSTS header, subsequent visits to these hostnames use HTTPS. HSTS on an HTTP response is not processed. The SPA already redirects HTTP to HTTPS, so the first visit upgrades. The API does not yet redirect.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_4_1_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_4_1_1_page1.png")


def page2():
    im, d, y = new_page("4.1.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "TLS 1.2+",
            "Production 443 negotiated TLS 1.3 by default and accepted TLS 1.2. TLS 1.0/1.1 were rejected by this client.",
            True,
        ),
        (
            "HSTS",
            "SPA and API HTTPS responses send max-age=31536000; includeSubDomains.",
            True,
        ),
        (
            "SPA HTTP",
            "CloudFront 301 from http://app.velvetelves.com/ to HTTPS.",
            True,
        ),
        (
            "API HTTP listener",
            "Port 80 still reaches FastAPI (GET /api/v1/health returned 200 JSON). Not claimed as HTTPS-only.",
            False,
        ),
        (
            "Trusted certs on 443",
            "Peer certificate issuer organization is Amazon (public ACM). Same hosts as 4.1.2.",
            True,
        ),
    ]
    for title, detail, ok in rows:
        color = OK if ok else WARN
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
                "Velvet Elves production 443 defaults to TLS 1.3, accepts TLS 1.2, and sends HSTS. The SPA upgrades HTTP to HTTPS. The API HTTP listener still forwards to FastAPI on port 80. A Qualys SSL Labs PDF of both hostnames is the ADA-named AL1 evidence for the full protocol and cipher matrix.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_4_1_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_4_1_1_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "4.1.1 API HSTS middleware and SPA CloudFront policy", font=F_H, fill=INK)
    snippet = """# app/core/security_headers.py
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    ...
}

# SPA CloudFront (app.velvetelves.com)
# Managed SecurityHeadersPolicy HSTS max-age=31536000
# MinimumProtocolVersion = TLSv1.2_2021

# API ALB (api.prod.velvetelves.com)
# Documented ssl-policy ELBSecurityPolicy-TLS13-1-2-2021-06"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_4_1_1_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_4_1_1_code.png", "PNG")
    print("wrote", OUT / "CASA_4_1_1_code.png")


def tests_page():
    im = Image.new("RGB", (1400, 780), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "4.1.1 Tests for API security headers including HSTS", font=F_H, fill=INK)
    snippet = """test_health_response_includes_security_headers
  GET /api/v1/health includes
  Strict-Transport-Security: max-age=31536000; includeSubDomains

test_security_headers_on_not_found
  GET /api/v1/does-not-exist still sends nosniff and X-Frame-Options

Live 31 Aug 2026 (production, not these unit tests):
  TLS 1.3 default, TLS 1.2 accepted, TLS 1.0/1.1 rejected
  SPA HTTP 301 to HTTPS
  API HTTP /api/v1/health 200 (ALB does not redirect yet)"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_4_1_1_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_4_1_1_tests.png", "PNG")
    print("wrote", OUT / "CASA_4_1_1_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    tests_page()
