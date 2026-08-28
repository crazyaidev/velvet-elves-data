"""Render CASA 1.3.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\1.3.1")
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
    d.text((W - MARGIN - 220, H - 42), "CASA_1_3_1_oob_expiry", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("1.3.1 Out of band verifier expiry", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 2.7.2.",
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
                "Supabase Auth (GoTrue) issues password-reset recovery emails, signup email confirmation, and TOTP MFA factors. It is not claimed as an ADA-approved identity provider.",
                F_BODY,
                INK,
            ),
            (
                "Google OAuth (authorization code + PKCE) is used for Gmail and Calendar. It is not an email or SMS verifier for Velvet Elves login. Velvet Elves does not send SMS one-time codes.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Password reset (email recovery link)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/password-reset/request calls supabase.auth.reset_password_email. The API always returns 202 so the response does not reveal whether the email is registered. Confirm uses the recovery token from the email (POST /users/password-reset/confirm).",
                F_BODY,
                INK,
            ),
            (
                "Velvet Elves does not generate a proprietary reset code and does not pass a custom TTL in application code. GoTrue expires the recovery link. Auth Email OTP expiration is 3600 seconds (1 hour). The forgot-password success screen tells the user: Link expires in 1 hour. ADA allows password-reset verifiers up to 7 days; one hour is within that bound.",
                F_BODY,
                INK,
            ),
            (
                "Opening /reset-password without a recovery token shows Invalid or expired link and cannot set a password. The user must request a new link.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. MFA-related verifiers (TOTP)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Platform-admin MFA uses TOTP via GoTrue (otpauth://totp/). Authenticator codes use the standard 30-second time step (RFC 6238 default). ADA allows MFA verifiers up to 30 minutes. A 30-second TOTP window is within that bound.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_3_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_1_3_1_page1.png")


def page2():
    im, d, y = new_page("1.3.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        ("ADA-approved IdP", "Not claimed for Supabase.", False),
        (
            "Password reset verifiers expire within 7 days",
            "GoTrue recovery email. Email OTP expiration 3600 seconds (1 hour). Missing or expired link cannot set a password.",
            True,
        ),
        (
            "MFA verifiers expire within 30 minutes",
            "TOTP 30-second time step (otpauth totp / RFC 6238). Under the 30-minute cap.",
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
                "Out-of-band verifiers for Velvet Elves login are issued by Supabase Auth. Password-reset links are presented as expiring in one hour and cannot be used after they are missing or expired. TOTP codes rotate every 30 seconds. Invite-token lifetime is documented under 1.1.2, not this check.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_3_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_1_3_1_page2.png")


if __name__ == "__main__":
    page1()
    page2()
