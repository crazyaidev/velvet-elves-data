"""Render CASA 2.2.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.2.1")
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
F_MONO = mono(13)


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
    d.text((W - MARGIN - 220, H - 42), "CASA_2_2_1_logout", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("2.2.1 Logout invalidates the session", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 3.3.1.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. User can log out", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "The app menu includes Log Out. The platform MFA gate includes Sign out. Both call AuthContext.logout(), which POSTs /api/v1/users/logout and then clears localStorage keys velvet_elves_token and velvet_elves_refresh_token. The browser is sent to /login.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Server-side revocation", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/logout requires a Bearer token. If the JWT decodes, the API calls GoTrue auth.admin.sign_out(token, scope local). That revokes this session's refresh token so it cannot be replayed. If the JWT is already invalid or expired, the API still returns HTTP 204 so the client can finish sign-out.",
                F_BODY,
                INK,
            ),
            (
                "The access JWT is stateless. It expires on its own (under 24 hours; see 2.2.3). Logout's server-side job is the stateful refresh token. Scope local means this session, not every device.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Staging check", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Login issued a refresh token. POST /users/logout returned 204. Replaying that same refresh token to POST /users/refresh returned 401 Refresh token is invalid or expired.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_2_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_2_2_1_page1.png")


def page2():
    im, d, y = new_page("2.2.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "User can log out",
            "Log Out in the app menu. Sign out on the MFA gate. Both call AuthContext.logout().",
            True,
        ),
        (
            "Server-side invalidation on logout",
            "GoTrue admin.sign_out(local). Staging: refresh replay after logout returns 401.",
            True,
        ),
        (
            "Session expiration",
            "Access JWT expires on its own (2.2.3). A stale or revoked refresh token returns 401 and the SPA redirects to /login.",
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
                "Logout revokes the Supabase session for this device and clears browser storage. The refresh token cannot be reused. The access JWT is short-lived and is not a server-side session row.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_2_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_2_2_1_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 920), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.2.1 Logout revokes GoTrue, then clears storage", font=F_H, fill=INK)
    snippet = """# app/api/v1/users.py
@router.post("/logout", status_code=204)
async def logout(token: str = Depends(oauth2_scheme), ...):
    try:
        decode_access_token(token)
    except JWTError:
        return Response(status_code=204)
    await supabase.auth.admin.sign_out(token, "local")
    return Response(status_code=204)

# AuthContext.tsx
void fetch(buildApiUrl('/api/v1/users/logout'), {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
  keepalive: true,
})
clearTokens()  // removes velvet_elves_token and velvet_elves_refresh_token"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_2_2_1_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_2_2_1_code.png", "PNG")
    print("wrote", OUT / "CASA_2_2_1_code.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
