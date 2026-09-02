"""Live staging probe for the Feature 14-32 deploy. Does not create deals or send mail."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

API = os.environ.get("QA_API", "https://api.stage.velvetelves.com").rstrip("/")
EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD", "QWE!@#asd234")
SEED = os.path.join(os.path.dirname(__file__), "artifacts_feature14_32", "seed.json")
OUT = os.path.join(os.path.dirname(__file__), "artifacts_feature14_32_staging_deploy")
os.makedirs(OUT, exist_ok=True)

findings: list[dict] = []


def log(id_: str, result: str, details: str = "") -> None:
    findings.append({"id": id_, "result": result, "details": details[:4000]})
    extra = f" — {details[:500]}" if details else ""
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


def fetch_templates(token: str, active: bool) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        status, body = req(
            "GET",
            f"/api/v1/task-templates?is_active={'true' if active else 'false'}&page={page}&page_size=200",
            token,
        )
        if status != 200:
            log("templates.fetch", "FAIL", f"active={active} status={status} {body}")
            return items
        batch = body.get("items") or []
        items.extend(batch)
        if page >= (body.get("pages") or 1):
            break
        page += 1
    return items


def by_legacy(items: list[dict]) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for t in items:
        lid = t.get("legacy_task_id")
        if lid is not None:
            out[int(lid)] = t
    return out


def preview(token: str, **kwargs):
    today = date.today()
    payload = {
        "address": kwargs.pop("address", "901 Staging Probe Ln"),
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
        "has_appraisal": True,
        "title_ordered_by": kwargs.pop("title_ordered_by", "us"),
        "warranty_ordered_by": "us",
        "closing_mode": "title_escrow",
        "is_owner_occupied": True,
    }
    payload.update(kwargs)
    return req("POST", "/api/v1/transactions/preview-tasks", token, data=payload)


def ids_from_preview(body: dict, by_tid: dict) -> list[int]:
    out = []
    for t in body.get("tasks") or []:
        lid = t.get("legacy_task_id")
        if lid is None:
            tmpl = by_tid.get(t.get("template_id") or "")
            lid = (tmpl or {}).get("legacy_task_id")
        if lid is not None:
            out.append(int(lid))
    return out


def names_for(body: dict, needle: str) -> list[dict]:
    return [
        {"name": t.get("name"), "target": t.get("target"), "legacy_task_id": t.get("legacy_task_id")}
        for t in (body.get("tasks") or [])
        if needle.lower() in (t.get("name") or "").lower()
    ]


def main() -> int:
    with open(SEED, encoding="utf8") as fh:
        seed = json.load(fh)
    files = seed["files"]

    status, health = req("GET", "/api/health")
    log("api.health", "PASS" if status == 200 else "FAIL", f"{status} {health}")

    status, login = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PASSWORD})
    if status != 200 or not login.get("access_token"):
        log("login", "FAIL", f"{status} {login}")
        return 1
    token = login["access_token"]
    log("login", "PASS", EMAIL)

    active = fetch_templates(token, True)
    inactive = fetch_templates(token, False)
    a_map = by_legacy(active)
    i_map = by_legacy(inactive)
    by_tid = {t["id"]: t for t in active + inactive}

    # Dual library (Audri Q1)
    t305 = a_map.get(305) or i_map.get(305) or {}
    log(
        "library.305.inactive",
        "PASS" if 305 not in a_map and 305 in i_map else "FAIL",
        json.dumps({
            "active": 305 in a_map,
            "inactive": 305 in i_map,
            "is_active": t305.get("is_active"),
            "dual": t305.get("dual_agency_behavior"),
            "target": t305.get("target"),
        }),
    )
    for lid, want in ((300, "standard"), (310, "standard"), (150, "standard"), (160, "suppressed")):
        t = a_map.get(lid) or {}
        got = t.get("dual_agency_behavior")
        log(
            f"library.{lid}.dual_{want}",
            "PASS" if got == want else "FAIL",
            json.dumps({"dual": got, "target": t.get("target"), "is_active": lid in a_map}),
        )

    t265 = a_map.get(265) or {}
    log(
        "library.265.question_copy",
        "PASS" if "ask the buyer whether" in (t265.get("description") or "").lower() else "WARN",
        (t265.get("description") or "")[:240],
    )

    status, both = preview(
        token,
        use_case="Both-Fin",
        financing_type="Financed",
        representation_type="Both",
        address="902 Dual Probe Ave",
    )
    log("preview.Both-Fin.ok", "PASS" if status == 200 else "FAIL", str(status))
    both_ids = set(ids_from_preview(both, by_tid)) if status == 200 else set()
    titles = names_for(both, "Deliver Title")
    utils = names_for(both, "Deliver Utility")
    welcomes = names_for(both, "Welcome")
    log("preview.Both-Fin.no_305", "PASS" if 305 not in both_ids else "FAIL", str(sorted(both_ids & {300, 305, 310})))
    log(
        "preview.Both-Fin.deliver_title_300_and_310",
        "PASS" if {300, 310} <= both_ids else "FAIL",
        json.dumps(titles),
    )
    log("preview.Both-Fin.no_160", "PASS" if 160 not in both_ids else "FAIL", json.dumps(utils))
    log(
        "preview.Both-Fin.has_150_buyer_utility",
        "PASS" if 150 in both_ids else "FAIL",
        json.dumps(utils),
    )
    coop_welcome = [w for w in welcomes if "co-op" in (w.get("name") or "").lower()]
    log("preview.Both-Fin.no_coop_welcome", "PASS" if not coop_welcome else "FAIL", json.dumps(welcomes))

    def plan(task_id: str):
        return req("GET", f"/api/v1/tasks/{task_id}/email-plan", token)

    # F14 cash appraisal copy on existing files
    for key, plan_name, must, must_not in (
        ("buyCash", "Appraisal Ordered", "Has the appraisal been ordered", "Email the buyer and ask"),
        ("buyCash", "Appraisal Completed", "Has the appraisal been completed", "Email the buyer and ask"),
        ("sellCash", "Appraisal Ordered", "Has the buyer's appraisal been ordered", "Email the co-op"),
    ):
        task_id = (((files.get(key) or {}).get("plans") or {}).get(plan_name) or {}).get("task_id")
        if not task_id:
            log(f"f14.{key}.{plan_name}", "FAIL", "no task_id in seed")
            continue
        st, body = plan(task_id)
        text = f"{body.get('subject') or ''}\n{body.get('body') or ''}"
        ok = st == 200 and must.lower() in text.lower() and must_not.lower() not in text.lower()
        log(f"f14.{key}.{plan_name}.question", "PASS" if ok else "FAIL", text[:500])
        to = [r.get("email") for r in (body.get("recipients") or [])]
        log(f"f14.{key}.{plan_name}.can_send", "PASS" if body.get("can_send") else "WARN", json.dumps({"to": to, "blocked": body.get("blocked_reason")}))

    # F18 no-contract send gate
    nc = ((files.get("noContract") or {}).get("plans") or {})
    for name in ("Order Title", "Loan Officer Welcome"):
        task_id = (nc.get(name) or {}).get("task_id")
        if not task_id:
            log(f"f18.{name}", "FAIL", "no task_id")
            continue
        st, body = plan(task_id)
        blocked = not body.get("can_send") and "purchase agreement" in (body.get("blocked_reason") or "").lower()
        log(f"f18.{name}.blocked", "PASS" if blocked else "FAIL", json.dumps({
            "status": st,
            "can_send": body.get("can_send"),
            "blocked_reason": body.get("blocked_reason"),
            "body_head": (body.get("body") or "")[:180],
        }))

    # F19 inspection date on Pine
    insp_id = (((files.get("pine") or {}).get("plans") or {}).get("Inspection Response Reminder") or {}).get("task_id")
    if insp_id:
        st, body = plan(insp_id)
        text = body.get("body") or ""
        log(
            "f19.inspection_date_not_tbd",
            "PASS" if "TBD" not in text and st == 200 else "FAIL",
            text[:400],
        )

    # F29 courtesy name
    conf_id = (((files.get("titleOther") or {}).get("plans") or {}).get("Confirm Title Order") or {}).get("task_id")
    if conf_id:
        st, body = plan(conf_id)
        text = (body.get("body") or "").lower()
        log(
            "f29.courtesy_names_coop",
            "PASS" if "as a courtesy to titleother co-op" in text and "as a courtesy to titleother rep" not in text else "FAIL",
            (body.get("body") or "")[:500],
        )

    # F30 listing utility
    util_id = (((files.get("utility") or {}).get("plans") or {}).get("Deliver Utility Info") or {}).get("task_id")
    if util_id:
        st, body = plan(util_id)
        legs = body.get("legs") or []
        reason = (body.get("blocked_reason") or "").lower()
        one_leg = len(legs) == 1 and (legs[0].get("key") == "delivery")
        no_buyer_block = "buyer" not in reason
        to_ok = any(
            "coop" in (r.get("email") or "").lower()
            for r in ((legs[0].get("recipients") if legs else body.get("recipients")) or [])
        )
        log(
            "f30.one_letter_to_coop",
            "PASS" if body.get("can_send") and one_leg and no_buyer_block and to_ok else "FAIL",
            json.dumps({
                "can_send": body.get("can_send"),
                "blocked": body.get("blocked_reason"),
                "n_legs": len(legs),
                "legs": [{"key": x.get("key"), "to": [r.get("email") for r in (x.get("recipients") or [])]} for x in legs],
                "summary": body.get("summary"),
            }),
        )

    # F15 maple tasks include_ai plus posture: Buyer Welcome should be listed without include_ai on manual
    maple_id = (files.get("maple") or {}).get("id")
    if maple_id:
        st, tasks = req("GET", f"/api/v1/tasks/transaction/{maple_id}", token)
        names = [t.get("name") for t in (tasks or [])] if isinstance(tasks, list) else []
        log(
            "f15.maple.welcome_visible_without_include_ai",
            "PASS" if "Buyer Welcome" in names else "FAIL",
            json.dumps({"status": st, "n": len(names), "has_welcome": "Buyer Welcome" in names}),
        )
        st2, tasks_ai = req("GET", f"/api/v1/tasks/transaction/{maple_id}?include_ai=true", token)
        names_ai = [t.get("name") for t in (tasks_ai or [])] if isinstance(tasks_ai, list) else []
        log("f15.maple.include_ai_also_has_welcome", "PASS" if "Buyer Welcome" in names_ai else "FAIL", str(len(names_ai)))

        st, ny = req("GET", "/api/v1/automation/needs-you", token)
        items = (ny or {}).get("items") or [] if isinstance(ny, dict) else []
        cedar_id = (files.get("cedar") or {}).get("id")
        cedar_rows = [it for it in items if it.get("transaction_id") == cedar_id]
        verbs = sorted({it.get("recovery_verb") for it in cedar_rows if it.get("recovery_verb")})
        log(
            "f22.needs_you.recovery_verbs_present",
            "PASS" if any(v in verbs for v in ("Add contact", "Upload document", "Switch this deal off Manual")) or any(it.get("recovery_href") for it in items[:20]) else "WARN",
            json.dumps({
                "cedar_n": len(cedar_rows),
                "cedar_sample": [
                    {"title": it.get("title"), "code": it.get("block_code"), "verb": it.get("recovery_verb"), "href": it.get("recovery_href")}
                    for it in cedar_rows[:8]
                ],
                "any_verb": sorted({it.get("recovery_verb") for it in items if it.get("recovery_verb")})[:12],
            }),
        )

    path = os.path.join(OUT, "findings.json")
    with open(path, "w", encoding="utf8") as fh:
        json.dump({"findings": findings}, fh, indent=2)
    fails = [f for f in findings if f["result"] == "FAIL"]
    print(f"\nSUMMARY {len(findings) - len(fails)} ok / {len(fails)} fail / {len(findings)} total")
    print("wrote", path)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
