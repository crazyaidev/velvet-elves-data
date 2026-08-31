"""Render CASA 3.1.4 write-up pages as portal-ready PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\3.1.4")
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
    d.text((W - MARGIN - 220, H - 42), "CASA_3_1_4_idor", font=F_FOOT, fill=MUTED)
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
    im, d, y = new_page("3.1.4 Object IDs are not enough (IDOR)", 1)
    y = paint(
        d,
        y,
        [
            (
                "Source: ADA Web App Test Guide v1.0 / ASVS 4.2.1. AL1: list APIs that take a user-supplied URL or parameter ID, and describe how they are protected from Insecure Direct Object Reference.",
                F_SMALL,
                MUTED,
            ),
        ],
    )
    y += 8
    d.text((MARGIN, y), "1. APIs that take a caller-supplied ID", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Path IDs include /users/{id} (GET, PUT role, DELETE), /tenants/{id}, /transactions/{id} and nested deal routes, /documents/{id}, /invoices/{id}, /payments/{id}, /tasks/{id}, /teams/{id}, /audit-logs/{type}/{id}, and /platform/.../{id}. List endpoints are tenant-scoped, not a global dump. Public invoice and invite links may carry a capability token; those are not the session JWT.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "2. How those APIs are protected", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "Missing Authorization returns 401. The API then loads the row and calls require_tenant_access (403 if the tenant does not match). Deal objects also call require_transaction_access: Agents must be the creator or assigned. Tenant Admin is not cross-tenant. Some cross-owner reads return 404. Audit entity reads filter the caller's tenant_id.",
                F_BODY,
                INK,
            ),
        ],
    )
    y += 10
    d.text((MARGIN, y), "3. Staging (unsigned ID paths)", font=F_SEC, fill=INK)
    y += 32
    y = paint(
        d,
        y,
        [
            (
                "GET of a placeholder UUID on /transactions, /users, /tenants, /documents, and /invoices all returned 401. No other tenant was queried. No staging user was registered.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_4_page1.png", "PNG")
    print("wrote", OUT / "CASA_3_1_4_page1.png")


def page2():
    im, d, y = new_page("3.1.4 AL1 verification mapping", 2)
    d.text((MARGIN, y), "AL1 verification", font=F_SEC, fill=INK)
    y += 32
    rows = [
        (
            "List of user-parameter APIs",
            "Path IDs on users, tenants, transactions, documents, invoices, tasks, teams, audit, platform.",
            True,
        ),
        (
            "IDOR process",
            "JWT then load row then tenant check; deals also check assignment. Lists are tenant-scoped.",
            True,
        ),
        (
            "Named tests",
            "Other-tenant tenant/user 403. Other user's transaction 403. Unrelated document 404. Audit empty.",
            True,
        ),
        (
            "Staging",
            "Unsigned GET of placeholder UUIDs on those ID paths returns 401.",
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
                "Velvet Elves mitigates IDOR on the API. A guessed UUID does not return another tenant's or another user's record. Tenant Admin is not cross-tenant. Unsigned callers receive 401.",
                F_BODY,
                INK,
            ),
        ],
    )
    im.save(OUT / "CASA_3_1_4_page2.png", "PNG")
    print("wrote", OUT / "CASA_3_1_4_page2.png")


def code_page():
    im = Image.new("RGB", (1400, 1080), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.4 IDOR guards on object IDs", font=F_H, fill=INK)
    snippet = """# app/core/auth.py  require_transaction_access
tx = await tx_repo.get_by_id(transaction_id)
if tx is None: raise HTTPException(404)          # hide missing
require_tenant_access(user, tx.tenant_id)        # 403 other tenant
# Agent/TC/Attorney: creator or active assignment, else 403

# app/api/v1/users.py  GET /users/{user_id}
user = await repo.get_by_id(user_id)
require_tenant_access(current_user, user.tenant_id)

# app/api/v1/audit_logs.py
repo.get_for_entity(current_user.tenant_id, entity_type, entity_id)"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_4_code", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_4_code.png", "PNG")
    print("wrote", OUT / "CASA_3_1_4_code.png")


def tests_page():
    im = Image.new("RGB", (1400, 900), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1400, 10), fill=RULE)
    d.text((MARGIN, 36), "Velvet Elves  |  ADA-CASA AL1 evidence", font=F_SUB, fill=MUTED)
    d.text((MARGIN, 64), "3.1.4 Tests that object IDs do not leak", font=F_H, fill=INK)
    snippet = """test_tenant_admin_cannot_read_another_tenant_by_id
  GET /tenants/{other} → 403

test_admin_cannot_manage_user_in_another_tenant
  PUT /users/{other}/role and DELETE → 403

test_agent_cannot_get_other_users_transaction_by_id
  GET /transactions/{other} → 403

test_internal_user_cannot_fetch_document_from_unrelated_transaction
  GET /documents/{other} → 404

test_entity_audit_logs_do_not_leak_across_tenants
  GET /audit-logs/user/{other} → empty list"""
    lines = snippet.split("\n")
    box_y = 120
    box_h = 24 * len(lines) + 40
    d.rounded_rectangle((MARGIN, box_y, 1400 - MARGIN, box_y + box_h), radius=8, fill=CODE_BG)
    y = box_y + 18
    for line in lines:
        d.text((MARGIN + 24, y), line, font=F_MONO, fill=CODE_FG)
        y += 24
    d.text((MARGIN, box_y + box_h + 16), "CASA_3_1_4_tests", font=F_FOOT, fill=MUTED)
    im.save(OUT / "CASA_3_1_4_tests.png", "PNG")
    print("wrote", OUT / "CASA_3_1_4_tests.png")


if __name__ == "__main__":
    page1()
    page2()
    code_page()
    tests_page()
