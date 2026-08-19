"""Live probe of Yareny's FSBO portal APIs (local)."""
from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "http://127.0.0.1:8000"
FSBO_EMAIL = "yareny.evaly@minafter.com"
AGENT_EMAIL = "keison.londyn@minafter.com"
ADMIN_EMAIL = "shyna.elene@minafter.com"
PASSWORD = "QWE!@#asd234"


def req(method: str, path: str, token: str | None = None, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = Request(API + path, data=data, headers=headers, method=method)
    try:
        with urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else raw
        except Exception:
            parsed = raw
        return e.code, parsed


def login(email: str) -> str:
    data = urlencode({"username": email, "password": PASSWORD}).encode()
    r = Request(
        API + "/api/v1/users/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(r, timeout=30) as resp:
            body = json.loads(resp.read().decode())
    except HTTPError as e:
        raise SystemExit(f"login failed {email}: {e.code} {e.read().decode()}")
    return body["access_token"]


def slim(obj, limit=1800):
    return json.dumps(obj, default=str)[:limit]


def main():
    try:
        tok = login(FSBO_EMAIL)
        print("fsbo login ok")
    except SystemExit as e:
        print(e)
        return

    status, me = req("GET", "/api/v1/users/me", token=tok)
    print("me", status, slim({
        "id": (me or {}).get("id") if isinstance(me, dict) else me,
        "email": (me or {}).get("email") if isinstance(me, dict) else None,
        "role": (me or {}).get("role") if isinstance(me, dict) else None,
        "is_active": (me or {}).get("is_active") if isinstance(me, dict) else None,
        "onboarding_completed": (me or {}).get("onboarding_completed") if isinstance(me, dict) else None,
        "tenant_id": (me or {}).get("tenant_id") if isinstance(me, dict) else None,
        "full_name": (me or {}).get("full_name") if isinstance(me, dict) else None,
    }))

    for path in [
        "/api/v1/dashboard/fsbo/overview",
        "/api/v1/dashboard/fsbo/documents",
        "/api/v1/dashboard/fsbo/milestones",
        "/api/v1/dashboard/fsbo/notifications",
        "/api/v1/notifications/pending",
        "/api/v1/dashboard/fsbo/share-link",
        "/api/v1/client/invoices",
        "/api/v1/client/notifications",
        "/api/v1/documents?page_size=20",
    ]:
        status, body = req("GET", path, token=tok)
        if isinstance(body, dict) and "properties" in body:
            props = body.get("properties") or []
            summary = {
                "status": status,
                "n_properties": len(props),
                "addresses": [
                    p.get("address") or p.get("transaction_id") for p in props[:8]
                ],
                "ids": [p.get("transaction_id") or p.get("id") for p in props[:8]],
                "missing_documents_count": body.get("missing_documents_count"),
                "share_links_live": body.get("share_links_live"),
                "days_to_close_nearest": body.get("days_to_close_nearest"),
                "next_steps": [
                    {"title": s.get("title"), "kind": s.get("action_kind"), "tx": s.get("transaction_id")}
                    for s in (body.get("critical_next_steps") or [])[:4]
                ],
                "totals": body.get("totals"),
                "messages": len(body.get("messages") or []),
                "closing_timeline": body.get("closing_timeline"),
                "support": body.get("support_contact"),
            }
        elif isinstance(body, dict) and "items" in body:
            items = body.get("items") or []
            summary = {
                "status": status,
                "count": len(items) if isinstance(items, list) else items,
                "unread": body.get("unread_count"),
                "sample": items[:4] if isinstance(items, list) else items,
            }
        elif isinstance(body, list):
            summary = {"status": status, "count": len(body), "sample": body[:4]}
        else:
            summary = {"status": status, "body": body}
        print(path, slim(summary))

    # If we have a property, fetch detail
    status, overview = req("GET", "/api/v1/dashboard/fsbo/overview", token=tok)
    props = (overview or {}).get("properties") or [] if isinstance(overview, dict) else []
    if props:
        tid = props[0].get("transaction_id")
        status, detail = req("GET", f"/api/v1/dashboard/fsbo/properties/{tid}", token=tok)
        print("property detail", status, slim({
            "address": (detail or {}).get("address") if isinstance(detail, dict) else detail,
            "fsbo_state": (detail or {}).get("fsbo_state") if isinstance(detail, dict) else None,
            "closing_date": (detail or {}).get("closing_date") if isinstance(detail, dict) else None,
            "docs": len((detail or {}).get("documents") or []) if isinstance(detail, dict) else None,
            "board": (detail or {}).get("document_board", {}).get("counts") if isinstance(detail, dict) else None,
            "milestones": len((detail or {}).get("milestones") or []) if isinstance(detail, dict) else None,
            "contacts": [
                {"role": c.get("role"), "name": c.get("name")}
                for c in ((detail or {}).get("contacts") or [])[:6]
            ] if isinstance(detail, dict) else None,
            "share_links": len((detail or {}).get("share_links") or []) if isinstance(detail, dict) else None,
            "messages": len((detail or {}).get("messages") or []) if isinstance(detail, dict) else None,
            "guidance": (detail or {}).get("ai_guidance") if isinstance(detail, dict) else None,
        }))
    else:
        print("NO PROPERTIES — agent/admin seed needed")
        try:
            agent_tok = login(AGENT_EMAIL)
            print("agent login ok")
            status, txs = req("GET", "/api/v1/transactions?page_size=20&status=Active", token=agent_tok)
            items = (txs or {}).get("items") or (txs or {}).get("transactions") or []
            print("agent txs", status, slim([
                {
                    "id": t.get("id"),
                    "address": t.get("address"),
                    "is_fsbo": t.get("is_fsbo"),
                    "fsbo_state": t.get("fsbo_state"),
                    "status": t.get("status"),
                }
                for t in (items[:12] if isinstance(items, list) else [])
            ]))
        except SystemExit as e:
            print("agent login failed", e)


if __name__ == "__main__":
    main()
