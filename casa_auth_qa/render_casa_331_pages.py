"""Render CASA 3.3.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.3.1")
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
    d.text((W - MARGIN - 240, H - 42), "CASA_3_3_1_admin_mfa", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("3.3.1 Platform admin console enforces TOTP MFA", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0. AL1: evidence that application administrative interfaces enforce MFA for administrative accounts. Cloud consoles (GCP, AWS) are out of this check.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Administrative interface", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "The platform console (/platform/* and /api/v1/platform/*) is the cross-tenant operator surface. Tenant Admin is a workspace role, not this interface. Ordinary users may enroll TOTP; they are not required to.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Enforcement", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "require_platform_admin demands is_platform_admin, JWT aal=aal2, and a currently verified TOTP factor. PLATFORM_ADMIN_MFA_REQUIRED defaults true. Login of an enrolled account returns mfa_required with an AAL1 token and no refresh token until POST /users/mfa/verify. PlatformMfaGate blocks the console until a code is entered.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Staging and production UI", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Login shows two-step verification (authenticator code). The platform console shows a code gate. Security settings show authenticator app is on. Captured on staging and production. Enrollment QR images are not attached (they contain a TOTP setup key).",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "4. Staging API", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Unsigned GET /platform/users, GET /platform/registrations, and GET /users/mfa/factors returned 401. A live aal1 session was not replayed this pack (QA_PASSWORD unset). test_platform_route_rejects_aal1_platform_admin covers 403 mfa_required.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_3_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_3_3_1_page1.png")


def page2():
    im, d, y = new_page("3.3.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Admin interface identified",
            "Platform console only. Not GCP/AWS. Not tenant Admin.",
            True,
        ),
        (
            "MFA type",
            "TOTP authenticator app (GoTrue). Code at login and to unlock the console.",
            True,
        ),
        (
            "API gate",
            "aal2 plus a live verified factor. Unenroll closes platform APIs.",
            True,
        ),
        (
            "UI",
            "Staging and production: two-step prompt and Security authenticator on.",
            True,
        ),
        (
            "Unsigned API",
            "GET /platform/users without Authorization is 401.",
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
                "Velvet Elves enforces TOTP MFA on the application administrative interface (platform console) for platform administrator accounts. MFA is not claimed as a default for all users.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_3_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_3_3_1_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1120), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.3.1 require_platform_admin demands aal2 TOTP", font=F_H, fill=INK)
    snippet = """# app/core/auth.py  require_platform_admin
if not current_user.is_platform_admin:
    raise HTTPException(403, "Platform administrator privileges are required.")
if get_settings().platform_admin_mfa_required:
    has_totp = await mfa_service.has_verified_totp_factor(token)
    if current_user.session_aal != "aal2" or not has_totp:
        raise HTTPException(403, error_code="mfa_required")

# POST /users/login  (enrolled account)
# mfa_required=true, AAL1 access token, no refresh token
# POST /users/mfa/verify  upgrades the session JWT to aal=aal2"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_3_1_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_3_1_code.png", "PNG")
    print("wrote", OUT / "CASA_3_3_1_code.png")


def tests_page():
    im = Image.new("RGB", (1400, 900), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.3.1 Tests for platform MFA gate", font=F_H, fill=INK)
    snippet = """test_platform_route_rejects_aal1_platform_admin
  GET /platform/users with aal1 JWT → 403 mfa_required

test_platform_route_allows_aal2_platform_admin
  GET /platform/users with aal2 + verified TOTP → 200

test_platform_route_rejects_stale_aal2_after_unenroll
  leftover aal2 JWT after factor removal → 403

test_login_returns_mfa_required_for_enrolled_account"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_3_1_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_3_1_tests.png", "PNG")
    print("wrote", OUT / "CASA_3_3_1_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    tests_page()
