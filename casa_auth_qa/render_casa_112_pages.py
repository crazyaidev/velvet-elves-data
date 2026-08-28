"""Render CASA 1.1.2 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\1.1.2")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1400, 1800
MARGIN = 56
BG = (248, 248, 246)
INK = (24, 24, 24)
MUTED = (80, 80, 80)
RULE = (200, 80, 70)
OK = (20, 90, 50)
WARN = (140, 80, 20)
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
        "GCP 538509143953  |  production app.velvetelves.com  |  27 Aug 2026",
        font=F_SMALL,
        fill=MUTED,
    )
    d.line((MARGIN, 124, W - MARGIN, 124), fill=LINE, width=1)
    d.text((MARGIN, H - 42), f"Page {page_no} of 2", font=F_FOOT, fill=MUTED)
    d.text((W - MARGIN - 240, H - 42), "CASA_1_1_2_activation", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("1.1.2 Initial passwords / activation codes expire", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 2.3.1.",
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
                "Supabase Auth (GoTrue): register, invite accept, password reset, email confirmation. Not claimed as an ADA-approved identity provider.",
                F_BODY,
                INK,
            ),
            (
                "Google OAuth (authorization code + PKCE): Gmail and Calendar integrations only. Out of scope for 1.1.2.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. We do not issue initial passwords", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "A user always chooses the long-term password. Self-register sets it on POST /users/register. Invite accept sets it on POST /invitations/accept/{token}. Password reset sets a new password from a one-time recovery link. The invite or reset token is never stored as the password.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Invite activation token (our wrapper)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Generated with uuid.uuid4().hex: 32 hex characters (0-9 and a-f), 128 bits of randomness. InvitationRepository.create.",
                F_BODY,
                INK,
            ),
            (
                "Single use: is_used is set on accept. Reuse, revoke, or unknown token returns 404 or 410. The SPA shows Invalid Invitation.",
                F_BODY,
                INK,
            ),
            (
                "Default lifetime is 72 hours (_DEFAULT_EXPIRY_HOURS). Email copy says the link expires in 72 hours. An admin extend adds another 72 hours to the same token.",
                F_BODY,
                WARN,
            ),
            (
                "ADA 1.1.2 verification 2.3 recommends 24 hours and caps at 48 hours. We do not claim the 48-hour cap. Compensating: the token is not a password, is single-use, and is 32 hex characters.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "4. Password reset", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/password-reset/request calls supabase.auth.reset_password_email. Confirm consumes the recovery token once. The new password must differ from the old one. Opening /reset-password without a token shows Invalid or expired link and cannot set a password.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_1_2_page1.png", "PNG")
    print("wrote", OUT / "CASA_1_1_2_page1.png")


def page2():
    im, d, y = new_page("1.1.2 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification (2.1-2.4 if not an ADA-approved IdP)", font=F_SEC, fill=INK)
    y += 32
    rows = [
        ("ADA-approved IdP", "Not claimed for Supabase.", False, False),
        (
            "2.1  Codes at least 6 characters",
            "PASS. Invite token is 32 hex characters.",
            True,
            False,
        ),
        (
            "2.2  Letters and numbers",
            "PASS. Hex alphabet (0-9, a-f).",
            True,
            False,
        ),
        (
            "2.3  Expire within 48 hours (24h recommended)",
            "NOT CLAIMED. Invite TTL is 72 hours; extend adds 72. Reset uses vendor recovery (do not invent the OTP hours).",
            False,
            True,
        ),
        (
            "2.4  Must not become the long-term password",
            "PASS. User always sets their own password. Token is discarded after use.",
            True,
            False,
        ),
    ]
    for title, detail, ok, warn in rows:
        color = WARN if warn else (OK if ok else INK)
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
                "Velvet Elves does not generate initial passwords. Activation is an invite token that is random, 32 hex characters, single-use, and cannot be used as the password. Password reset is a one-time Supabase recovery link. We are honest that invite expiry is 72 hours, above ADA's 48-hour maximum for this control.",
                F_BODY,
                INK,
            ),
            (
                "If TAC requires the 48-hour cap, change _DEFAULT_EXPIRY_HOURS (and the extend window) in InvitationRepository, update branded invite email copy, deploy, and re-upload this row.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    im.save(OUT / "CASA_1_1_2_page2.png", "PNG")
    print("wrote", OUT / "CASA_1_1_2_page2.png")


if __name__ == "__main__":
    page1()
    page2()
