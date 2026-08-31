"""Render CASA 2.3.3 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.3.3")
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
    d.text((W - MARGIN - 300, H - 42), "CASA_2_3_3_session_not_static", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("2.3.3 Session tokens after authentication", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 3.5.2. AL1 is code or documentation of dynamically generated session tokens. Verification: tokens are generated after user authentication.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Login mints a new GoTrue JWT", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/login calls sign_in_with_password. GoTrue returns a new session.access_token and session.refresh_token for that sign-in. TokenResponse sends them to the client. The SPA uses Authorization Bearer. A later login issues a different JWT (iat changes). The user session is not a shared static API key.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Google mailbox tokens are per user", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Gmail and Calendar store that user's OAuth access and refresh tokens in integrations, Fernet-encrypted. They are not a shared mailbox API key and they are not the Velvet Elves login session.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Inbound CRM keys are not the user session", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Admins may create tenant inbound keys (vek_ prefix, secrets.token_urlsafe) so an external system can POST contacts with X-API-Key. Those keys are hashed at rest. Creating them requires an admin JWT. They do not sign a person into the app. Backend service secrets (OpenAI, Stripe, SendGrid, Supabase service role) stay on the server.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_3_3_page1.png", "PNG")
    print("wrote", OUT / "CASA_2_3_3_page1.png")


def page2():
    im, d, y = new_page("2.3.3 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Session token after authentication",
            "GoTrue issues access_token and refresh_token only after a successful sign_in_with_password (or MFA verify / OAuth exchange).",
            True,
        ),
        (
            "Dynamically generated",
            "Staging: two successive logins produced different JWT iat values. Tokens not shown.",
            True,
        ),
        (
            "Not a static user API key",
            "The SPA session is that JWT, not a hardcoded key in the client.",
            True,
        ),
        (
            "Machine inbound keys",
            "X-API-Key contact push is a separate path. It is not the human login session.",
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
                "Velvet Elves user sessions are dynamically generated JWTs issued after authentication. The product does not log users in with a static shared API key.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_3_3_page2.png", "PNG")
    print("wrote", OUT / "CASA_2_3_3_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 980), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.3.3 Login returns a new GoTrue session JWT", font=F_H, fill=INK)
    snippet = """# app/services/auth_service.py
auth_resp = await auth_client.auth.sign_in_with_password({
    "email": email, "password": password,
})
return TokenResponse(
    access_token=auth_resp.session.access_token,   # minted now
    refresh_token=auth_resp.session.refresh_token,
    user=UserResponse.model_validate(profile),
)

# app/api/v1/crm_sync.py  (machine inbound — not the user session)
raw = f"vek_{secrets.token_urlsafe(32)}"
# stored as SHA-256; caller sends X-API-Key. Admin JWT required to create."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_2_3_3_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_2_3_3_code.png", "PNG")
    print("wrote", OUT / "CASA_2_3_3_code.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
