"""Deep live probe of Yareny FSBO verbs (download, flag, mailbox, isolation)."""
from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "http://127.0.0.1:8000"
FSBO_EMAIL = "yareny.evaly@minafter.com"
PASSWORD = "QWE!@#asd234"
MAPLE = "f5dcbc04-f63d-4bb5-859d-b1cd8dd7a55c"
VELVET = "9dacae5e-cf19-4312-b976-81e587dd0df6"
GHOST = "00000000-0000-0000-0000-000000000000"


def req(method: str, path: str, token: str | None = None, body: dict | None = None, timeout: int = 30):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = Request(API + path, data=data, headers=headers, method=method)
    try:
        with urlopen(r, timeout=timeout) as resp:
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
    with urlopen(r, timeout=20) as resp:
        return json.loads(resp.read().decode())["access_token"]


def slim(obj, n=2400):
    return json.dumps(obj, default=str)[:n]


def main() -> None:
    tok = login(FSBO_EMAIL)
    print("login ok")

    st, ov = req("GET", "/api/v1/dashboard/fsbo/overview", tok)
    print("overview", st)
    if isinstance(ov, dict):
        print("counts", slim({
            "n": len(ov.get("properties") or []),
            "missing": ov.get("missing_documents_count"),
            "seller_owed": ov.get("seller_owed_missing_count"),
            "invoices": ov.get("open_invoice_count"),
            "share_live": ov.get("share_links_live"),
            "dtc": ov.get("days_to_close_nearest"),
        }))
        print("critical_next_steps", slim([
            {
                "kind": s.get("kind"),
                "title": s.get("title"),
                "tx": s.get("transaction_id"),
                "doc_type": s.get("doc_type"),
                "cta": s.get("cta_label"),
            }
            for s in (ov.get("critical_next_steps") or [])
        ]))
        for p in ov.get("properties") or []:
            na = p.get("next_action") or {}
            print("property", slim({
                "addr": p.get("address"),
                "state": p.get("state") or p.get("fsbo_state"),
                "missing": p.get("missing_docs_count"),
                "seller_owed": p.get("seller_owed_missing_count"),
                "msgs": p.get("new_messages_count"),
                "next": {
                    "kind": na.get("kind"),
                    "title": na.get("title"),
                    "doc_type": na.get("doc_type"),
                    "cta": na.get("cta_label"),
                },
                "checklist": p.get("listing_prep_checklist"),
            }))

    st, docs = req("GET", "/api/v1/dashboard/fsbo/documents", tok)
    print("documents", st)
    own_ids = []
    staff_ids = []
    if isinstance(docs, dict):
        print("totals", slim(docs.get("totals")))
        for g in docs.get("properties") or []:
            board = g.get("board") or {}
            missing_items = []
            for col in board.get("columns") or []:
                if col.get("key") == "missing":
                    missing_items = col.get("items") or []
            print("docs_group", slim({
                "addr": g.get("address"),
                "state": g.get("fsbo_state"),
                "counts": board.get("counts"),
                "seller_owed": board.get("seller_owed_missing"),
                "velvet": board.get("velvet_collecting_missing"),
                "missing_items": missing_items,
                "projected": [
                    {
                        "id": d.get("id"),
                        "label": d.get("doc_label"),
                        "type": d.get("doc_type"),
                        "can_open": d.get("can_open"),
                        "can_flag": d.get("can_flag"),
                        "action": d.get("action"),
                        "own": d.get("is_own"),
                        "visible": d.get("is_client_visible"),
                    }
                    for d in (g.get("documents") or [])[:12]
                ],
            }))
            for d in g.get("documents") or []:
                if d.get("is_own"):
                    own_ids.append(d["id"])
                elif not d.get("can_open"):
                    staff_ids.append(d["id"])

    print("own_ids", own_ids[:4], "staff_closed", staff_ids[:4])

    if own_ids:
        st, body = req("GET", f"/api/v1/documents/{own_ids[0]}/download", tok)
        print("download_own", st, slim(body)[:300])
    if staff_ids:
        st, body = req("GET", f"/api/v1/documents/{staff_ids[0]}/download", tok)
        print("download_staff_unshared", st, slim(body)[:300])

    st, body = req("GET", f"/api/v1/dashboard/fsbo/properties/{GHOST}", tok)
    print("ghost_property", st, slim(body)[:200])

    st, maple = req("GET", f"/api/v1/dashboard/fsbo/properties/{MAPLE}", tok)
    print("maple", st, slim({
        "addr": (maple or {}).get("address") if isinstance(maple, dict) else maple,
        "state": (maple or {}).get("fsbo_state") if isinstance(maple, dict) else None,
        "go_live": (maple or {}).get("listing_go_live_date") if isinstance(maple, dict) else None,
        "next": (maple or {}).get("next_action") if isinstance(maple, dict) else None,
        "milestones": [
            {"title": m.get("title") or m.get("name") or m.get("label"), "status": m.get("status")}
            for m in ((maple or {}).get("milestones") or [])[:8]
        ] if isinstance(maple, dict) else None,
        "contacts": [
            {"role": c.get("party_role"), "label": c.get("role_label"), "name": c.get("name")}
            for c in ((maple or {}).get("contacts") or [])
        ] if isinstance(maple, dict) else None,
        "checklist": (maple or {}).get("listing_prep_checklist") if isinstance(maple, dict) else None,
    }))

    st, velvet = req("GET", f"/api/v1/dashboard/fsbo/properties/{VELVET}", tok)
    print("velvet", st, slim({
        "addr": (velvet or {}).get("address") if isinstance(velvet, dict) else velvet,
        "state": (velvet or {}).get("fsbo_state") if isinstance(velvet, dict) else None,
        "next": (velvet or {}).get("next_action") if isinstance(velvet, dict) else None,
        "milestones": [
            {"title": m.get("title") or m.get("name") or m.get("label"), "status": m.get("status")}
            for m in ((velvet or {}).get("milestones") or [])[:8]
        ] if isinstance(velvet, dict) else None,
        "contacts": [
            {"role": c.get("party_role"), "label": c.get("role_label"), "name": c.get("name")}
            for c in ((velvet or {}).get("contacts") or [])
        ] if isinstance(velvet, dict) else None,
        "board_missing": (velvet or {}).get("document_board", {}).get("seller_owed_missing") if isinstance(velvet, dict) else None,
        "velvet_collecting": (velvet or {}).get("document_board", {}).get("velvet_collecting_missing") if isinstance(velvet, dict) else None,
    }))

    st, ms = req("GET", "/api/v1/dashboard/fsbo/milestones", tok)
    print("milestones", st)
    if isinstance(ms, dict):
        print("mailbox", slim([
            {
                "id": m.get("id"),
                "tx": m.get("transaction_id"),
                "dir": m.get("direction"),
                "seen": m.get("seen"),
                "subj": m.get("subject"),
                "body": (m.get("body") or "")[:80],
            }
            for m in (ms.get("messages") or [])[:8]
        ]))

    st, posted = req(
        "POST",
        "/api/v1/dashboard/fsbo/messages",
        tok,
        {"transaction_id": MAPLE, "body": "QA deep probe: can the seller send a question?"},
    )
    print("post_message", st, slim(posted)[:400])

    st, settings = req("GET", "/api/v1/fsbo/settings", tok)
    print("settings", st, slim(settings)[:400])

    st, inv = req("GET", "/api/v1/client/invoices", tok)
    print("invoices", st, slim(inv)[:200])

    st, ack = req("POST", f"/api/v1/client/documents/{own_ids[0]}/acknowledge", tok) if own_ids else (None, None)
    print("ack_own_unshared", st, slim(ack)[:300] if ack is not None else "skip")

    # Isolation: staff documents list should not be a tenant dump, but this
    # seller hitting /transactions must 403/404.
    st, txs = req("GET", "/api/v1/transactions?page_size=5", tok)
    print("staff_transactions", st, slim(txs)[:200])


if __name__ == "__main__":
    main()
