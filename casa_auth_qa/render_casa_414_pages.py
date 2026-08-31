"""Render CASA 4.1.4 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.4")
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
    d.text((W - MARGIN - 280, H - 42), "CASA_4_1_4_fail_closed", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("4.1.4 Cryptographic failures fail closed", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0. AL1: crypto failures must not disclose operation state or enable a padding oracle. User-facing errors stay vague and consistent. WSTG-CRYP-02 is AL2.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Fernet (tokens and PII)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Fernet verifies HMAC-SHA256 before AES-CBC decrypt. A bad MAC and a flipped ciphertext byte both raise cryptography InvalidToken. decrypt() turns that into ValueError Decryption failed — invalid or corrupted ciphertext. The exception text does not include plaintext. Display helpers (_safe_decrypt) catch any Exception and return empty or None so the UI never shows gAAAA ciphertext.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. OAuth state", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "decode_state catches InvalidToken, ValueError, KeyError, and TypeError and returns None. Exchange then returns 400 Invalid or expired OAuth state. Missing, tampered, wrong-key, and expired tokens share that one message. Staging POST /users/oauth/google/exchange with garbage state returned 400.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Session JWT", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "decode_access_token raises JWTError on invalid, expired, or tampered tokens. get_current_user maps every JWTError to 401 Could not validate credentials. Staging GET /users/me with Bearer not-a-jwt returned that 401. The response does not echo the token.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "4. Padding oracle", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "There is no application CBC decrypt that returns distinct padding errors. Fernet HMAC failure and payload failure are the same InvalidToken. This pack does not claim a full WSTG-CRYP-02 lab scan. Legacy rows that do not start with gAAAAA are returned as-is (plaintext migration), not as a decrypt-error oracle.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_4_1_4_page1.png", "PNG")
    print("wrote", OUT / "CASA_4_1_4_page1.png")


def page2():
    im, d, y = new_page("4.1.4 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Fernet InvalidToken",
            "HMAC flip and ciphertext flip both InvalidToken. No plaintext in the exception.",
            True,
        ),
        (
            "Display path",
            "_safe_decrypt / _safe_decrypt_value return empty or None. Ciphertext is not echoed.",
            True,
        ),
        (
            "OAuth state",
            "Garbage state is 400 Invalid or expired OAuth state (staging 31 Aug 2026).",
            True,
        ),
        (
            "JWT",
            "Garbage Bearer is 401 Could not validate credentials (staging 31 Aug 2026).",
            True,
        ),
        (
            "Consistent messages",
            "Users do not get distinct MAC vs padding vs expiry strings from Fernet or JWT.",
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
                "Velvet Elves cryptographic failures fail closed. Fernet and JWT errors do not return plaintext or distinct padding messages. Staging garbage JWT is 401; garbage OAuth state is 400.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_4_1_4_page2.png", "PNG")
    print("wrote", OUT / "CASA_4_1_4_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1180), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "4.1.4 InvalidToken, JWTError, and _safe_decrypt swallows", font=F_H, fill=INK)
    snippet = """# app/utils/encryption.py
except InvalidToken:
    raise ValueError("Decryption failed — invalid or corrupted ciphertext.")

# app/api/v1/dashboard.py  _safe_decrypt
except Exception:
    logger.warning("PII decrypt failed; returning empty placeholder")
    return ""

# app/services/oauth_service.py  _decode_state
except (InvalidToken, ValueError, KeyError, TypeError):
    return None
# exchange → 400 Invalid or expired OAuth state.

# app/core/auth.py
except JWTError:
    raise HTTPException(401, "Could not validate credentials.")"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_4_1_4_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_4_1_4_code.png", "PNG")
    print("wrote", OUT / "CASA_4_1_4_code.png")


def tests_page():
    im = Image.new("RGB", (1400, 780), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "4.1.4 Tests that failures do not leak ciphertext", font=F_H, fill=INK)
    snippet = """test_safe_decrypt_value_returns_none_for_fernet_looking_garbage
  gAAAAABFAKE_... must not be returned as the display name

test_email_oauth_state_rejects_garbage
  decode_state("not-a-fernet-token") is None

test_oauth_exchange_rejects_tampered_state
  garbage Fernet → 400

Live 31 Aug 2026:
  HMAC flip and ciphertext flip → InvalidToken
  GET /users/me Bearer not-a-jwt → 401
  POST oauth/google/exchange garbage state → 400"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_4_1_4_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_4_1_4_tests.png", "PNG")
    print("wrote", OUT / "CASA_4_1_4_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    tests_page()
