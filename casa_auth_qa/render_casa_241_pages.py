"""Render CASA 2.4.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.4.1")
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
F_MONO = mono(13)


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
    d.text((W - MARGIN - 280, H - 42), "CASA_2_4_1_sensitive_changes", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("2.4.1 Session or verification before account changes", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 3.7.1. AL1 is code or documentation that a full login session or an account verification process runs before account modifications or sensitive data transactions. Verification is the same or.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Profile and email need a valid session", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "PATCH /users/me is the self-service profile and sign-in email path. It depends on get_current_user, which verifies the signed JWT and loads an active user. Missing or invalid Authorization returns 401. The Settings Profile screen is behind ProtectedRoute. Email change is allowed in this session; it is not restricted and does not wait for a new-inbox confirm.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Password change is email recovery", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "There is no in-session current-password form. Forgot password sends a Supabase recovery email. Confirm posts the recovery token from that mail. That is secondary verification, not a leftover JWT.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Turning MFA off needs a current TOTP", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/mfa/disable verifies a fresh authenticator code. A leftover aal2 session cannot strip MFA. Platform admin APIs also require aal2 plus a live TOTP factor (see 3.3.1).",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_4_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_2_4_1_page1.png")


def page2():
    im, d, y = new_page("2.4.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Full login session for account edits",
            "PATCH /users/me uses get_current_user. Staging: no Authorization and Bearer not-a-jwt both return 401. A valid JWT returns 200 on GET /users/me.",
            True,
        ),
        (
            "Password change uses account verification",
            "Recovery email plus confirm token. Not an in-app current-password field.",
            True,
        ),
        (
            "MFA disable uses secondary verification",
            "Current TOTP required. Leftover aal2 is not enough.",
            True,
        ),
        (
            "Not claimed",
            "No password re-prompt on every profile save. Email change is not restricted.",
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
                "Velvet Elves requires a valid login session for profile and email changes, email recovery for password change, and a current authenticator code to turn MFA off. ADA 2.4.1 is met via a full login session and, where the change is more sensitive, a second verification step.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_4_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_2_4_1_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1100), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.4.1 Session gate and extra checks", font=F_H, fill=INK)
    snippet = """# app/core/auth.py
async def get_current_user(token = Depends(oauth2_scheme), ...):
    payload = decode_access_token(token)   # 401 if invalid / expired
    user = await repo.get_by_id(payload["sub"])
    if not user.is_active: raise 403

# app/api/v1/users.py
@router.patch("/me")
async def update_me(..., current_user = Depends(get_current_user)):
    # profile + sign-in email; valid session required

@router.post("/password-reset/request")   # unauthenticated
# recovery email; confirm uses the token from that mail

@router.post("/mfa/disable")
async def mfa_disable(..., current_user = Depends(get_current_user)):
    # fresh TOTP; leftover aal2 cannot strip MFA"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_2_4_1_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_2_4_1_code.png", "PNG")
    print("wrote", OUT / "CASA_2_4_1_code.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
