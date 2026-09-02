"""Hit email-plans on shyna's Fix files. No send."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.stage.velvetelves.com"
EMAIL = "shyna.elene@minafter.com"
PASSWORD = os.environ.get("QA_PASSWORD", "QWE!@#asd234")
DEALS = os.path.join(os.path.dirname(__file__), "artifacts_feature14_32_staging_deploy", "deals.json")
OUT = os.path.join(os.path.dirname(__file__), "artifacts_feature14_32_staging_deploy", "plans.json")


def req(method, path, token=None, form=None):
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
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


def log(id_, result, details=""):
    print(f"[{result}] {id_}{' — ' + details[:700] if details else ''}")
    return {"id": id_, "result": result, "details": details[:4000]}


def main():
    findings = []
    st, login = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PASSWORD})
    token = login["access_token"]
    with open(DEALS, encoding="utf8") as fh:
        deals = {d["address"]: d for d in json.load(fh)["deals"]}

    def special(addr, name):
        for t in (deals[addr].get("special") or []):
            if t["name"] == name:
                return t
        return None

    def plan_of(addr, name):
        t = special(addr, name)
        if not t:
            return None, None
        st, body = req("GET", f"/api/v1/tasks/{t['id']}/email-plan", token)
        return t, body if st == 200 else {"_status": st, "_body": body}

    # Dual row counts
    for addr, expect_title, expect_util, expect_305_target in (
        ("700 Dual Fix 20260901fix", 2, True, False),
        ("701 Dual After 20260901fix", 1, False, True),
    ):
        names = deals[addr]["task_names"]
        n_title = names.count("Deliver Title")
        has_util = "Deliver Utility Info" in names
        target_305 = any(
            t.get("name") == "Deliver Title" and t.get("target") == "Buyer & Seller"
            for t in deals[addr].get("special") or []
        )
        findings.append(log(
            f"dual.{addr}.title_count",
            "INFO",
            json.dumps({"n_title": n_title, "has_util": has_util, "target_305": target_305}),
        ))
        # Audri: Dual should have 300+310 (two Deliver Title) and 150 (buyer utility), no 305
        findings.append(log(
            f"audri.{addr}.two_deliver_title",
            "PASS" if n_title == 2 and not target_305 else "FAIL",
            f"n_title={n_title} target_305={target_305}",
        ))
        findings.append(log(
            f"audri.{addr}.buyer_utility",
            "PASS" if has_util else "FAIL",
            f"has_util={has_util} (150 should populate on Dual)",
        ))

    # F15 maple welcome without include_ai
    maple_id = deals["200 Maple Fix 20260901fix"]["id"]
    st, tasks = req("GET", f"/api/v1/tasks/transaction/{maple_id}", token)
    names = [t.get("name") for t in tasks] if isinstance(tasks, list) else []
    findings.append(log(
        "f15.maple.welcome_without_include_ai",
        "PASS" if "Buyer Welcome" in names else "FAIL",
        json.dumps({"status": st, "n": len(names), "welcome": "Buyer Welcome" in names}),
    ))

    # F14 Elm cash appraisal
    t, body = plan_of("500 Elm Fix 20260901fix", "Appraisal Ordered")
    text = f"{body.get('subject') or ''}\n{body.get('body') or ''}"
    findings.append(log(
        "f14.elm.question",
        "PASS" if "Has the appraisal been ordered" in text and "Email the buyer and ask" not in text else "FAIL",
        text[:500],
    ))
    tos = [r.get("email") for r in (body.get("recipients") or [])]
    findings.append(log("f14.elm.to", "PASS" if tos else "WARN", json.dumps({"to": tos, "can_send": body.get("can_send")})))

    # F18 no contract
    t, body = plan_of("410 NoContract Fix 20260901fix", "Order Title")
    findings.append(log(
        "f18.order_title.blocked",
        "PASS" if not body.get("can_send") and "purchase agreement" in (body.get("blocked_reason") or "").lower() else "FAIL",
        json.dumps({"can_send": body.get("can_send"), "blocked": body.get("blocked_reason"), "head": (body.get("body") or "")[:160]}),
    ))
    t, body = plan_of("410 NoContract Fix 20260901fix", "Loan Officer Welcome")
    findings.append(log(
        "f18.lo_welcome.blocked",
        "PASS" if not body.get("can_send") and "purchase agreement" in (body.get("blocked_reason") or "").lower() else "FAIL",
        json.dumps({"can_send": body.get("can_send"), "blocked": body.get("blocked_reason")}),
    ))

    # F19 inspection date
    t, body = plan_of("200 Maple Fix 20260901fix", "Inspection Response Reminder")
    text = body.get("body") or ""
    findings.append(log(
        "f19.inspection_not_tbd",
        "PASS" if "TBD" not in text and text else "FAIL",
        text[:400],
    ))

    # F29 courtesy
    t, body = plan_of("720 Confirm Fix 20260901fix", "Confirm Title Order")
    text = (body.get("body") or "").lower()
    findings.append(log(
        "f29.courtesy",
        "PASS" if "as a courtesy to" in text and "titleother rep" not in text.split("as a courtesy to")[-1][:80] else "FAIL",
        (body.get("body") or "")[:500],
    ))

    # F30 listing utility
    t, body = plan_of("800 Utility Fix 20260901fix", "Deliver Utility Info")
    legs = body.get("legs") or []
    reason = (body.get("blocked_reason") or "").lower()
    findings.append(log(
        "f30.listing_one_letter",
        "PASS" if body.get("can_send") and len(legs) == 1 and "buyer" not in reason else "FAIL",
        json.dumps({
            "can_send": body.get("can_send"),
            "blocked": body.get("blocked_reason"),
            "n_legs": len(legs),
            "legs": [{"key": x.get("key"), "to": [r.get("email") for r in (x.get("recipients") or [])]} for x in legs],
            "summary": body.get("summary"),
        }),
    ))

    # F22 cedar needs you
    cedar_id = deals["400 Cedar Fix 20260901fix"]["id"]
    st, ny = req("GET", "/api/v1/automation/needs-you", token)
    items = (ny or {}).get("items") or []
    cedar = [it for it in items if it.get("transaction_id") == cedar_id]
    findings.append(log(
        "f22.cedar.recovery",
        "PASS" if any(it.get("recovery_verb") in {"Add contact", "Upload document"} for it in cedar) else "FAIL",
        json.dumps([
            {"title": it.get("title"), "code": it.get("block_code"), "verb": it.get("recovery_verb"), "href": it.get("recovery_href")}
            for it in cedar[:10]
        ]),
    ))

    with open(OUT, "w", encoding="utf8") as fh:
        json.dump({"findings": findings}, fh, indent=2)
    fails = [f for f in findings if f["result"] == "FAIL"]
    print(f"\nSUMMARY {len(findings)-len(fails)} ok / {len(fails)} fail")


if __name__ == "__main__":
    main()
