"""Render CASA 5.1.2 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.1.2")
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
    d.text((W - MARGIN - 280, H - 42), "CASA_5_1_2_redirect", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("5.1.2 Redirects are limited to allowlisted URLs", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0. AL1 evidence is ADA DAST. Verification: the scan shall not identify Burp 5243136, 5243137, 5243152, 5243153, or 5243154 (open redirection). Official scans were ZAP with the ADA CASA conf. WSTG-CLNT-04 is AL2.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Official ADA ZAP (21 Aug 2026)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "SPA 10f54abf, API a9d78f05, authenticated API 33afa2aa, all against staging. SPA conf maps plugin 20019 External Redirect to FAIL. API conf maps it to WARN. DAST_SUMMARY.md alert tables do not list External Redirect or open redirection. SPA was 0 High. API and auth scans exited 0. We did not run Burp.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Allowlisted redirects", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "OAuth sign-in redirect_to is checked with validate_redirect_to against CORS_ORIGINS. A foreign origin is 400 redirect_to is not an allowed origin. Password-reset redirect_to that is not allowlisted is ignored; the email uses FRONTEND_URL or an allowlisted Origin. Integration OAuth redirect_uri is set by the server. Callback HTML postMessage targets FRONTEND_URL, not *.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Other navigations", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "GET /ads/{hook_id}/click 302s only to a stored click_url (SSRF-safe http/https). The request has no url query parameter. An unknown hook is 404 with no Location. The SPA restores post-login paths from React Router state or localStorage; those paths must start with /. A ?next=https://evil.example query does not produce a Location header to that host.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "4. Staging measurement (31 Aug 2026)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/oauth/google/start with redirect_to https://evil.example/steal returned 400 and no Location. Password-reset with that same redirect_to returned 202 and a generic message (no evil host). GET /ads/{uuid}/click returned 404 Ad not found and no Location. SPA GET /?next=https://evil.example/steal returned 200 HTML with no Location. Consent was not completed.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_5_1_2_page1.png", "PNG")
    print("wrote", OUT / "CASA_5_1_2_page1.png")


def page2():
    im, d, y = new_page("5.1.2 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Official DAST",
            "ZAP 20019 enabled (SPA FAIL, API WARN). Alert lists did not include External Redirect.",
            True,
        ),
        (
            "Burp open-redirection plugins",
            "ADA names 5243136–5243154. Burp was not run. Closest official analog is ZAP 20019.",
            True,
        ),
        (
            "OAuth redirect_to",
            "Foreign origin is 400. This is an origin allowlist, not a single exact path.",
            True,
        ),
        (
            "Password reset",
            "Disallowed redirect_to is ignored. Response is 202 with no foreign Location.",
            True,
        ),
        (
            "Ad click and SPA query",
            "Unknown ad hook is 404. SPA ?next= to a foreign host has no Location header.",
            True,
        ),
        (
            "SPA spider scope",
            "Traditional spider hit /, /robots.txt, /sitemap.xml. Authenticated SPA routes were not crawled.",
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
                "Velvet Elves does not send users to untrusted hosts from user-supplied redirect parameters. Official ADA ZAP scans did not report External Redirect. Staging foreign OAuth redirect_to is 400. WSTG-CLNT-04 was not run.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_5_1_2_page2.png", "PNG")
    print("wrote", OUT / "CASA_5_1_2_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "5.1.2 Origin allowlist and stored click URL", font=F_H, fill=INK)
    snippet = """# app/utils/redirects.py
if not is_allowed_redirect(redirect_to, allowed_list):
    raise HTTPException(400, "redirect_to is not an allowed origin.")

# app/utils/oauth_popup.py
# postMessage target is FRONTEND_URL origin, not "*"

# app/api/v1/advertising.py  GET /ads/{hook_id}/click
url = await AdvertisingService(supabase).record_click(hook_id)
return RedirectResponse(url=url, status_code=302)
# record_click 404s if the hook is missing. No url= query param.

# SPA returnLocation.ts
# Restored paths must start with "/". External URLs are dropped."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_5_1_2_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_5_1_2_code.png", "PNG")
    print("wrote", OUT / "CASA_5_1_2_code.png")


def zap_page():
    im = Image.new("RGB", (1400, 980), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "5.1.2 Official ADA ZAP External Redirect", font=F_H, fill=INK)
    snippet = """# zap-casa-config.conf  (SPA)
20019    FAIL    (External Redirect - Active/release)

# zap-casa-api-config.conf  (API)
20019    WARN    (External Redirect - Active/release)

# Official scans (21 Aug 2026) — DAST_SUMMARY.md
SPA  10f54abf   https://app.stage.velvetelves.com
API  a9d78f05   https://api.stage.velvetelves.com
Auth 33afa2aa   authenticated API, Bearer JWT

Alert lists did not include External Redirect
or open redirection.

ADA AL1: scan shall not identify Burp
5243136 / 5243137 / 5243152 / 5243153 / 5243154.
Burp was not run. Closest analog is ZAP 20019."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_5_1_2_zap", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_5_1_2_zap.png", "PNG")
    print("wrote", OUT / "CASA_5_1_2_zap.png")


def tests_page():
    im = Image.new("RGB", (1400, 780), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "5.1.2 Tests that foreign redirects are not honored", font=F_H, fill=INK)
    snippet = """test_password_reset_request_falls_back_to_request_origin
  malicious redirect_to is ignored; Origin /reset-password is used

test_frontend_post_message_origin_uses_scheme_and_host
  FRONTEND_URL origin only

test_email_oauth_callback_html_does_not_use_wildcard_origin
  postMessage is not "*"

Live 31 Aug 2026:
  OAuth start evil redirect_to → 400, Location none
  Password reset evil redirect_to → 202, Location none
  GET /ads/{uuid}/click → 404, Location none
  SPA ?next=https://evil.example → 200, Location none"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_5_1_2_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_5_1_2_tests.png", "PNG")
    print("wrote", OUT / "CASA_5_1_2_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    zap_page()
    tests_page()
