"""Live probe of Bradyn's client portal APIs (local)."""
from __future__ import annotations

import json
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API = "http://127.0.0.1:8000"
CLIENT_EMAIL = "bradyn.dejuan@minafter.com"
AGENT_EMAIL = "keison.londyn@minafter.com"
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


def main():
    client_tok = login(CLIENT_EMAIL)
    print("client login ok")
    for path in [
        "/api/v1/users/me",
        "/api/v1/dashboard/client",
        "/api/v1/documents?page_size=50",
        "/api/v1/client/notifications",
        "/api/v1/client/invoices",
    ]:
        status, body = req("GET", path, token=client_tok)
        summary = body
        if isinstance(body, dict):
            if "home" in body:
                home = body.get("home") or {}
                summary = {
                    "status": status,
                    "tx_count": len(body.get("transactions") or []),
                    "addresses": [t.get("address") for t in (body.get("transactions") or [])],
                    "open_invoice_count": body.get("open_invoice_count"),
                    "next_action": (home.get("next_action") or {}).get("title"),
                    "cta": (home.get("next_action") or {}).get("cta_target"),
                    "attention": home.get("documents_needing_attention"),
                    "hero": (home.get("hero") or {}).get("address"),
                }
            elif "items" in body:
                items = body.get("items") or []
                summary = {
                    "status": status,
                    "count": len(items) if isinstance(items, list) else items,
                    "unread": body.get("unread_count"),
                    "sample": [
                        {k: i.get(k) for k in ("id", "kind", "doc_label", "file_name", "is_client_visible", "uploaded_by", "action") if isinstance(i, dict) and k in i}
                        for i in (items[:8] if isinstance(items, list) else [])
                    ],
                }
            else:
                summary = {"status": status, "keys": list(body.keys())[:12], "role": body.get("role"), "email": body.get("email")}
        print(path, json.dumps(summary, default=str)[:1200])

    agent_tok = login(AGENT_EMAIL)
    print("agent login ok")
    status, me = req("GET", "/api/v1/users/me", token=agent_tok)
    print("agent me", status, me.get("role") if isinstance(me, dict) else me)

    status, docs = req("GET", "/api/v1/documents?page_size=50", token=agent_tok)
    items = (docs or {}).get("items") or []
    harness = [d for d in items if str(d.get("transaction_id") or "") in (
        "f8bf6263-99cd-4ed6-8225-b9a5a951de07",
        "8045898a-4e17-4af7-aa74-ffa76fbab96f",
    )]
    print("agent docs on bradyn txs", len(harness))
    for d in harness[:8]:
        print(" ", d.get("id"), d.get("doc_label") or d.get("file_name"), d.get("transaction_id"), "visible", d.get("is_client_visible"), "kind", d.get("client_share_kind"))

    target = next((d for d in harness if not d.get("is_client_visible")), harness[0] if harness else None)
    if target:
        tid = target["transaction_id"]
        did = target["id"]
        status, shared = req(
            "POST",
            f"/api/v1/transactions/{tid}/documents/{did}/share-with-client",
            token=agent_tok,
            body={"action": "acknowledge"},
        )
        print("share", status, json.dumps(shared, default=str)[:500])
        status, dash = req("GET", f"/api/v1/dashboard/client?transaction_id={tid}", token=client_tok)
        home = (dash or {}).get("home") or {}
        print("client after share", status, {
            "next_action": (home.get("next_action") or {}).get("title"),
            "cta": (home.get("next_action") or {}).get("cta_target"),
            "attention": home.get("documents_needing_attention"),
        })


if __name__ == "__main__":
    main()
