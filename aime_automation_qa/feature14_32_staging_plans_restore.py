"""Email-plan checks on Jan's staging test files, then restore Audri Q1 Dual."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

API = "https://api.stage.velvetelves.com"
EMAIL = "crazyaidev20500519@gmail.com"
PW = "QWE!@#asd234"
OUT = Path(__file__).resolve().parent / "artifacts_feature14_32_staging_deploy"
OUT.mkdir(parents=True, exist_ok=True)

FILES = {
    "elm": "3f469ceb-d5d1-490a-8808-c6abd3a8bc46",
    "maple": "9507baaf-ad8b-41ce-912c-6d637fbb9138",
    "cedar": "002b791f-ef34-4b8c-ad45-37479d447019",
    "nocontract": "36507487-da17-4c37-a458-3d6faad3863c",
    "dual": "f53d0674-8322-4568-9fb9-fae7715d521d",
    "confirm": "ff800067-b769-4964-82a3-3855ea94a565",
    "utility": "10e00794-5689-45d0-9c3f-8a165eff85d4",
    "pine": "a2c9c989-d9dc-4102-871c-1ce7d3142c4d",
}


def req(method, path, token=None, data=None, form=None):
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(API + path, data=body, headers=headers, method=method)
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


findings = []


def log(id_, result, details=""):
    findings.append({"id": id_, "result": result, "details": str(details)[:4000]})
    extra = (" — " + str(details)[:700]) if details else ""
    print(f"[{result}] {id_}{extra}")


def tasks_of(token, tx_id, include_ai=True):
    q = "?include_ai=true" if include_ai else ""
    status, body = req("GET", f"/api/v1/tasks/transaction/{tx_id}{q}", token)
    return status, body if isinstance(body, list) else []


def named(tasks, name):
    return [t for t in tasks if t.get("name") == name]


def plan(token, task_id):
    return req("GET", f"/api/v1/tasks/{task_id}/email-plan", token)


def preview(token, **kwargs):
    today = date.today()
    payload = {
        "address": "903 Dual After Restore Ave",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "use_case": "Both-Fin",
        "financing_type": "Financed",
        "representation_type": "Both",
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
        "title_ordered_by": "us",
        "warranty_ordered_by": "us",
        "closing_mode": "title_escrow",
        "is_owner_occupied": True,
    }
    payload.update(kwargs)
    return req("POST", "/api/v1/transactions/preview-tasks", token, data=payload)


def fetch_templates(token, active):
    items = []
    page = 1
    flag = "true" if active else "false"
    while True:
        status, body = req(
            "GET",
            f"/api/v1/task-templates?is_active={flag}&page={page}&page_size=200",
            token,
        )
        if status != 200:
            return items
        items.extend(body.get("items") or [])
        if page >= (body.get("pages") or 1):
            break
        page += 1
    return items


def by_legacy(items):
    out = {}
    for t in items:
        lid = t.get("legacy_task_id")
        if lid is not None:
            out[int(lid)] = t
    return out


def main():
    status, login = req(
        "POST", "/api/v1/users/login", form={"username": EMAIL, "password": PW}
    )
    token = login.get("access_token")
    if status != 200 or not token:
        log("login", "FAIL", f"{status} {login}")
        return 1
    log("login", "PASS", EMAIL)

    # ── existing-file checks ────────────────────────────────────────────
    st, elm = tasks_of(token, FILES["elm"])
    for name, must, must_not in (
        ("Appraisal Ordered", "Has the appraisal been ordered", "Email the buyer and ask"),
        ("Appraisal Completed", "Has the appraisal been completed", "Email the buyer and ask"),
    ):
        rows = named(elm, name)
        if not rows:
            log(f"f14.elm.{name}", "FAIL", "task missing")
            continue
        pst, body = plan(token, rows[0]["id"])
        text = f"{body.get('subject') or ''}\n{body.get('body') or ''}"
        ok = (
            pst == 200
            and must.lower() in text.lower()
            and must_not.lower() not in text.lower()
        )
        log(f"f14.elm.{name}.question", "PASS" if ok else "FAIL", text[:500])

    st, maple_open = tasks_of(token, FILES["maple"], include_ai=False)
    names_open = [t.get("name") for t in maple_open]
    log(
        "f15.maple.welcome_without_include_ai",
        "PASS" if "Buyer Welcome" in names_open else "FAIL",
        json.dumps({"n": len(names_open), "welcome": "Buyer Welcome" in names_open}),
    )
    st, maple_plan = req("GET", f"/api/v1/transactions/{FILES['maple']}/plan", token)
    posture = ((maple_plan or {}).get("automation") or {}).get("posture")
    log("f15.maple.posture", "INFO", str(posture))

    st, cedar_plan = req("GET", f"/api/v1/transactions/{FILES['cedar']}/plan", token)
    cedar_posture = ((cedar_plan or {}).get("automation") or {}).get("posture")
    log("f16.cedar.posture", "INFO", str(cedar_posture))
    st, cedar_open = tasks_of(token, FILES["cedar"], include_ai=False)
    cedar_names = [t.get("name") for t in cedar_open]
    if (cedar_posture or "").lower() == "autopilot":
        log(
            "f16.cedar.welcome_hidden_without_include_ai",
            "PASS" if "Buyer Welcome" not in cedar_names else "FAIL",
            json.dumps({"n": len(cedar_names), "welcome": "Buyer Welcome" in cedar_names}),
        )
    else:
        log("f16.cedar.not_autopilot", "WARN", str(cedar_posture))

    st, nc = tasks_of(token, FILES["nocontract"])
    for name in ("Order Title", "Loan Officer Welcome"):
        rows = named(nc, name)
        if not rows:
            log(f"f18.{name}", "FAIL", "task missing")
            continue
        pst, body = plan(token, rows[0]["id"])
        blocked = (not body.get("can_send")) and "purchase agreement" in (
            body.get("blocked_reason") or ""
        ).lower()
        log(
            f"f18.{name}.blocked",
            "PASS" if blocked else "FAIL",
            json.dumps(
                {
                    "can_send": body.get("can_send"),
                    "blocked": body.get("blocked_reason"),
                    "head": (body.get("body") or "")[:180],
                }
            ),
        )

    st, maple = tasks_of(token, FILES["maple"])
    rows = named(maple, "Inspection Response Reminder")
    if not rows:
        st, pine = tasks_of(token, FILES["pine"])
        rows = named(pine, "Inspection Response Reminder")
        src = "pine"
    else:
        src = "maple"
    if not rows:
        log("f19.inspection", "FAIL", "task missing")
    else:
        pst, body = plan(token, rows[0]["id"])
        text = body.get("body") or ""
        log(
            f"f19.{src}.inspection_not_tbd",
            "PASS" if "TBD" not in text and text else "FAIL",
            text[:400],
        )

    st, ny = req("GET", "/api/v1/automation/needs-you", token)
    items = (ny or {}).get("items") or []
    cedar = [it for it in items if it.get("transaction_id") == FILES["cedar"]]
    log(
        "f22.cedar.recovery",
        "PASS"
        if any(it.get("recovery_verb") in {"Add contact", "Upload document"} for it in cedar)
        else "FAIL",
        json.dumps(
            [
                {
                    "title": it.get("title"),
                    "code": it.get("block_code"),
                    "verb": it.get("recovery_verb"),
                    "href": it.get("recovery_href"),
                }
                for it in cedar[:12]
            ]
        ),
    )

    st, dual = tasks_of(token, FILES["dual"])
    titles = named(dual, "Deliver Title")
    utils = named(dual, "Deliver Utility Info")
    log(
        "f28.existing_dual.two_per_side_title",
        "PASS"
        if len(titles) == 2
        and {t.get("target") for t in titles} == {"Buyer", "Seller"}
        else "FAIL",
        json.dumps([{"target": t.get("target"), "id": t.get("id")} for t in titles]),
    )
    log(
        "f28.existing_dual.buyer_utility",
        "PASS" if any(t.get("target") == "Buyer" for t in utils) else "FAIL",
        json.dumps([{"target": t.get("target")} for t in utils]),
    )

    st, conf = tasks_of(token, FILES["confirm"])
    rows = named(conf, "Confirm Title Order")
    if not rows:
        log("f29.confirm", "FAIL", "task missing")
    else:
        pst, body = plan(token, rows[0]["id"])
        text = (body.get("body") or "").lower()
        # Courtesy should use the co-op's full name, not the title rep.
        log(
            "f29.courtesy",
            "PASS" if "as a courtesy to" in text else "WARN",
            (body.get("body") or "")[:600],
        )

    st, util = tasks_of(token, FILES["utility"])
    rows = named(util, "Deliver Utility Info")
    if not rows:
        log("f30.utility", "FAIL", "task missing")
    else:
        pst, body = plan(token, rows[0]["id"])
        legs = body.get("legs") or []
        reason = (body.get("blocked_reason") or "").lower()
        one_leg = len(legs) == 1 and (legs[0].get("key") == "delivery")
        no_buyer_block = "buyer" not in reason
        log(
            "f30.listing_one_letter",
            "PASS" if body.get("can_send") and one_leg and no_buyer_block else "FAIL",
            json.dumps(
                {
                    "can_send": body.get("can_send"),
                    "blocked": body.get("blocked_reason"),
                    "n_legs": len(legs),
                    "legs": [
                        {
                            "key": x.get("key"),
                            "to": [r.get("email") for r in (x.get("recipients") or [])],
                        }
                        for x in legs
                    ],
                    "summary": body.get("summary"),
                }
            ),
        )

    # ── restore Dual library (Audri Q1) ────────────────────────────────
    active = by_legacy(fetch_templates(token, True))
    inactive = by_legacy(fetch_templates(token, False))
    t305 = active.get(305) or inactive.get(305)
    t300 = active.get(300)
    t310 = active.get(310)
    t150 = active.get(150)
    t160 = active.get(160)
    if not all([t305, t300, t310, t150, t160]):
        log("restore.templates_found", "FAIL", json.dumps({
            "305": bool(t305), "300": bool(t300), "310": bool(t310),
            "150": bool(t150), "160": bool(t160),
        }))
    else:
        patches = [
            (305, t305["id"], {"is_active": False, "dual_agency_behavior": "consolidated"}),
            (300, t300["id"], {"dual_agency_behavior": "standard"}),
            (310, t310["id"], {"dual_agency_behavior": "standard"}),
            (150, t150["id"], {"dual_agency_behavior": "standard"}),
            (160, t160["id"], {"dual_agency_behavior": "suppressed"}),
        ]
        for lid, tid, patch in patches:
            st, body = req("PUT", f"/api/v1/task-templates/{tid}", token, data=patch)
            ok = st == 200 and body.get("dual_agency_behavior") == patch["dual_agency_behavior"]
            if "is_active" in patch:
                ok = ok and body.get("is_active") is False
            log(
                f"restore.{lid}",
                "PASS" if ok else "FAIL",
                json.dumps(
                    {
                        "status": st,
                        "active": body.get("is_active"),
                        "dual": body.get("dual_agency_behavior"),
                        "err": body if st != 200 else None,
                    },
                    default=str,
                )[:800],
            )

    st, both = preview(token)
    titles = []
    utils = []
    welcomes = []
    for t in both.get("tasks") or []:
        rec = {"name": t.get("name"), "target": t.get("target")}
        if t.get("name") == "Deliver Title":
            titles.append(rec)
        if t.get("name") == "Deliver Utility Info":
            utils.append(rec)
        if "Welcome" in (t.get("name") or ""):
            welcomes.append(rec)
    coop_welcome = [w for w in welcomes if "co-op" in (w.get("name") or "").lower()]
    log(
        "preview.after.deliver_title_buyer_and_seller",
        "PASS"
        if {t.get("target") for t in titles} == {"Buyer", "Seller"} and len(titles) == 2
        else "FAIL",
        json.dumps(titles),
    )
    log(
        "preview.after.no_305_buyer_seller_combo",
        "PASS" if not any(t.get("target") == "Buyer & Seller" for t in titles) else "FAIL",
        json.dumps(titles),
    )
    log(
        "preview.after.has_150_no_160",
        "PASS"
        if any(u.get("target") == "Buyer" for u in utils)
        and not any(u.get("target") == "Co-op Agent" for u in utils)
        else "FAIL",
        json.dumps(utils),
    )
    log(
        "preview.after.no_coop_welcome",
        "PASS" if not coop_welcome else "FAIL",
        json.dumps(welcomes),
    )

    path = OUT / "plans_and_restore.json"
    path.write_text(json.dumps({"findings": findings}, indent=2), encoding="utf8")
    fails = [f for f in findings if f["result"] == "FAIL"]
    print(f"\nSUMMARY {len(findings) - len(fails)} ok / {len(fails)} fail / {len(findings)} total")
    print("wrote", path)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
