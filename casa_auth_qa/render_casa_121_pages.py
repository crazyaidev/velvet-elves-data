"""Render CASA 1.2.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\1.2.1")
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
        "GCP 538509143953  |  production app.velvetelves.com  |  28 Aug 2026",
        font=F_SMALL,
        fill=MUTED,
    )
    d.line((MARGIN, 124, W - MARGIN, 124), fill=LINE, width=1)
    d.text((MARGIN, H - 42), f"Page {page_no} of 2", font=F_FOOT, fill=MUTED)
    d.text((W - MARGIN - 280, H - 42), "CASA_1_2_1_default_credentials", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("1.2.1 Default credentials shall not be present", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 2.5.4.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. ADA definition", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Default credentials are a predefined username and password pair (example: Admin/Admin). An administrator account with a user-chosen password is not a default credential. AL1: if default accounts exist on public interfaces, confirm default credentials are not used.",
                F_BODY,
                INK,
            ),
            (
                "Velvet Elves has no default accounts on publicly exposed interfaces. Public surfaces: app.velvetelves.com, app.stage.velvetelves.com, and the matching APIs. Vendor, client, and FSBO portals use the same SPA login. Help center and marketing have no login form.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. How accounts are created", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "No bootstrap script, SQL seed, README, or .env.example ships a username/password pair for the app. AuthService delegates credentials to Supabase Auth. public.users is a profile row with no password column.",
                F_BODY,
                INK,
            ),
            (
                "Self-register: POST /users/register calls supabase.auth.sign_up with the password the user typed. Self-signup roles: Agent, TeamLead, TransactionCoordinator, Admin. DEFAULT_ACCOUNT_ROLE on the register form is Agent — a role picker default, not a password.",
                F_BODY,
                INK,
            ),
            (
                "Invite: branded invite creates an Auth user without a password. POST /invitations/accept/{token} sets the password the invitee typed. Password reset: the user chooses a new password from a one-time recovery link.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Login UI and live check", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "LoginPage has no defaultValues for email or password. Placeholders only. Google Sign-in is OAuth for that Google user, not a shared Velvet Elves password.",
                F_BODY,
                INK,
            ),
            (
                "Staging live check: classic pair admin@velvetelves.com / Admin is rejected (Invalid email or password). Those values are not pre-filled by the product.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_2_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_1_2_1_page1.png")


def page2():
    im, d, y = new_page("1.2.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        ("ADA-approved IdP", "Not claimed for Supabase.", False, False),
        (
            "Default accounts on public interfaces",
            "None. Ship path is self-register or invite. SQL seeds do not insert auth users or passwords.",
            True,
            False,
        ),
        (
            "Default username/password pairs (Admin/Admin)",
            "None shipped. Login form starts empty. Classic pair rejected on staging.",
            True,
            False,
        ),
        (
            "Admin accounts",
            "Allowed when the password is user-chosen (ADA definition). Not a default credential.",
            True,
            False,
        ),
        (
            "Google Sign-in",
            "User authenticates to their own Google account via OAuth. Not a Velvet Elves default password.",
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
                "Default credentials are not present on publicly exposed Velvet Elves interfaces. There are no pre-configured accounts with a known password. Every login password is chosen by the user at register, invite accept, or password reset.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_2_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_1_2_1_page2.png")


if __name__ == "__main__":
    page1()
    page2()
