"""Render CASA 1.1.3 write-up and schema evidence PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\1.1.3")
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
CODE_BG = (36, 36, 36)
CODE_FG = (230, 230, 226)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    for p in (
        rf"C:\Windows\Fonts\{name}",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ):
        if Path(p).exists() and (not bold or "segoeui" in name or "arialbd" in p.lower()):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def mono(size: int):
    for p in (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return font(size)


F_H = font(22, True)
F_SUB = font(14)
F_SEC = font(16, True)
F_BODY = font(15)
F_SMALL = font(13)
F_FOOT = font(12)
F_MONO = mono(14)


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


def new_page(title: str, page_no: int, pages: int = 2):
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
    d.text((MARGIN, H - 42), f"Page {page_no} of {pages}", font=F_FOOT, fill=MUTED)
    d.text((W - MARGIN - 280, H - 42), "CASA_1_1_3_password_storage", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("1.1.3 Passwords stored resistant to offline attacks", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 2.4.1.",
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
                "Supabase Auth (GoTrue): register, login, invite accept, password reset. GoTrue owns credential storage. Not claimed as an ADA-approved identity provider.",
                F_BODY,
                INK,
            ),
            (
                "Google OAuth (authorization code + PKCE): Gmail and Calendar tokens only. Those tokens are Fernet-encrypted at rest and are not login passwords. Out of scope for 1.1.3.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Velvet Elves does not store passwords", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "AuthService delegates credentials to GoTrue. POST /users/register calls supabase.auth.sign_up. POST /users/login calls supabase.auth.sign_in_with_password. Invite accept and password reset update the password through GoTrue admin or recovery APIs. The plaintext password is never written to public.users, logs, or object storage.",
                F_BODY,
                INK,
            ),
            (
                "public.users is an application profile keyed by the Auth user UUID (JWT sub). UserRepository.create inserts id, encrypted email, role, tenant_id, and optional PII. There is no password field. See CASA_1_1_3_users_schema.png.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Where the password hash lives", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "GoTrue stores a salted bcrypt hash in auth.users.encrypted_password. The column name is a misnomer: it is a one-way hash, not reversible encryption. Each hash has a random salt. Official FAQ: supabase.com/docs/guides/auth/password-security (How are passwords stored?).",
                F_BODY,
                INK,
            ),
            (
                "bcrypt is a NIST SP 800-63B section 5.1.1.2 one-way key derivation function. We do not operate a custom hasher and we do not log passwords (row 6.5.1).",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_1_3_page1.png", "PNG")
    print("wrote", OUT / "CASA_1_1_3_page1.png")


def page2():
    im, d, y = new_page("1.1.3 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        ("ADA-approved IdP", "Not claimed for Supabase.", False),
        (
            "NIST 800-63B KDF for password storage",
            "PASS via vendor. GoTrue bcrypt + per-hash salt. Application tables never persist the password.",
            True,
        ),
        (
            "Custom application password hasher",
            "None. AuthService docstring: Supabase Auth owns every secret/credential.",
            True,
        ),
    ]
    for title, detail, ok in rows:
        d.text((MARGIN, y), title, font=F_BODY, fill=OK if ok else INK)
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
                "User passwords are stored only by Supabase Auth as salted bcrypt hashes. Velvet Elves stores a profile row without a password column. We have not exported production encrypted_password values. Vendor documentation is attached instead of a database dump.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_1_1_3_page2.png", "PNG")
    print("wrote", OUT / "CASA_1_1_3_page2.png")


def schema_page():
    im = Image.new("RGB", (1400, 720), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "1.1.3 public.users has no password column", font=F_H, fill=INK)
    d.text(
        (MARGIN, 98),
        "Source: supabase/migrations/20260225_init.sql  |  UserRepository.create never inserts a password",
        font=F_SMALL,
        fill=MUTED,
    )
    sql = """create table if not exists public.users (
  id varchar(36) primary key,
  tenant_id varchar(36) not null,
  email varchar(512) not null unique,
  full_name varchar(512),
  phone varchar(512),
  role varchar(32) not null default 'Agent',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
-- Later migrations add profile fields. None add a password column.
-- Password hashes live in GoTrue auth.users.encrypted_password (bcrypt)."""
    lines = sql.split("\n")
    box_y = 140
    box_h = 28 * len(lines) + 56
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 24
    for line in lines:
        d.text((MARGIN + 28, y), line, font=F_MONO, fill=CODE_FG)
        y += 28
    d.text((MARGIN, box_y + box_h + 20), "CASA_1_1_3_users_schema", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_1_1_3_users_schema.png", "PNG")
    print("wrote", OUT / "CASA_1_1_3_users_schema.png")


if __name__ == "__main__":
    page1()
    page2()
    schema_page()
