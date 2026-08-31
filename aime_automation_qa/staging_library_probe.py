"""Staging library probe for Audri's updated task list (ID-preserving).

Logs in as the given admin, reads system templates, dry-runs preview-tasks
for each use case, and prints PASS/FAIL. Does not create deals or send mail.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

API = os.environ.get("QA_API", "https://api.stage.velvetelves.com").rstrip("/")
EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD", "")
OUT = os.environ.get("QA_OUT", "")

INACTIVE = {95, 115, 135, 155, 215, 235, 255, 305, 375, 380, 505}
SUPPRESSED_ON_DUAL = {30, 90, 120, 130, 160, 180, 440, 450, 510, 267, 275}
STANDARD_ON_DUAL = {100, 110, 140, 150, 250, 257, 300, 310, 370, 500}
NEVER_ON_NEW = INACTIVE
COOP_WELCOME = 30

findings: list[tuple[str, str, str]] = []


def log(id_: str, result: str, details: str = "") -> None:
    findings.append((id_, result, details))
    extra = f" — {details[:420]}" if details else ""
    print(f"[{result}] {id_}{extra}")


def req(method: str, path: str, token: str | None = None, data=None, form=None):
    url = f"{API}{path}"
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw[:2000]}
        return e.code, parsed


def expect(id_: str, cond: bool, details: str = "") -> None:
    log(id_, "PASS" if cond else "FAIL", details)


def by_legacy(items: list[dict]) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for t in items:
        lid = t.get("legacy_task_id")
        if lid is None:
            continue
        out[int(lid)] = t
    return out


def fetch_all_templates(token: str, is_active: bool) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        status, body = req(
            "GET",
            f"/api/v1/task-templates?is_active={'true' if is_active else 'false'}&page={page}&page_size=200",
            token,
        )
        if status != 200:
            log("templates.fetch", "FAIL", f"status={status} active={is_active} {body}")
            return items
        batch = body.get("items") or []
        items.extend(batch)
        pages = body.get("pages") or 1
        if page >= pages:
            break
        page += 1
    return items


def preview(token: str, **kwargs) -> tuple[int, dict]:
    today = date.today()
    payload = {
        "address": kwargs.pop("address", "900 Library Probe Ln"),
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "use_case": kwargs.pop("use_case"),
        "financing_type": kwargs.pop("financing_type", "Financed"),
        "representation_type": kwargs.pop("representation_type", "Buyer"),
        "purchase_price": 425000,
        "earnest_money": 5000,
        "earnest_money_days": 3,
        "contract_acceptance_date": str(today),
        "closing_date": str(today + timedelta(days=30)),
        "has_inspection": True,
        "inspection_days": 10,
        "inspection_response_days": 3,
        "has_hoa": False,
        "has_home_warranty": True,
        "has_appraisal": kwargs.pop("has_appraisal", True),
        "title_ordered_by": kwargs.pop("title_ordered_by", "us"),
        "warranty_ordered_by": kwargs.pop("warranty_ordered_by", "us"),
        "closing_mode": kwargs.pop("closing_mode", "title_escrow"),
        "is_owner_occupied": True,
    }
    payload.update(kwargs)
    return req("POST", "/api/v1/transactions/preview-tasks", token, data=payload)


def _legacy_for_preview_task(task: dict, by_tid: dict[str, dict]) -> int | None:
    lid = task.get("legacy_task_id")
    if lid is not None:
        return int(lid)
    tmpl = by_tid.get(task.get("template_id") or "")
    if tmpl and tmpl.get("legacy_task_id") is not None:
        return int(tmpl["legacy_task_id"])
    return None


def ids_from_preview(body: dict, by_tid: dict[str, dict]) -> set[int]:
    out = set()
    for t in body.get("tasks") or []:
        lid = _legacy_for_preview_task(t, by_tid)
        if lid is not None:
            out.add(lid)
    return out


def task_by_id(body: dict, lid: int, by_tid: dict[str, dict]) -> dict | None:
    for t in body.get("tasks") or []:
        if _legacy_for_preview_task(t, by_tid) == lid:
            return t
    return None


def main() -> int:
    if not PASSWORD:
        print("QA_PASSWORD is required", file=sys.stderr)
        return 2

    status, health = req("GET", "/api/health")
    expect("api.health", status == 200, f"status={status} {health}")

    status, login = req(
        "POST",
        "/api/v1/users/login",
        form={"username": EMAIL, "password": PASSWORD},
    )
    if status != 200 or not login.get("access_token"):
        log("login", "FAIL", f"status={status} {login}")
        return 1
    token = login["access_token"]
    log("login", "PASS", f"user={login.get('user', {}).get('email') or EMAIL}")

    status, me = req("GET", "/api/v1/users/me", token)
    expect("me", status == 200, json.dumps({k: me.get(k) for k in ("email", "role", "tenant_id") if isinstance(me, dict)}))

    active = fetch_all_templates(token, True)
    inactive = fetch_all_templates(token, False)
    a_map = by_legacy(active)
    i_map = by_legacy(inactive)
    by_tid = {t["id"]: t for t in active + inactive}
    log("templates.active_count", "PASS", str(len(active)))
    log("templates.inactive_count", "PASS", str(len(inactive)))

    for lid in (267, 275):
        t = a_map.get(lid)
        expect(f"tmpl.{lid}.exists_active", t is not None, json.dumps({
            "name": (t or {}).get("name"),
            "use_cases": (t or {}).get("use_cases"),
            "target": (t or {}).get("target"),
            "dep_rel": (t or {}).get("dep_rel"),
            "dep_task_id": (t or {}).get("dep_task_id"),
            "float_days": (t or {}).get("float_days"),
            "dual_agency_behavior": (t or {}).get("dual_agency_behavior"),
        }) if t else "missing")

    for lid in NEVER_ON_NEW:
        t_active = a_map.get(lid)
        t_inactive = i_map.get(lid)
        expect(
            f"tmpl.{lid}.inactive_for_new",
            t_active is None and t_inactive is not None,
            f"active={t_active is not None} inactive={t_inactive is not None} name={(t_inactive or t_active or {}).get('name')}",
        )

    t70 = a_map.get(70)
    t80 = a_map.get(80)
    expect("tmpl.70.description_package", bool(t70 and "withhold" in (t70.get("description") or "").lower()), (t70 or {}).get("description") or "missing")
    expect(
        "tmpl.80.courtesy_not_followup",
        bool(
            t80
            and "courtesy" in (t80.get("description") or "").lower()
            and "has title been ordered" in (t80.get("description") or "").lower()
        ),
        (t80 or {}).get("description") or "missing",
    )

    t160 = a_map.get(160)
    expect("tmpl.160.target_coop", (t160 or {}).get("target") == "Co-op Agent", json.dumps({k: (t160 or {}).get(k) for k in ("target", "description")}))

    t170 = a_map.get(170)
    expect("tmpl.170.target_agent", (t170 or {}).get("target") == "Agent", json.dumps({k: (t170 or {}).get(k) for k in ("target", "cc_targets", "description")}))
    expect(
        "tmpl.170.internal_reminder",
        bool(t170 and "internal reminder" in (t170.get("description") or "").lower()),
        (t170 or {}).get("description") or "missing",
    )

    t180 = a_map.get(180)
    expect("tmpl.180.target_coop", (t180 or {}).get("target") == "Co-op Agent", json.dumps({k: (t180 or {}).get(k) for k in ("target", "cc_targets")}))
    expect("tmpl.180.cc_tc", "TC" in ((t180 or {}).get("cc_targets") or []), str((t180 or {}).get("cc_targets")))

    t250 = a_map.get(250)
    expect("tmpl.250.buy_only", set((t250 or {}).get("use_cases") or []) == {"Buy-Fin", "Buy-Cash"}, str((t250 or {}).get("use_cases")))
    t257 = a_map.get(257)
    expect("tmpl.257.exists_active", t257 is not None, json.dumps({k: (t257 or {}).get(k) for k in ("use_cases", "dep_task_id", "dep_task_ids")}))
    expect("tmpl.257.dep_245", 245 in ((t257 or {}).get("dep_task_ids") or []) or (t257 or {}).get("dep_task_id") == 245, str((t257 or {}).get("dep_task_ids")))

    t265 = a_map.get(265)
    t271 = a_map.get(271)
    expect("tmpl.265.buy_cash_buyer", (t265 or {}).get("use_cases") == ["Buy-Cash"] and (t265 or {}).get("target") == "Buyer", json.dumps({k: (t265 or {}).get(k) for k in ("use_cases", "target")}))
    expect("tmpl.271.buy_cash_buyer", (t271 or {}).get("use_cases") == ["Buy-Cash"] and (t271 or {}).get("target") == "Buyer", json.dumps({k: (t271 or {}).get(k) for k in ("use_cases", "target")}))
    t267 = a_map.get(267)
    t275 = a_map.get(275)
    expect("tmpl.267.sell_cash_coop", (t267 or {}).get("use_cases") == ["Sell-Cash"] and (t267 or {}).get("target") == "Co-op Agent", json.dumps({k: (t267 or {}).get(k) for k in ("use_cases", "target", "dep_rel", "float_days")}))
    expect("tmpl.267.fs_plus3", (t267 or {}).get("dep_rel") == "FS" and str((t267 or {}).get("float_days")) in ("3", "3.0"), str((t267 or {}).get("float_days")))
    expect("tmpl.275.ss_minus15", (t275 or {}).get("dep_rel") == "SS" and str((t275 or {}).get("float_days")) in ("-15", "-15.0") and (t275 or {}).get("dep_task_id") == 1000, json.dumps({k: (t275 or {}).get(k) for k in ("dep_rel", "dep_task_id", "float_days", "target")}))

    t370 = a_map.get(370)
    expect(
        "tmpl.370.all_four_use_cases",
        set((t370 or {}).get("use_cases") or []) == {"Buy-Fin", "Buy-Cash", "Sell-Fin", "Sell-Cash"},
        str((t370 or {}).get("use_cases")),
    )

    t453 = a_map.get(453)
    t455 = a_map.get(455)
    expect("tmpl.453.ss_minus5", (t453 or {}).get("dep_rel") == "SS" and str((t453 or {}).get("float_days")) in ("-5", "-5.0"), json.dumps({k: (t453 or {}).get(k) for k in ("name", "dep_rel", "float_days", "cc_targets")}))
    expect("tmpl.455.ss_plus1", (t455 or {}).get("dep_rel") == "SS" and str((t455 or {}).get("float_days")) in ("1", "1.0"), json.dumps({k: (t455 or {}).get(k) for k in ("name", "dep_rel", "float_days", "cc_targets")}))
    expect("tmpl.453.cc_tc", "TC" in ((t453 or {}).get("cc_targets") or []), str((t453 or {}).get("cc_targets")))
    expect("tmpl.455.cc_tc", "TC" in ((t455 or {}).get("cc_targets") or []), str((t455 or {}).get("cc_targets")))

    t30 = a_map.get(30)
    expect("tmpl.30.merge_unsigned", bool(t30 and "signature" in (t30.get("description") or "").lower()), (t30 or {}).get("description") or "missing")

    for lid in SUPPRESSED_ON_DUAL:
        t = a_map.get(lid)
        expect(f"tmpl.{lid}.dual_suppressed", (t or {}).get("dual_agency_behavior") == "suppressed", str((t or {}).get("dual_agency_behavior")))
    for lid in STANDARD_ON_DUAL:
        t = a_map.get(lid)
        expect(f"tmpl.{lid}.dual_standard", (t or {}).get("dual_agency_behavior") == "standard", str((t or {}).get("dual_agency_behavior")))

    t420 = a_map.get(420)
    t430 = a_map.get(430)
    expect("tmpl.420.buyer_closing_info", bool(t420 and "closing" in (t420.get("name") or "").lower()), (t420 or {}).get("name"))
    expect("tmpl.430.seller_closing_info", bool(t430 and "closing" in (t430.get("name") or "").lower()), (t430 or {}).get("name"))

    t500 = a_map.get(500)
    t510 = a_map.get(510)
    expect("tmpl.500.feedback_not_sales", bool(t500 and "feedback" in (t500.get("description") or "").lower() and "10%" not in (t500.get("description") or "")), (t500 or {}).get("description"))
    expect("tmpl.510.feedback_not_sales", bool(t510 and "feedback" in (t510.get("description") or "").lower()), (t510 or {}).get("description"))

    t290 = a_map.get(290)
    expect("tmpl.290.deps_70_80", set((t290 or {}).get("dep_task_ids") or []) >= {70, 80}, str((t290 or {}).get("dep_task_ids")))

    # ── Preview generation ──────────────────────────────────────────────
    cases = [
        ("Buy-Fin", "Financed", "Buyer", True, "us"),
        ("Buy-Cash", "Cash", "Buyer", True, "us"),
        ("Sell-Fin", "Financed", "Seller", True, "us"),
        ("Sell-Cash", "Cash", "Seller", True, "us"),
        ("Both-Fin", "Financed", "Both", True, "us"),
        ("Both-Cash", "Cash", "Both", True, "us"),
    ]
    previews: dict[str, dict] = {}
    for use_case, fin, rep, has_appr, title_by in cases:
        status, body = preview(
            token,
            use_case=use_case,
            financing_type=fin,
            representation_type=rep,
            has_appraisal=has_appr,
            title_ordered_by=title_by,
            address=f"9 {use_case} Probe Ln",
        )
        expect(f"preview.{use_case}.ok", status == 200, f"status={status} {str(body)[:300]}")
        if status == 200:
            previews[use_case] = body
            lids = sorted(ids_from_preview(body, by_tid))
            names = [t.get("name") for t in (body.get("tasks") or [])]
            log(f"preview.{use_case}.ids", "PASS", ",".join(str(x) for x in lids) or "(none)")
            log(f"preview.{use_case}.names", "PASS", " | ".join(names)[:1500])
            leaked = sorted(ids_from_preview(body, by_tid) & NEVER_ON_NEW)
            expect(f"preview.{use_case}.no_inactive_ids", not leaked, f"leaked={leaked}")

    buy = previews.get("Buy-Fin") or {}
    buy_ids = ids_from_preview(buy, by_tid)
    expect("preview.Buy-Fin.has_250", 250 in buy_ids, "")
    expect("preview.Buy-Fin.no_257", 257 not in buy_ids, "")
    expect("preview.Buy-Fin.has_370", 370 in buy_ids, "")
    expect("preview.Buy-Fin.no_235", 235 not in buy_ids, "")
    expect("preview.Buy-Fin.no_265", 265 not in buy_ids, "financed should not get cash appraisal")

    sell = previews.get("Sell-Fin") or {}
    sell_ids = ids_from_preview(sell, by_tid)
    expect("preview.Sell-Fin.has_257", 257 in sell_ids, "")
    expect("preview.Sell-Fin.no_250", 250 not in sell_ids, "")
    expect("preview.Sell-Fin.has_370", 370 in sell_ids, "")
    expect("preview.Sell-Fin.no_235", 235 not in sell_ids, "")
    expect("preview.Sell-Fin.has_160", 160 in sell_ids, "")
    t160p = task_by_id(sell, 160, by_tid)
    expect("preview.Sell-Fin.160_to_coop", (t160p or {}).get("target") == "Co-op Agent", json.dumps({k: (t160p or {}).get(k) for k in ("name", "target", "cc_targets")}))
    expect("preview.Sell-Fin.has_453", 453 in sell_ids, "")
    expect("preview.Sell-Fin.has_455", 455 in sell_ids, "")
    expect("preview.Sell-Fin.no_265_267", not ({265, 267} & sell_ids), str({265, 267} & sell_ids))

    buy_cash = previews.get("Buy-Cash") or {}
    bc_ids = ids_from_preview(buy_cash, by_tid)
    expect("preview.Buy-Cash.has_265_271", {265, 271} <= bc_ids, str(bc_ids & {265, 267, 271, 275}))
    expect("preview.Buy-Cash.no_267_275", not ({267, 275} & bc_ids), str({267, 275} & bc_ids))
    t265p = task_by_id(buy_cash, 265, by_tid)
    expect("preview.Buy-Cash.265_to_buyer", (t265p or {}).get("target") == "Buyer", json.dumps({k: (t265p or {}).get(k) for k in ("name", "target")}))

    sell_cash = previews.get("Sell-Cash") or {}
    sc_ids = ids_from_preview(sell_cash, by_tid)
    expect("preview.Sell-Cash.has_267_275", {267, 275} <= sc_ids, str(sc_ids & {265, 267, 271, 275}))
    expect("preview.Sell-Cash.no_265_271", not ({265, 271} & sc_ids), str({265, 271} & sc_ids))
    t267p = task_by_id(sell_cash, 267, by_tid)
    t275p = task_by_id(sell_cash, 275, by_tid)
    expect("preview.Sell-Cash.267_to_coop", (t267p or {}).get("target") == "Co-op Agent", json.dumps({k: (t267p or {}).get(k) for k in ("name", "target", "cc_targets")}))
    expect("preview.Sell-Cash.275_to_coop", (t275p or {}).get("target") == "Co-op Agent", json.dumps({k: (t275p or {}).get(k) for k in ("name", "target")}))
    expect("preview.Sell-Cash.267_cc_tc", "TC" in ((t267p or {}).get("cc_targets") or []), str((t267p or {}).get("cc_targets")))

    both = previews.get("Both-Fin") or {}
    both_ids = ids_from_preview(both, by_tid)
    leaked_coop = sorted(both_ids & (SUPPRESSED_ON_DUAL - {267, 275}))
    expect("preview.Both-Fin.coop_suppressed", not leaked_coop, f"leaked={leaked_coop}")
    expect("preview.Both-Fin.has_buyer_utility_and_gift", {140, 150, 250, 370, 500} <= both_ids, str(sorted(both_ids)))
    expect(
        "preview.Both-Fin.has_sell_inspection_agent_rows",
        {245, 257} <= both_ids,
        "Dual must keep seller Inspection Response Reminder 245 and Inspection Negotiated 257 (Q1). "
        f"got_inspection={sorted(both_ids & {240, 245, 250, 257})}",
    )
    expect("preview.Both-Fin.no_both_only_extras", not (both_ids & {95, 115, 135, 155, 215, 305, 375, 505}), str(both_ids & {95, 115, 135, 155, 215, 305, 375, 505}))
    expect("preview.Both-Fin.one_title_family", len({70, 80} & both_ids) <= 1, str({70, 80} & both_ids))

    both_cash = previews.get("Both-Cash") or {}
    bothc_ids = ids_from_preview(both_cash, by_tid)
    expect("preview.Both-Cash.no_coop_appraisal", not ({267, 275} & bothc_ids), str({267, 275} & bothc_ids))
    expect("preview.Both-Cash.has_buyer_appraisal", {265, 271} <= bothc_ids, str(bothc_ids & {265, 271, 267, 275}))

    status, both_hoa = preview(
        token,
        use_case="Both-Fin",
        financing_type="Financed",
        representation_type="Both",
        has_hoa=True,
        hoa_doc_days=10,
        address="1 Dual Hoa Ln",
    )
    if status == 200:
        hoa_ids = ids_from_preview(both_hoa, by_tid)
        expect("preview.Both-Fin.hoa.request_seller", 100 in hoa_ids, str(hoa_ids & {90, 95, 100}))
        expect("preview.Both-Fin.hoa.deliver_buyer", 110 in hoa_ids, str(hoa_ids & {110, 115, 120}))
        expect("preview.Both-Fin.hoa.no_coop_rows", not ({90, 120} & hoa_ids), str({90, 120} & hoa_ids))
        expect("preview.Both-Fin.hoa.no_consolidated_extras", not ({95, 115} & hoa_ids), str({95, 115} & hoa_ids))

    # 70 vs 80: us vs other_party
    status, us_title = preview(token, use_case="Buy-Fin", title_ordered_by="us", address="1 Title Us Ln")
    status2, them_title = preview(token, use_case="Buy-Fin", title_ordered_by="other_party", address="1 Title Them Ln")
    if status == 200 and status2 == 200:
        us_ids = ids_from_preview(us_title, by_tid)
        them_ids = ids_from_preview(them_title, by_tid)
        expect("preview.title.us_gets_70_not_80", 70 in us_ids and 80 not in us_ids, str({70, 80} & us_ids))
        expect("preview.title.other_gets_80_not_70", 80 in them_ids and 70 not in them_ids, str({70, 80} & them_ids))
        t80p = task_by_id(them_title, 80, by_tid)
        expect("preview.title.80_courtesy_copy", bool(t80p and "courtesy" in ((t80p.get("description") or "").lower())), (t80p or {}).get("description"))

    status, hw_us = preview(token, use_case="Sell-Fin", has_home_warranty=True, warranty_ordered_by="us", address="1 HW Us Ln")
    status2, hw_them = preview(token, use_case="Sell-Fin", has_home_warranty=True, warranty_ordered_by="other_party", address="1 HW Them Ln")
    if status == 200 and status2 == 200:
        expect("preview.hw.us_gets_170", 170 in ids_from_preview(hw_us, by_tid), "")
        expect("preview.hw.other_gets_180", 180 in ids_from_preview(hw_them, by_tid) and 170 not in ids_from_preview(hw_them, by_tid), str(ids_from_preview(hw_them, by_tid) & {170, 180}))
        t170p = task_by_id(hw_us, 170, by_tid)
        expect("preview.hw.170_to_agent", (t170p or {}).get("target") == "Agent", json.dumps({k: (t170p or {}).get(k) for k in ("name", "target")}))

    # Autopilot grant should NOT have expanded yet (step 2 not shipped)
    auto_send_ok = {10, 20, 30, 60, 70, 80, 50, 240, 245}
    not_yet = {100, 110, 140, 150, 160, 200, 210, 220, 260, 270, 280, 290, 320, 330, 340, 420, 430, 440, 450, 460, 470}
    unexpected_auto = []
    for lid in sorted(not_yet):
        t = a_map.get(lid)
        if not t:
            continue
        level = (t.get("automation_level") or "")
        if level in ("Autopilot", "FullyAutomated", "AutoSend"):
            unexpected_auto.append((lid, level, t.get("name")))
    expect("scope.no_autopilot_expansion_yet", not unexpected_auto, str(unexpected_auto))

    for lid in auto_send_ok:
        t = a_map.get(lid)
        if t:
            log(f"scope.named_letter.{lid}", "PASS", f"{t.get('name')} level={t.get('automation_level')}")

    fails = [f for f in findings if f[1] == "FAIL"]
    passes = [f for f in findings if f[1] == "PASS"]
    print(f"\nSUMMARY {len(passes)} pass / {len(fails)} fail / {len(findings)} total")
    if OUT:
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, "staging_library_probe.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"findings": findings, "previews": {k: v.get("summary") for k, v in previews.items()}}, fh, indent=2)
        print(f"wrote {path}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
