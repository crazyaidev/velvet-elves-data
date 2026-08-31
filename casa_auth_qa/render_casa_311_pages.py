"""Render CASA 3.1.1 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.1")
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
    d.text((W - MARGIN - 280, H - 42), "CASA_3_1_1_least_privilege", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("3.1.1 Least privilege on the API", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 4.1.1. AL1 is documentation of authentication, authorization, roles, and least privilege. Verification: access control is enforced on a trusted service layer. ADA says 3.1.1 through 3.1.3 share one written description. This is that description for least privilege.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. Trusted service layer is FastAPI", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "The browser hides routes (ProtectedRoute, RoleRoute). The API is the control. get_current_user verifies the JWT and loads role and tenant_id from the server profile. require_role, require_tenant_access, and require_transaction_access run on the request. Repositories also filter tenant_id. Postgres RLS is defense in depth; the service-role client can bypass RLS, so the API must not rely on it as the primary control.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. Roles", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "UserRole: Agent, TransactionCoordinator, TeamLead, Attorney, Admin, Client, ForSaleByOwner, Vendor. Admin satisfies every role check. TeamLead satisfies TeamLead, Agent, and TC. Other roles satisfy only themselves. is_platform_admin is a separate flag. Tenant Admin is not cross-tenant and cannot call /api/v1/platform/* without that flag plus AAL2.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Least privilege examples", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Clients cannot create transactions (403). Agents cannot GET another user's profile. Intra-tenant, Agent/TC/Attorney see a transaction only if they created it or are assigned; Admin/TeamLead see the tenant. Gmail tokens are per user_id, not a shared mailbox. Platform user list requires platform admin plus AAL2.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_1_page1.png", "PNG")
    print("wrote", OUT / "CASA_3_1_1_page1.png")


def page2():
    im, d, y = new_page("3.1.1 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "Trusted service layer",
            "FastAPI dependencies. SPA RoleRoute is UX only.",
            True,
        ),
        (
            "Roles documented",
            "Eight UserRole values plus is_platform_admin. Hierarchy in ROLE_HIERARCHY.",
            True,
        ),
        (
            "Least privilege",
            "Tenant scope, assignment scope, platform flag. Tests in test_rbac.py and M9f isolation tests.",
            True,
        ),
        (
            "Staging",
            "Unsigned GET /users/ and GET /platform/users return 401. Platform AAL2 is in require_platform_admin (see 3.3.1).",
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
                "Velvet Elves enforces least privilege on the API. Users and tenants are scoped from the verified session. Tenant Admin is not a cross-tenant superuser. The platform console is a separate, MFA-gated path.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_1_page2.png", "PNG")
    print("wrote", OUT / "CASA_3_1_1_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1120), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.1 Role hierarchy and API guards", font=F_H, fill=INK)
    snippet = """# app/models/enums.py  — Admin satisfies all; Agent satisfies Agent only
ROLE_HIERARCHY[ADMIN] = {ADMIN, TEAM_LEAD, AGENT, TC, ATTORNEY, CLIENT, FSBO, VENDOR}
ROLE_HIERARCHY[AGENT] = {AGENT}

# app/core/auth.py
def require_role(*roles):
    if current_user.is_tenant_owner: return current_user
    if role_has_permission(current_user.role, required): return current_user
    raise HTTPException(403, "You do not have permission...")

def require_tenant_access(user, tenant_id):
    if user.is_platform_admin: return
    if user.tenant_id != tenant_id: raise HTTPException(403)

# require_transaction_access: same tenant; Agent/TC/Attorney must be
# creator or assigned. Admin/TeamLead see the tenant.

# /api/v1/platform/*  →  require_platform_admin (flag + aal2)"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_1_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_1_code.png", "PNG")
    print("wrote", OUT / "CASA_3_1_1_code.png")


def tests_page():
    im = Image.new("RGB", (1400, 980), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.1 Automated least-privilege tests", font=F_H, fill=INK)
    snippet = """# app/tests/test_rbac.py
test_agent_only_has_own_role
test_client_cannot_access_agent_routes
test_client_role_cannot_create_transaction          → 403
test_agent_cannot_fetch_other_user                  → 403

# Isolation (see M9f)
test_two_self_registrations_get_isolated_tenants
test_tenant_admin_cannot_read_another_tenant_by_id  → 403
test_admin_cannot_manage_user_in_another_tenant
test_task_get_by_id_respects_tenant_filter
test_api_key_acts_only_in_its_own_tenant
test_property_detail_cross_owner_returns_404

Enforcement is the API. SPA RoleRoute is not the control."""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_1_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_1_tests.png", "PNG")
    print("wrote", OUT / "CASA_3_1_1_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    tests_page()
