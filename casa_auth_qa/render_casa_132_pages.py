"""Render CASA 1.3.2 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\1.3.2")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1400, 1800
MARGIN = 56
BG = (248, 248, 246)
INK = (24, 24, 24)
MUTED = (80, 80, 80)
RULE = (200, 80, 70)
OK = (20, 90, 50)
LINE = (220, 218, 214)


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


F_H = font(22, True)
F_SUB = font(14)
F_SEC = font(16, True)
F_BODY = font(15)
F_SMALL = font(13)
F_FOOT = font(12)


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
    d.text((W - MARGIN - 250, H - 42), "CASA_1_3_2_oob_single_use", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("1.3.2 Out of band verifier is single-use", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 2.7.3.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. External user authentication services", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Supabase Auth (GoTrue) issues password-reset recovery emails, signup confirmation, and TOTP MFA factors. It is not claimed as an ADA-approved identity provider. Google OAuth is not an email or SMS login verifier. Velvet Elves does not send SMS one-time codes.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Password reset recovery token", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/password-reset/request calls supabase.auth.reset_password_email. Confirm is POST /users/password-reset/confirm with the recovery token from the email. Velvet Elves does not store a reusable reset code in application tables.",
                F_BODY,
                INK,
            ),
            (
                "A missing, invalid, or already-consumed token returns HTTP 400: Invalid or expired reset token. Please request a new one. The SPA /reset-password page without a token shows Invalid or expired link and Request a new link. It cannot set a password.",
                F_BODY,
                INK,
            ),
            (
                "Staging check: the same non-recovery token posted twice to confirm both return 400. Neither attempt sets a password.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. TOTP MFA", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "GoTrue opens a challenge and verifies the current authenticator code. Codes rotate every 30 seconds (otpauth totp). Invite-token single-use is documented under 1.1.2.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_3_2_page1.png", "PNG")
    print("wrote", OUT / "CASA_1_3_2_page1.png")


def page2():
    im, d, y = new_page("1.3.2 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        ("ADA-approved IdP", "Not claimed for Supabase.", False),
        (
            "OOB verifier used only once",
            "GoTrue recovery token. Confirm without a valid token returns 400. SPA cannot set a password without a fresh link.",
            True,
        ),
        (
            "SMS OTP",
            "Not used.",
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
                "Out-of-band password-reset verifiers for Velvet Elves are issued by Supabase Auth and cannot be reused to set a password. A used, missing, or invalid recovery token is rejected. The user must request a new link.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_3_2_page2.png", "PNG")
    print("wrote", OUT / "CASA_1_3_2_page2.png")


if __name__ == "__main__":
    page1()
    page2()
