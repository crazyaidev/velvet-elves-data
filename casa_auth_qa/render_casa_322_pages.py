"""Render CASA 3.2.2 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.2.2")
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
    d.text((W - MARGIN - 260, H - 42), "CASA_3_2_2_redirect_state", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("3.2.2 OAuth redirect_uri and state are validated", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0. AL1: written description plus evidence of how state and redirect_uri prevent open redirect and OAuth CSRF. WSTG-ATHZ-05 is AL2 and was not run.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Sign-in redirect_to (Google / Microsoft)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/oauth/{provider}/start requires redirect_to to match a CORS allowlisted origin (validate_redirect_to). A foreign origin returns 400. This is an origin check, not a single exact path. Tokens cannot be sent to an unlisted host.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Sign-in and integration state", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Sign-in state is a Fernet token (provider plus PKCE verifier) with a 10-minute TTL. Exchange rejects missing, tampered, expired, or provider-mismatched state with 400 Invalid or expired OAuth state, before any code exchange. Gmail, Outlook, Calendar, and DocuSign encrypt user_id, provider, redirect_uri, and the verifier in the same way. Those redirect_uri values are set by the API from configuration, not by the client.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Callback postMessage", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Integration callback HTML posts to the FRONTEND_URL origin, not *. The SPA ignores messages unless the origin is the API host (isTrustedOAuthMessageOrigin).",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "4. Staging (flow not completed)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Foreign redirect_to returned 400. Allowlisted SPA callback returned 200. Garbage state on exchange returned 400. Consent was not completed. Google Cloud lists production Gmail, Calendar, and Supabase Auth callback URIs (secret not shown).",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_2_2_page1.png", "PNG")
    print("wrote", OUT / "CASA_3_2_2_page1.png")


def page2():
    im, d, y = new_page("3.2.2 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "redirect_uri / redirect_to",
            "Sign-in origin must be on CORS_ORIGINS. Integration redirect_uri is server-set. GCP lists those production callback URIs.",
            True,
        ),
        (
            "state",
            "Fernet, 10-minute TTL. Forged or mismatched state is 400 before exchange.",
            True,
        ),
        (
            "Open redirect",
            "Foreign host on start is 400. Callbacks do not echo untrusted redirect URLs.",
            True,
        ),
        (
            "OAuth CSRF",
            "State binds the flow. postMessage is locked to FRONTEND_URL, not *.",
            True,
        ),
        (
            "Staging",
            "evil.example redirect_to 400. Garbage exchange state 400. Flow not completed.",
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
                "Velvet Elves OAuth uses validated redirect_uri and state to prevent open redirect and OAuth CSRF. We did not run WSTG-ATHZ-05.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_2_2_page2.png", "PNG")
    print("wrote", OUT / "CASA_3_2_2_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1180), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.2.2 redirect_to allowlist and Fernet state", font=F_H, fill=INK)
    snippet = """# app/utils/redirects.py
if not is_allowed_redirect(redirect_to, allowed_list):
    raise HTTPException(400, "redirect_to is not an allowed origin.")

# app/services/oauth_service.py  sign-in
redirect_to = validate_redirect_to(payload.redirect_to, cors_origins)
state_data = _decode_state(payload.state)  # Fernet, 10 min TTL
if not state_data:
    raise HTTPException(400, "Invalid or expired OAuth state.")

# app/api/v1/integrations.py  Gmail (Outlook/Calendar/DocuSign same idea)
redirect_uri = _derive_email_redirect_uri(
    request, provider="gmail", override=gmail_redirect_uri
)  # not supplied by the SPA"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_2_2_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_2_2_code.png", "PNG")
    print("wrote", OUT / "CASA_3_2_2_code.png")


def tests_page():
    im = Image.new("RGB", (1400, 900), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.2.2 Tests for state and postMessage origin", font=F_H, fill=INK)
    snippet = """test_oauth_exchange_rejects_tampered_state
  POST /users/oauth/google/exchange garbage state → 400
  "Invalid or expired OAuth state."

test_oauth_exchange_rejects_provider_mismatch
  Azure-minted state on Google exchange → 400

test_email_oauth_callback_html_does_not_use_wildcard_origin
  postMessage target is FRONTEND_URL origin, not *

isTrustedOAuthMessageOrigin("https://evil.example") → false"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_2_2_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_2_2_tests.png", "PNG")
    print("wrote", OUT / "CASA_3_2_2_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    tests_page()
