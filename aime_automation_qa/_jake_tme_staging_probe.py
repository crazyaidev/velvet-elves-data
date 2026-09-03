"""Read-mostly staging probe for the Jake TME wrap just deployed. No send."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.stage.velvetelves.com"
EMAIL = "crazyaidev20500519@gmail.com"
PW = "QWE!@#asd234"
OUT = Path(__file__).resolve().parent / "artifacts_jake_tme_staging"
OUT.mkdir(parents=True, exist_ok=True)


def req(method, path, token=None, form=None, data=None, timeout=60):
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
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = ""
        try:
            raw = e.read().decode()[:4000]
        except Exception:
            raw = str(e)
        try:
            parsed = json.loads(raw) if raw else {"raw": raw}
        except json.JSONDecodeError:
            parsed = {"raw": raw[:2000]}
        return e.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}


def slim_login(body):
    if not isinstance(body, dict):
        return body
    user = body.get("user") or {}
    return {
        "status_keys": list(body.keys())[:20],
        "mfa_required": body.get("mfa_required"),
        "has_token": bool(body.get("access_token")),
        "email": user.get("email"),
        "role": user.get("role"),
        "platform": user.get("is_platform_admin"),
        "onboarding": user.get("onboarding_completed"),
    }


def main():
    dump: dict = {"api": API, "email": EMAIL}
    st, health = req("GET", "/api/health")
    dump["health"] = {"status": st, "body": health}
    print("health", st, health)

    st, login = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PW})
    dump["login"] = {"status": st, **slim_login(login if isinstance(login, dict) else {})}
    print("login", dump["login"])
    token = (login or {}).get("access_token") if isinstance(login, dict) else None
    if not token:
        dump["login_body"] = login
        (OUT / "probe.json").write_text(json.dumps(dump, indent=2), encoding="utf8")
        print("NO TOKEN")
        return

    st, me = req("GET", "/api/v1/users/me", token)
    dump["me"] = {
        "status": st,
        "email": (me or {}).get("email"),
        "role": (me or {}).get("role"),
        "full_name": (me or {}).get("full_name"),
        "platform": (me or {}).get("is_platform_admin"),
        "tenant_id": (me or {}).get("tenant_id"),
    }
    print("me", dump["me"])

    st, settings = req("GET", "/api/v1/automation/settings", token)
    dump["settings"] = {"status": st}
    if isinstance(settings, dict):
        dump["settings"].update(
            {
                k: settings.get(k)
                for k in (
                    "default_posture",
                    "obligation_autonomy",
                    "scheduler_enabled",
                    "library_send_enabled",
                    "inspection_reminder_send_enabled",
                    "aime_signature_enabled",
                )
            }
        )
    print("settings", dump["settings"])

    st, status = req("GET", "/api/v1/automation/status", token)
    dump["status"] = {"http": st}
    if isinstance(status, dict):
        dump["status"].update(
            {
                k: status.get(k)
                for k in (
                    "scheduler_healthy",
                    "last_tick_at",
                    "tenant_last_run_at",
                    "scheduler_enabled",
                )
            }
        )
    print("status", dump["status"])

    st, ny = req("GET", "/api/v1/automation/needs-you", token)
    items = (ny or {}).get("items") if isinstance(ny, dict) else None
    if items is None and isinstance(ny, list):
        items = ny
    items = items or []
    verify = []
    for it in items:
        if not isinstance(it, dict):
            continue
        title = (it.get("title") or "") + " " + (it.get("summary") or "")
        code = it.get("block_code") or ""
        if (
            code == "amendment_date_confirm"
            or "verify deadline" in title.lower()
            or "amendment date" in title.lower()
            or it.get("date_changes")
        ):
            verify.append(
                {
                    "id": it.get("id"),
                    "title": it.get("title"),
                    "action_verb": it.get("action_verb"),
                    "block_code": it.get("block_code"),
                    "recovery_verb": it.get("recovery_verb"),
                    "recovery_href": it.get("recovery_href"),
                    "date_changes": it.get("date_changes"),
                    "deal_label": it.get("deal_label"),
                    "transaction_id": it.get("transaction_id"),
                }
            )
    dump["needs_you"] = {
        "status": st,
        "count": len(items) if isinstance(items, list) else None,
        "keys": list(ny.keys())[:20] if isinstance(ny, dict) else type(ny).__name__,
        "verify_deadline": verify[:15],
        "sample": [
            {
                "title": it.get("title"),
                "kind": it.get("kind"),
                "block_code": it.get("block_code"),
                "action_verb": it.get("action_verb"),
            }
            for it in items[:12]
            if isinstance(it, dict)
        ],
    }
    print("needs_you", dump["needs_you"]["count"], "verify", len(verify))

    st, listed = req("GET", "/api/v1/transactions?page=1&page_size=20", token)
    txs = (listed or {}).get("items") or []
    dump["transactions"] = {
        "status": st,
        "total": (listed or {}).get("total"),
        "page": [
            {
                "id": t.get("id"),
                "address": t.get("address") or t.get("property_address"),
                "status": t.get("status"),
                "use_case": t.get("use_case"),
            }
            for t in txs
        ],
    }
    print("tx total", dump["transactions"]["total"], "page", len(txs))

    plans = []
    for t in txs[:8]:
        tid = t.get("id")
        st_p, plan = req("GET", f"/api/v1/transactions/{tid}/plan", token)
        auto = (plan or {}).get("automation") if isinstance(plan, dict) else {}
        tracking = (plan or {}).get("tracking_dates") or (plan or {}).get("key_dates") or []
        provenances = []
        if isinstance(tracking, list):
            for kd in tracking[:12]:
                if isinstance(kd, dict) and kd.get("provenance"):
                    provenances.append(
                        {
                            "field": kd.get("field_name") or kd.get("key") or kd.get("label"),
                            "provenance": kd.get("provenance"),
                            "value": kd.get("value") or kd.get("date"),
                        }
                    )
        header = {
            k: (plan or {}).get(k)
            for k in ("next_action", "stages", "tme_stages", "lifecycle_stages", "status")
            if isinstance(plan, dict) and k in plan
        }
        row = {
            "id": tid,
            "address": t.get("address") or t.get("property_address"),
            "http": st_p,
            "automation": {
                k: auto.get(k)
                for k in (
                    "posture",
                    "tenant_default",
                    "obligation_autonomy",
                    "obligation_source",
                    "tenant_obligation_default",
                    "needs_you",
                )
            }
            if isinstance(auto, dict)
            else auto,
            "provenances": provenances,
            "header_keys": header,
            "plan_keys": list(plan.keys())[:40] if isinstance(plan, dict) else type(plan).__name__,
        }
        # verify-deadline without a pending proposal should 400
        st_v, body_v = req(
            "POST",
            f"/api/v1/transactions/{tid}/verify-deadline",
            token,
            data={"decision": "keep"},
        )
        row["verify_deadline_keep"] = {"http": st_v, "detail": (body_v or {}).get("detail") if isinstance(body_v, dict) else str(body_v)[:300]}
        plans.append(row)
        print(
            "plan",
            (t.get("address") or "")[:40],
            row["automation"],
            "prov",
            len(provenances),
            "verify",
            st_v,
        )
        if len(plans) >= 3:
            break
    dump["plans"] = plans

    # Dual preview if the endpoint exists
    st_prev, prev = req(
        "POST",
        "/api/v1/transactions/preview-tasks",
        token,
        data={"use_case": "both_fin", "has_appraisal": True},
    )
    names = []
    if isinstance(prev, dict):
        for key in ("tasks", "items", "preview"):
            if isinstance(prev.get(key), list):
                names = [x.get("name") or x.get("title") for x in prev[key] if isinstance(x, dict)]
                break
    elif isinstance(prev, list):
        names = [x.get("name") or x.get("title") for x in prev if isinstance(x, dict)]
    dump["dual_preview"] = {
        "status": st_prev,
        "name_count": len(names),
        "deliver_title": [n for n in names if n and "title" in n.lower() and "deliver" in n.lower()],
        "utility": [n for n in names if n and "utility" in n.lower()],
        "sample": names[:30],
        "raw_keys": list(prev.keys())[:20] if isinstance(prev, dict) else type(prev).__name__,
    }
    print("dual_preview", dump["dual_preview"]["status"], dump["dual_preview"]["deliver_title"], dump["dual_preview"]["utility"])

    (OUT / "probe.json").write_text(json.dumps(dump, indent=2), encoding="utf8")
    print("wrote", OUT / "probe.json")


if __name__ == "__main__":
    main()
