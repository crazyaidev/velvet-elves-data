"""Render CASA 2.2.2 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\2.2.2")
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
    d.text((W - MARGIN - 280, H - 42), "CASA_2_2_2_password_change", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("2.2.2 Other sessions after password change", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 3.3.3. AL1 is code or documentation.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Password change is reset / recovery", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "There is no logged-in current-password form. Users change the password with Forgot password. Confirm is POST /users/password-reset/confirm. Success copy is Password updated successfully. Please sign in. The SPA then redirects to /login.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. GoTrue terminates other sessions by default", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "The app does not call sign_out(others). It updates the password through GoTrue. GoTrue User.UpdatePassword then deletes auth.sessions rows for that user.",
                F_BODY,
                INK,
            ),
            (
                "If confirm has a recovery session, GoTrue keeps that session and logs out every other session (LogoutAllExceptMe). The SPA does not keep the recovery session; it sends the user to sign in.",
                F_BODY,
                INK,
            ),
            (
                "If confirm uses admin.update_user_by_id with the new password, GoTrue passes a nil session id and logs out all sessions for that user (Logout).",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Access JWT and federated login", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Refresh tokens on other devices cannot be reused after those session rows are deleted. The short-lived access JWT is stateless and expires on its own (under 24 hours; see 2.2.3).",
                F_BODY,
                INK,
            ),
            (
                "Google Sign-in sessions are GoTrue sessions on the same user id and are deleted with those rows. Gmail and Calendar mailbox OAuth tokens are not login sessions and are not claimed here.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_2_2_page1.png", "PNG")
    print("wrote", OUT / "CASA_2_2_2_page1.png")


def page2():
    im, d, y = new_page("2.2.2 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Password change includes reset / recovery",
            "Forgot password is the product path. Confirm posts the new password to GoTrue.",
            True,
        ),
        (
            "Other sessions terminated by default",
            "GoTrue UpdatePassword: LogoutAllExceptMe when a session is present; Logout of all sessions on admin password update.",
            True,
        ),
        (
            "Option to terminate",
            "Not a UI checkbox. ADA allows acting by default. There is no in-app password form.",
            True,
        ),
        (
            "Stateful refresh tokens",
            "Deleted session rows cannot refresh. Access JWT expiry is 2.2.3.",
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
                "After a successful password reset, GoTrue terminates other active sessions for that user by default. The app then requires a new sign-in. This was attested from application confirm code plus public GoTrue source, not from a live two-device reset of a production account.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_2_2_2_page2.png", "PNG")
    print("wrote", OUT / "CASA_2_2_2_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 980), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.2.2 Password reset confirm updates GoTrue", font=F_H, fill=INK)
    snippet = """# app/api/v1/users.py  POST /password-reset/confirm
if payload.refresh_token:
    await auth_client.auth.set_session(payload.token, payload.refresh_token)
    await auth_client.auth.update_user({"password": payload.new_password})
    return MessageResponse(message="Password updated successfully. Please sign in.")

if user_id:  # JWT sub from the recovery access token
    await supabase.auth.admin.update_user_by_id(
        user_id,
        {"password": payload.new_password},
    )
    return MessageResponse(message="Password updated successfully. Please sign in.")

# PKCE auth code path also uses admin.update_user_by_id({password})
# ResetPasswordPage then navigates to /login."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_2_2_2_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_2_2_2_code.png", "PNG")
    print("wrote", OUT / "CASA_2_2_2_code.png")


def gotrue_page():
    im = Image.new("RGB", (1400, 920), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "2.2.2 GoTrue UpdatePassword (public source)", font=F_H, fill=INK)
    snippet = """# github.com/supabase/auth  internal/models/user.go
func (u *User) UpdatePassword(tx, sessionID) error {
    // ... persist encrypted_password, clear recovery tokens ...
    if sessionID == nil {
        // log out user from all sessions to ensure
        // reauthentication after password change
        return Logout(tx, u.ID)
    }
    // log out user from all other sessions
    return LogoutAllExceptMe(tx, *sessionID, u.ID)
}

# internal/api/admin.go  admin password update
if params.Password != nil {
    if terr := user.UpdatePassword(tx, nil); terr != nil { ... }
}"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text(
        (MARGIN, box_y + box_h + 16),
        "Public GoTrue source excerpt. Not a Supabase dashboard screenshot.",
        font=F_FOOT,
        fill=MUTED,
    )
    im.save(OUT / "CASA_2_2_2_gotrue.png", "PNG")
    print("wrote", OUT / "CASA_2_2_2_gotrue.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    gotrue_page()
