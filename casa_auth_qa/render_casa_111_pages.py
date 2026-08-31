"""Render CASA 1.1.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\1.1.1")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1400, 1800
MARGIN = 56
BG = (248, 248, 246)
INK = (24, 24, 24)
MUTED = (80, 80, 80)
RULE = (200, 80, 70)
OK = (20, 90, 50)
NO = (140, 40, 30)
LINE = (220, 218, 214)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
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


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
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


def new_page(title: str, page_no: int) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=RULE)
    y = 36
    d.text((MARGIN, y), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    y = 64
    d.text((MARGIN, y), title, font=F_H, fill=INK)
    y = 98
    d.text(
        (MARGIN, y),
        "GCP 538509143953  |  production app.velvetelves.com  |  27 Aug 2026",
        font=F_SMALL,
        fill=MUTED,
    )
    y = 124
    d.line((MARGIN, y, W - MARGIN, y), fill=LINE, width=1)
    d.text((MARGIN, H - 42), f"Page {page_no} of 2", font=F_FOOT, fill=MUTED)
    d.text(
        (W - MARGIN - 220, H - 42),
        "CASA_1_1_1_brute_force",
        font=F_FOOT,
        fill=MUTED,
    )
    return im, d, 144


def paint_lines(d: ImageDraw.ImageDraw, y: int, lines: list[tuple[str, object, tuple]]) -> int:
    max_w = W - 2 * MARGIN
    for text, fnt, color in lines:
        for part in wrap(d, text, fnt, max_w):
            d.text((MARGIN, y), part, font=fnt, fill=color)
            y += 22 if fnt is F_SMALL else 24
        y += 4
    return y


def page1() -> None:
    im, d, y = new_page("1.1.1 Authentication is resistant to brute force attacks", 1)
    y = paint_lines(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 2.2.1.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. External user authentication services", font=F_SEC, fill=INK)
    y += 32
    y = paint_lines(
        d,
        y,
        [
            (
                "Supabase Auth (GoTrue): email/password login, register, invite accept, password reset, JWT issue/refresh, TOTP factors. Not claimed as an ADA-approved identity provider. Treated as a non-ADA-approved external auth service.",
                F_BODY,
                INK,
            ),
            (
                "Google OAuth (authorization code + PKCE): Gmail and Calendar integrations only. Not the Velvet Elves login IdP. Out of scope for 1.1.1 password brute force (covered under 3.2.x).",
                F_BODY,
                INK,
            ),
            (
                "We do not operate a custom password hasher. POST /api/v1/users/login calls supabase.auth.sign_in_with_password. Passwords are not stored in our tables (see 1.1.3).",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Password policy", font=F_SEC, fill=INK)
    y += 32
    y = paint_lines(
        d,
        y,
        [
            (
                "Register, invite accept, and password change require minimum 8 characters (Field min_length=8) and at least one digit.",
                F_BODY,
                INK,
            ),
            (
                "API rejects passwords on a static common-password denylist (~200 entries in app/core/weak_passwords.py), shared by register, invite accept, and password reset. This is an in-repo list, not a live Have I Been Pwned lookup.",
                F_BODY,
                INK,
            ),
            (
                "SPA register and invite UI additionally require uppercase, lowercase, digit, and symbol (PasswordStrengthIndicator).",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Anti-automation (summary)", font=F_SEC, fill=INK)
    y += 32
    for label, ok in (
        ("Login IP limiter: 10 requests / 60 s on POST /users/login", True),
        ("Per-account soft lockout: 20 failed attempts / rolling hour", True),
        ("Register limiter: 5 requests / 60 s on POST /users/register", True),
        ("CAPTCHA", False),
        ("MFA default for all users (platform admins are MFA-gated; see 3.3.1)", False),
        ("Unfamiliar-device / location OTP", False),
    ):
        color = OK if ok else MUTED
        mark = "YES  " if ok else "no   "
        y = paint_lines(d, y, [(mark + label, F_BODY, color)])
    y += 8
    y = paint_lines(
        d,
        y,
        [
            (
                "Limiter and throttle are in-process. Production runs 2 tasks, so worst-case lockout ceiling is 40 failures/hour/account, still under ADA 100/hour. Supabase Auth vendor rate limits apply on top (dashboard screenshot, no keys).",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    im.save(OUT / "CASA_1_1_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_1_1_1_page1.png")


def page2() -> None:
    im, d, y = new_page("1.1.1 Anti-automation and AL1 verification mapping", 2)
    d.text((MARGIN, y), "4. AL1 verification (need one of 2.1-2.5, or an ADA-approved IdP)", font=F_SEC, fill=INK)
    y += 32
    rows = [
        ("ADA-approved IdP", "Not claimed for Supabase.", False),
        ("2.1  <=100 failed logins per account per hour", "PASS. 20 failures/hour/account (worst case 40 with 2 tasks). Plus 10/min/IP.", True),
        ("2.2  CAPTCHA or other anti-automation UI", "Not implemented. Not required because 2.1 and 2.4 pass.", False),
        ("2.3  MFA enforced by default for all users", "No. TOTP is enforced for platform administrators (3.3.1).", False),
        ("2.4  Min 8 + no weak/commonly breached passwords", "PASS. Min 8 + digit + static denylist. Not a live HIBP API.", True),
        ("2.5  Unfamiliar device or location step-up", "Not implemented.", False),
    ]
    for title, detail, ok in rows:
        d.text((MARGIN, y), title, font=F_BODY, fill=OK if ok else INK)
        y += 24
        y = paint_lines(d, y, [(detail, F_SMALL, MUTED)])
        y += 6
    y += 8
    d.text((MARGIN, y), "Attestation", font=F_SEC, fill=INK)
    y += 32
    y = paint_lines(
        d,
        y,
        [
            (
                "Velvet Elves meets 2.1 (per-account failure ceiling on the login route, plus vendor limits) and 2.4 (min length 8, digit, common-password denylist). Register is separately rate-limited at 5 per minute. TOTP MFA is enforced for platform administrators. Login brute-force protection is implemented in our API, not only at the vendor.",
                F_BODY,
                INK,
            ),
            (
                "Tests: test_login_is_rate_limited_per_ip, test_login_account_lockout_survives_ip_rotation, test_login_success_clears_failure_history, test_register_rejects_common_breached_password, test_registration_is_rate_limited.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 12
    d.text((MARGIN, y), "What this packet does not claim", font=F_SEC, fill=INK)
    y += 32
    y = paint_lines(
        d,
        y,
        [
            (
                "No CAPTCHA. No MFA default for ordinary tenant users. No live breached-password network API. No HttpOnly session cookies (session is SPA localStorage JWT; see 2.3.1 / 2.3.2). No Zero Data Retention.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_1_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_1_1_1_page2.png")


if __name__ == "__main__":
    page1()
    page2()
