"""Render CASA 3.2.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.2.1")
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
    d.text((W - MARGIN - 240, H - 42), "CASA_3_2_1_oauth_pkce", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("3.2.1 OAuth is authorization code + PKCE", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0. AL1: describe which OAuth 2.0 flow is used. Verification: documentation must not indicate Implicit or Resource Owner Password Credentials.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Sign-in OAuth (Google / Microsoft)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/oauth/{provider}/start builds a PKCE verifier and S256 challenge, encrypts the verifier in state, and returns Supabase /auth/v1/authorize with code_challenge_method=s256. Exchange sends the verifier with the auth code. There is no response_type=token.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Mail, calendar, and DocuSign OAuth", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Gmail, Outlook, Google Calendar, and DocuSign authorize URLs set response_type=code and code_challenge_method=S256. Tokens stay on the API (Fernet at rest), not in the SPA. Email/password login is Supabase sign_in_with_password, not an OAuth password grant to Google.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Staging (flow not completed)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/oauth/google/start returned 200 with s256 and a code_challenge. Consent was not completed. Unsigned POST /integrations/gmail/authorize-url returned 401. Google Cloud Console was not opened.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_2_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_3_2_1_page1.png")


def page2():
    im, d, y = new_page("3.2.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Authorization code + PKCE",
            "Sign-in, Gmail, Outlook, Calendar, and DocuSign all use code + S256.",
            True,
        ),
        (
            "No implicit flow",
            "Authorize URLs use response_type=code. Sign-in start has no response_type=token.",
            True,
        ),
        (
            "No OAuth ROPC to Google",
            "Password login is Supabase email/password, not a Google password grant.",
            True,
        ),
        (
            "Staging",
            "Google start returned s256. Gmail authorize-url without a session is 401.",
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
                "Velvet Elves OAuth integrations use authorization code with PKCE. They do not use the Implicit flow or the Resource Owner Password Credentials flow.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_2_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_3_2_1_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.2.1 PKCE on sign-in and Gmail authorize URLs", font=F_H, fill=INK)
    snippet = """# app/services/oauth_service.py  Google/Microsoft sign-in
code_verifier = generate_pkce_verifier()
code_challenge = generate_pkce_challenge(code_verifier)
params = {
    "code_challenge": code_challenge,
    "code_challenge_method": "s256",
}

# app/services/email/gmail_provider.py
params = {
    "response_type": "code",
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
}
# Outlook and DocuSign use the same pattern."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_2_1_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_2_1_code.png", "PNG")
    print("wrote", OUT / "CASA_3_2_1_code.png")


def tests_page():
    im = Image.new("RGB", (1400, 820), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.2.1 Tests that PKCE state is encrypted", font=F_H, fill=INK)
    snippet = """test_oauth_state_is_stateless_and_roundtrips
  PKCE verifier is inside Fernet state, not plaintext

test_oauth_exchange_rejects_tampered_state
  POST /users/oauth/google/exchange garbage state → 400
  before any code exchange

# Gmail/Outlook/DocuSign begin() mint S256 challenges
# exchange_code sends grant_type=authorization_code + code_verifier"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_2_1_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_2_1_tests.png", "PNG")
    print("wrote", OUT / "CASA_3_2_1_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    tests_page()
