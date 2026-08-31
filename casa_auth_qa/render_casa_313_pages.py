"""Render CASA 3.1.3 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.3")
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
    d.text((W - MARGIN - 240, H - 42), "CASA_3_1_3_fail_secure", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("3.1.3 Access control fails closed", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 4.1.5. AL1 shares the 3.1.1 to 3.1.3 written description. Verification: access controls fail securely, including when an exception occurs.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Missing or bad credentials deny", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "OAuth2PasswordBearer returns 401 when Authorization is missing. get_current_user catches JWTError (invalid, expired, or tampered) and returns 401. A missing profile for the JWT sub is also 401. None of those paths load a user or return the resource.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Authorization misses are 403", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Inactive account and suspended tenant return 403. require_role and require_tenant_access raise 403; they do not return 200 with empty data. Some cross-owner reads return 404, which still denies. The scheduler tick requires X-VE-Cron-Secret; if the secret is unset the endpoint is unreachable.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Exceptions do not grant access", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Unhandled exceptions return HTTP 500 with a generic message. They do not skip the auth dependency or return the protected body. APP_DEBUG must be false in production.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_3_page1.png", "PNG")
    print("wrote", OUT / "CASA_3_1_3_page1.png")


def page2():
    im, d, y = new_page("3.1.3 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Fail closed on auth errors",
            "JWTError and missing bearer → 401. Tests: test_get_me_unauthenticated_returns_401.",
            True,
        ),
        (
            "Fail closed on authz errors",
            "403 on role/tenant miss. Client cannot create a transaction (403).",
            True,
        ),
        (
            "Exception path",
            "Generic 500 JSON. Cron tick fail-closed if secret unset.",
            True,
        ),
        (
            "Staging",
            "GET /users/me no auth and Bearer not-a-jwt → 401. POST /internal/schedules/tick no secret → 403.",
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
                "Velvet Elves access control fails closed. Missing or invalid credentials never yield the resource. Authorization misses are 403 or 404. Exceptions return a generic error, not the protected data.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_3_page2.png", "PNG")
    print("wrote", OUT / "CASA_3_1_3_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.3 Fail closed on JWT and cron errors", font=F_H, fill=INK)
    snippet = """# app/core/auth.py
try:
    payload = decode_access_token(token)
    if not payload.get("sub"): raise _CREDENTIALS_EXCEPTION  # 401
except JWTError:
    raise _CREDENTIALS_EXCEPTION  # 401, does not continue

# require_cron_secret — fail closed if secret unset
if not expected or not hmac.compare_digest(provided, expected):
    raise HTTPException(403, "Invalid or missing scheduler credentials.")

# app/core/exceptions.py  unhandled
return JSONResponse(500, {"message": "An internal server error occurred."})"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_3_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_3_code.png", "PNG")
    print("wrote", OUT / "CASA_3_1_3_code.png")


def tests_page():
    im = Image.new("RGB", (1400, 820), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.3 Tests that access control fails closed", font=F_H, fill=INK)
    snippet = """test_get_me_unauthenticated_returns_401
  GET /users/me with no Authorization → 401

test_unauthenticated_transaction_request_returns_401
  GET /transactions with no Authorization → 401

test_client_role_cannot_create_transaction
  Client POST /transactions → 403 (not 200)

test_tick_endpoint_fails_closed_without_secret
  POST /internal/schedules/tick, secret unset → 403"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_3_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_3_tests.png", "PNG")
    print("wrote", OUT / "CASA_3_1_3_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    tests_page()
