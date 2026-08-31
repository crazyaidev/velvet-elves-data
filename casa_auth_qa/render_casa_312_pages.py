"""Render CASA 3.1.2 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.2")
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
    d.text((W - MARGIN - 260, H - 42), "CASA_3_1_2_policy_attrs", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("3.1.2 Policy attributes are server-side", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 4.1.2. AL1 shares the 3.1.1 to 3.1.3 written description. Verification: user and data attributes used by access controls cannot be manipulated by the end user.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Session identity is loaded from the profile", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "get_current_user verifies the JWT sub, then reads role, tenant_id, is_platform_admin, and is_active from the users row. Those fields are not taken from the request body.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Clients cannot pick another tenant", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "POST /users/register accepts tenant_id for old clients and ignores it. The server always provisions a new tenant. OAuth ignores user_metadata.tenant_id and role (founder is Admin of a new tenant). Joining an existing org is invitation-only. X-Workspace-Id is allowed only for an active membership.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Profile PATCH cannot change policy fields", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "UserUpdateRequest has no role, tenant_id, is_platform_admin, or is_active. Extra is_active is ignored. Onboarding company PATCH drops role. After signup, role changes use PUT /users/{id}/role in the same tenant. There is no self-service API to set is_platform_admin. A founder may choose a self-signup role only on the new tenant they just created.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_2_page1.png", "PNG")
    print("wrote", OUT / "CASA_3_1_2_page1.png")


def page2():
    im, d, y = new_page("3.1.2 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Attributes not from client JSON",
            "get_current_user loads role and tenant from the server profile.",
            True,
        ),
        (
            "Cannot join another tenant at signup",
            "test_register_mints_fresh_tenant_and_ignores_client_supplied. OAuth ignores metadata tenant_id.",
            True,
        ),
        (
            "Cannot self-set role / active / platform admin",
            "PATCH /me schema. test_profile_update_cannot_self_deactivate. test_company_patch_role_is_ignored.",
            True,
        ),
        (
            "Staging",
            "Unsigned PATCH /users/me with role, tenant_id, is_platform_admin, is_active returns 401.",
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
                "Velvet Elves does not let an end user set the tenant, platform-admin flag, or active flag used by access control. Role after signup is an admin path in the same tenant. Signup cannot join an existing tenant by posting tenant_id.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_2_page2.png", "PNG")
    print("wrote", OUT / "CASA_3_1_2_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.2 Server ignores client policy fields", font=F_H, fill=INK)
    snippet = """# app/services/auth_service.py  register()
# ignore payload.tenant_id — always provision a fresh tenant
tenant_id = await self._tenants.provision_for_self_registration(...)

# app/services/oauth_service.py
# ignore metadata.tenant_id and metadata.role
role = UserRole.ADMIN
tenant_id = await self._tenants.provision_for_self_registration(...)

# app/schemas/user.py  UserUpdateRequest
# no role, tenant_id, is_platform_admin, is_active

# app/core/auth.py  get_current_user
payload = decode_access_token(token)   # sub only
user = await repo.get_by_id(payload["sub"])  # role + tenant from DB"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_2_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_2_code.png", "PNG")
    print("wrote", OUT / "CASA_3_1_2_code.png")


def tests_page():
    im = Image.new("RGB", (1400, 820), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.2 Tests that client policy fields are ignored", font=F_H, fill=INK)
    snippet = """test_register_mints_fresh_tenant_and_ignores_client_supplied
  POST /users/register tenant_id=tenant-legacy → new UUID tenant

test_oauth_exchange_ignores_client_supplied_tenant_id
  OAuth metadata.tenant_id is not joined

test_profile_update_cannot_self_deactivate
  PATCH /users/me {is_active: false} → still active

test_company_patch_role_is_ignored
  PATCH /onboarding/company {role: Vendor} → role unchanged"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_2_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_2_tests.png", "PNG")
    print("wrote", OUT / "CASA_3_1_2_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    tests_page()
