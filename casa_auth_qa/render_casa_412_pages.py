"""Render CASA 4.1.2 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.2")
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
    d.text((W - MARGIN - 240, H - 42), "CASA_4_1_2_certs", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("4.1.2 Production TLS certificates are public ACM", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0. AL1 named evidence is a Qualys SSL Labs PDF with grade B or higher. This page records the live peer certificates on Velvet Elves production hosts.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Qualys SSL Labs (31 Aug 2026)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "app.velvetelves.com and api.prod.velvetelves.com both graded A+ on every tested endpoint. An untrusted or self-signed leaf would not receive that grade. The Qualys chain shows Amazon RSA 2048 intermediates and Amazon Root CA 1, not a private CA.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Live peer certificates (OS trust store)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "app.velvetelves.com: subject CN app.stage.velvetelves.com. SAN covers app.stage.velvetelves.com and app.velvetelves.com (one ACM certificate for both SPA hostnames). Issuer Amazon / Amazon RSA 2048 M01. Valid 30 Jun 2026 to 13 Jan 2027.",
                F_BODY,
                INK,
            ),
            (
                "api.prod.velvetelves.com: subject CN and SAN api.prod.velvetelves.com. Issuer Amazon / Amazon RSA 2048 M04. Valid 1 Jul 2026 to 14 Jan 2027.",
                F_BODY,
                INK,
            ),
            (
                "Both handshakes verified with the default OS trust store. Neither certificate is self-signed. Presenting a wrong server name (evil.example.invalid) does not complete a trusted handshake.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. No private CA on the public app", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "TLS terminates at CloudFront (SPA) and the ALB (API) on public ACM certificates. The application does not ship a self-signed leaf for these hostnames. Backend HTTPS clients do not set verify=False. This check is about the application certificates, not a Google Cloud or AWS console screenshot.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_4_1_2_page1.png", "PNG")
    print("wrote", OUT / "CASA_4_1_2_page1.png")


def page2():
    im, d, y = new_page("4.1.2 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Qualys SSL Labs",
            "A+ on app.velvetelves.com and api.prod.velvetelves.com (31 Aug 2026). Chain is Amazon RSA 2048 plus Amazon Root CA 1.",
            True,
        ),
        (
            "Trusted leaf",
            "OS trust store verified both production hostnames. Issuer organization Amazon (ACM).",
            True,
        ),
        (
            "Name match",
            "SPA SAN includes app.velvetelves.com. API SAN is api.prod.velvetelves.com.",
            True,
        ),
        (
            "Not self-signed",
            "Issuer CN is Amazon RSA 2048 M01 / M04, not the leaf hostname.",
            True,
        ),
        (
            "Currently valid",
            "SPA through 13 Jan 2027. API through 14 Jan 2027. Captured 31 Aug 2026.",
            True,
        ),
        (
            "Wrong name",
            "Handshake with SNI/name evil.example.invalid does not complete a trusted session.",
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
                "Velvet Elves production SPA and API present public Amazon ACM certificates. They are trusted by the OS store, match the hostnames, and are not self-signed. Qualys SSL Labs graded both hosts A+.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_4_1_2_page2.png", "PNG")
    print("wrote", OUT / "CASA_4_1_2_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 900), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "4.1.2 Public ACM at CloudFront and ALB; no verify=False", font=F_H, fill=INK)
    snippet = """# Live 31 Aug 2026 (Python ssl.create_default_context)
# app.velvetelves.com
#   subject CN app.stage.velvetelves.com
#   SAN app.stage.velvetelves.com, app.velvetelves.com
#   issuer Amazon / Amazon RSA 2048 M01
#   valid 30 Jun 2026 - 13 Jan 2027  OS trust store: verified

# api.prod.velvetelves.com
#   subject CN / SAN api.prod.velvetelves.com
#   issuer Amazon / Amazon RSA 2048 M04
#   valid 1 Jul 2026 - 14 Jan 2027  OS trust store: verified

# Backend: no ssl.CERT_NONE / verify=False on HTTPS clients
# Certificates are ACM on CloudFront and the ALB, not app-issued."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_4_1_2_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_4_1_2_code.png", "PNG")
    print("wrote", OUT / "CASA_4_1_2_code.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
