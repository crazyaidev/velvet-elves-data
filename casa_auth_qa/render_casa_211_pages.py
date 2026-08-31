"""Render CASA 2.1.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.1.1")
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
    d.text((W - MARGIN - 280, H - 42), "CASA_2_1_1_no_tokens_in_url", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("2.1.1 No passwords or session tokens in URLs", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 3.1.1. AL1 evidence is ADA DAST (ZAP).",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Login password", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /api/v1/users/login sends username and password in the HTTP body (application/x-www-form-urlencoded). The SPA login form uses method POST via apiFetch. Putting the password on a GET query string is not a supported login path.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Session JWT", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "apiFetch sets Authorization: Bearer <token>. FastAPI OAuth2PasswordBearer reads that header only. The SPA stores the access and refresh JWTs in localStorage (velvet_elves_token / velvet_elves_refresh_token), not in the address bar.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. OAuth and password reset", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Google / Outlook / DocuSign OAuth is authorization code + PKCE. The API callback page postMessages the opener and does not put Google tokens in the Velvet Elves SPA query string.",
                F_BODY,
                INK,
            ),
            (
                "Password-reset confirm is POST /users/password-reset/confirm with the recovery token in the JSON body. GoTrue recovery emails may use a URL fragment (#access_token=), which is not a query parameter and is not sent to the API.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "4. Capability tokens (not the session JWT)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Invite accept emails use /invite/accept?token= (activation token; see 1.1.2). Public invoice pay links may include a one-time capability token. A fulfilled communications-export download also accepts a short-lived download token as a query param and still requires Authorization Bearer. Those are not the user session JWT.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_1_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_2_1_1_page1.png")


def page2():
    im, d, y = new_page("2.1.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "DAST (ADA ZAP config)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Official CASA ZAP scans: SPA 10f54abf, API a9d78f05, authenticated API 33afa2aa. Config marks plugin 3 (Session ID in URL Rewrite) and plugin 10024 (Sensitive Information in URL) as FAIL. Those alerts are not in the DAST_SUMMARY finding lists. Scans reported 0 High.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Password submitted using GET",
            "Login is POST body only. Staging GET /users/login with username and password in the query does not authenticate (401). The query string is not a login.",
            True,
        ),
        (
            "Password returned in URL query string",
            "Login and register responses are JSON. The SPA address bar after opening /login has no password query parameter.",
            True,
        ),
        (
            "Session token in URL",
            "Session JWT is Authorization Bearer. Staging GET /users/me?access_token=not-a-session is unauthenticated. Query token is ignored.",
            True,
        ),
        (
            "Option to send secrets in body or header",
            "Password in POST body. JWT in Authorization header.",
            True,
        ),
    ]
    for title, detail, ok in rows:
        color = OK if ok else INK
        d.text((MARGIN, y), title, font=F_BODY, fill=color)
        y += 24
        y = paint(d, y, [(detail, F_SMALL, MUTED)])
        y += 8
    im.save(OUT / "CASA_2_1_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_2_1_1_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 820), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.1.1 Password in POST body; JWT in Authorization", font=F_H, fill=INK)
    d.text(
        (MARGIN, 98),
        "LoginPage.tsx and apiFetch — session is not placed on the query string",
        font=F_SMALL,
        fill=MUTED,
    )
    snippet = """# LoginPage — POST body, not GET query
await apiFetch('/api/v1/users/login', {
  method: 'POST',
  body: { username: data.email, password: data.password },
  formEncoded: true,
})

# apiFetch — session JWT on the header
if (token) {
  headers['Authorization'] = `Bearer ${token}`
}

# FastAPI — OAuth2PasswordBearer reads Authorization only
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")"""
    lines = snippet.split("\n")
    box_y = 140
    box_h = 26 * len(lines) + 48
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 20
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 26
    d.text((MARGIN, box_y + box_h + 20), "CASA_2_1_1_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_2_1_1_code.png", "PNG")
    print("wrote", OUT / "CASA_2_1_1_code.png")


def stamp_login():
    raw = OUT / "CASA_2_1_1_login_raw.png"
    src = OUT / "CASA_2_1_1_login.png"
    base_path = raw if raw.exists() else src
    if not base_path.exists():
        return
    url_file = OUT / "login_url.txt"
    url = url_file.read_text(encoding="utf-8").strip() if url_file.exists() else ""
    if not url:
        url = "https://app.stage.velvetelves.com/login"
    base = Image.open(base_path).convert("RGB")
    bar_h = 56
    im = Image.new("RGB", (base.width, base.height + bar_h), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, base.width, bar_h), fill=(36, 36, 36))
    d.text((20, 8), "Address (live staging)", font=F_SMALL, fill=(180, 180, 176))
    d.text((20, 28), url, font=F_BODY, fill=(230, 230, 226))
    im.paste(base, (0, bar_h))
    im.save(src, "PNG")
    print("stamped", src, url)


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    stamp_login()
