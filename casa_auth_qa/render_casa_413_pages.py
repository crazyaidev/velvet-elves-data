"""Render CASA 4.1.3 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.3")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1400, 1800
MARGIN = 56
BG = (248, 248, 246)
INK = (24, 24, 24)
MUTED = (80, 80, 80)
RULE = (200, 80, 70)
OK = (20, 90, 50)
WARN = (140, 70, 20)
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
    d.text((W - MARGIN - 260, H - 42), "CASA_4_1_3_crypto", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("4.1.3 Cryptography used for confidentiality and integrity", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0. AL1: describe encryption, hashing, and MAC/HMAC (algorithms, key size, IV, key management). Baseline SP.800-57 / SP.800-131Ar2, 112-bit security.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Encryption / decryption", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "PII and OAuth tokens at rest use cryptography Fernet: AES-128-CBC plus HMAC-SHA256 (128-bit security, above the 112-bit baseline). Key is a 256-bit Fernet key (ENCRYPTION_KEY) in AWS Secrets Manager. Production startup fails if the key is missing. Fernet generates a fresh 128-bit IV per token. The API decrypts to call Gmail/Calendar; this is not browser end-to-end encryption. No Fernet key is shown in this pack.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Hashing", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "User passwords are salted bcrypt in Supabase GoTrue, not in Velvet Elves tables. Capability tokens (share links, colleague invites, CRM keys) store SHA-256 hashes of the secret, not the secret. PKCE uses S256 (SHA-256). Email fingerprints and similar ids use SHA-256.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. MAC / HMAC and signatures", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Fernet authenticates ciphertext with HMAC-SHA256. Outbound webhooks and DocuSign-style callbacks use HMAC-SHA256. Session JWTs are ES256 (P-256) or HS256, verified with jose. TOTP uses HMAC-SHA1 per RFC 6238 for 6-digit authenticator codes, not for storing PII.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "4. SHA-1 that is not secret crypto", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Intake proposal ids call hashlib.sha1(...).hexdigest()[:16]. That is a short stable label for UI proposals (Fluid SAST F052 Low). It is not a password hash, token MAC, or PII cipher. Tokens and PII use Fernet. In transit, Qualys A+ still lists two TLS 1.2 CBC suites as WEAK on the API; modern clients negotiate TLS 1.3 AES-GCM (see 4.1.1).",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_4_1_3_page1.png", "PNG")
    print("wrote", OUT / "CASA_4_1_3_page1.png")


def page2():
    im, d, y = new_page("4.1.3 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Confidentiality of tokens/PII",
            "Fernet AES-128-CBC + HMAC-SHA256. Key in Secrets Manager. Production requires ENCRYPTION_KEY.",
            True,
        ),
        (
            "Passwords",
            "GoTrue salted bcrypt. Application tables have no password column.",
            True,
        ),
        (
            "Integrity hashes / HMAC",
            "SHA-256 hashes of capability secrets. HMAC-SHA256 on webhooks. JWT ES256/HS256.",
            True,
        ),
        (
            "IV",
            "Fernet library generates a unique 128-bit IV per encrypt. Not a static IV in app code.",
            True,
        ),
        (
            "SHA-1 proposal ids",
            "16 hex chars for intake labels only. Not claimed as 112-bit secret hashing. Compensating (F052).",
            False,
        ),
        (
            "Key rotation drill",
            "Not attached. Rotation is an ops task; this pack does not claim a completed rotation.",
            False,
        ),
    ]
    for title, detail, ok in rows:
        color = OK if ok else WARN
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
                "Velvet Elves uses Fernet (AES-128 + HMAC-SHA256) for tokens and PII, SHA-256 / HMAC-SHA256 for capability secrets and webhooks, bcrypt via GoTrue for passwords, and ES256/HS256 for session JWTs. SHA-1 appears only as a short intake proposal id, not as protection of confidential data.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_4_1_3_page2.png", "PNG")
    print("wrote", OUT / "CASA_4_1_3_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "4.1.3 Fernet at rest; production requires ENCRYPTION_KEY", font=F_H, fill=INK)
    snippet = """# app/utils/encryption.py
# Fernet = AES-128-CBC + HMAC-SHA256  (cryptography)
if not key:
    if settings.is_production:
        raise RuntimeError("ENCRYPTION_KEY must be set in production.")
    key = Fernet.generate_key().decode()  # dev only, ephemeral

def encrypt(plaintext: str) -> str:
    return get_fernet().encrypt(plaintext.encode()).decode()

def decrypt(ciphertext: str) -> str:
    if not ciphertext.startswith("gAAAAA"):
        return ciphertext  # legacy plaintext rows
    try:
        return get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Decryption failed — invalid or corrupted ciphertext.")"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_4_1_3_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_4_1_3_code.png", "PNG")
    print("wrote", OUT / "CASA_4_1_3_code.png")


def sha1_page():
    im = Image.new("RGB", (1400, 720), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "4.1.3 SHA-1 is only a short intake proposal id", font=F_H, fill=INK)
    snippet = """# app/services/intake_intelligence.py
def _proposal_id(kind: str, *parts: Any) -> str:
    blob = "|".join([kind, *(str(p) for p in parts)])
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]

# 16 hex chars. Not a password KDF. Not Fernet. Not a token MAC.
# Fluid SAST F052 Low — compensating: secrets use Fernet / SHA-256."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_4_1_3_sha1", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_4_1_3_sha1.png", "PNG")
    print("wrote", OUT / "CASA_4_1_3_sha1.png")


def tests_page():
    im = Image.new("RGB", (1400, 820), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "4.1.3 Tests that Fernet hides secrets and rejects garbage", font=F_H, fill=INK)
    snippet = """test_email_oauth_state_roundtrip
  encode_state Fernet token does not contain user_id or PKCE verifier
  decode_state restores the fields

test_email_oauth_state_rejects_garbage
  decode_state("not-a-fernet-token") is None

test_oauth_exchange_rejects_tampered_state
  garbage Fernet on Google exchange → 400

Live 31 Aug 2026: ephemeral Fernet round-trip; tampered token InvalidToken
  (CASA_4_1_3_fernet.png — production ENCRYPTION_KEY not used)"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_4_1_3_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_4_1_3_tests.png", "PNG")
    print("wrote", OUT / "CASA_4_1_3_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    sha1_page()
    tests_page()
