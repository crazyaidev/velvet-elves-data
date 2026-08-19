"""Seed two FSBO properties for yareny.evaly@minafter.com so Chrome QA is populated."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "http://127.0.0.1:8000"
FSBO_EMAIL = "yareny.evaly@minafter.com"
ADMIN_EMAIL = "shyna.elene@minafter.com"
AGENT_EMAIL = "keison.londyn@minafter.com"
PASSWORD = "QWE!@#asd234"
PREP_ADDR = "14 Maple Prep Lane"
CONTRACT_ADDR = "22 Velvet Contract Ave"
FIXTURE = Path(__file__).with_name("fixtures") / "qa-upload.txt"


def _multipart(form: dict, files: dict) -> tuple[bytes, str]:
    boundary = "----VeFsboQaBoundary"
    chunks: list[bytes] = []
    for key, value in (form or {}).items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        chunks.append(str(value).encode() + b"\r\n")
    for key, (filename, content, ctype) in (files or {}).items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
        )
        chunks.append(f"Content-Type: {ctype}\r\n\r\n".encode())
        chunks.append(content + b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def req(method: str, path: str, token: str | None = None, body: dict | None = None, form=None, files=None):
    if files is not None:
        data, ctype = _multipart(form or {}, files)
        headers = {"Content-Type": ctype}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = Request(API + path, data=data, headers=headers, method=method)
        try:
            with urlopen(r, timeout=60) as resp:
                raw = resp.read().decode()
                return resp.status, json.loads(raw) if raw else None
        except HTTPError as e:
            raw = e.read().decode()
            try:
                parsed = json.loads(raw) if raw else raw
            except Exception:
                parsed = raw
            return e.code, parsed

    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = Request(API + path, data=data, headers=headers, method=method)
    try:
        with urlopen(r, timeout=60) as resp:
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


def find_tx(staff_tok: str, address: str) -> dict | None:
    q = urlencode({"search": address, "page_size": 100})
    status, body = req("GET", f"/api/v1/transactions?{q}", token=staff_tok)
    if status != 200 or not isinstance(body, dict):
        status, body = req("GET", "/api/v1/transactions?page_size=100", token=staff_tok)
    items = []
    if isinstance(body, dict):
        items = body.get("items") or body.get("data") or []
    for t in items:
        if address.lower() in str(t.get("address") or "").lower():
            return t
    return None


def ensure_assignment(staff_tok: str, tx_id: str, user_id: str) -> None:
    status, body = req(
        "POST",
        f"/api/v1/transactions/{tx_id}/assignments",
        token=staff_tok,
        body={"user_id": user_id, "role_in_transaction": "for_sale_by_owner"},
    )
    print("assign", tx_id[:8], status, str(body)[:240] if status >= 400 else "ok")


def create_tx(staff_tok: str, payload: dict) -> dict | None:
    status, body = req("POST", "/api/v1/transactions", token=staff_tok, body=payload)
    print("create", payload["address"], status, str(body)[:400] if status >= 400 else (body or {}).get("id"))
    if status in (200, 201) and isinstance(body, dict):
        return body
    return None


def main():
    fsbo_tok = login(FSBO_EMAIL)
    _, me = req("GET", "/api/v1/users/me", token=fsbo_tok)
    fsbo_id = me["id"]
    print("fsbo", fsbo_id, me.get("email"), me.get("role"))

    staff_tok = None
    for email in (ADMIN_EMAIL, AGENT_EMAIL):
        try:
            staff_tok = login(email)
            print("staff", email)
            break
        except SystemExit as e:
            print(e)
    if not staff_tok:
        raise SystemExit("no staff login")

    closing = (date.today() + timedelta(days=21)).isoformat()
    inspection = (date.today() + timedelta(days=7)).isoformat()
    em = (date.today() + timedelta(days=3)).isoformat()
    contract_date = date.today().isoformat()

    prep = find_tx(staff_tok, PREP_ADDR)
    if not prep:
        prep = create_tx(
            staff_tok,
            {
                "address": PREP_ADDR,
                "city": "Indianapolis",
                "state": "IN",
                "zip_code": "46204",
                "use_case": "Sell-Fin",
                "representation_type": "Seller",
                "financing_type": "Financed",
                "is_fsbo": True,
                "fsbo_state": "listing_prep",
                "status": "Active",
                "notes": "FSBO Chrome QA — listing prep",
            },
        )
    else:
        print("prep exists", prep.get("id"))
        req(
            "PATCH",
            f"/api/v1/transactions/{prep['id']}",
            token=staff_tok,
            body={"is_fsbo": True, "fsbo_state": "listing_prep"},
        )

    contract = find_tx(staff_tok, CONTRACT_ADDR)
    if not contract:
        contract = create_tx(
            staff_tok,
            {
                "address": CONTRACT_ADDR,
                "city": "Indianapolis",
                "state": "IN",
                "zip_code": "46220",
                "use_case": "Sell-Fin",
                "representation_type": "Seller",
                "financing_type": "Financed",
                "purchase_price": 385000,
                "is_fsbo": True,
                "fsbo_state": "under_contract",
                "status": "Active",
                "contract_acceptance_date": contract_date,
                "closing_date": closing,
                "em_delivered_date": em,
                "inspection_response_date": inspection,
                "notes": "FSBO Chrome QA — under contract",
            },
        )
    else:
        print("contract exists", contract.get("id"))
        req(
            "PATCH",
            f"/api/v1/transactions/{contract['id']}",
            token=staff_tok,
            body={
                "is_fsbo": True,
                "fsbo_state": "under_contract",
                "closing_date": closing,
                "contract_acceptance_date": contract_date,
                "em_delivered_date": em,
                "inspection_response_date": inspection,
            },
        )

    if not prep or not contract:
        raise SystemExit("could not create/find both properties")

    for tx in (prep, contract):
        ensure_assignment(staff_tok, tx["id"], fsbo_id)

    # People on the under-contract file
    status, party = req(
        "POST",
        f"/api/v1/transactions/{contract['id']}/parties",
        token=staff_tok,
        body={
            "party_role": "buyer",
            "full_name": "Jordan Buyer",
            "email": "jordan.buyer@example.com",
            "phone": "(317) 555-0144",
        },
    )
    print("party buyer", status, str(party)[:200] if status >= 400 else "ok")
    status, party = req(
        "POST",
        f"/api/v1/transactions/{contract['id']}/parties",
        token=staff_tok,
        body={
            "party_role": "title_company",
            "company": "Meridian Title",
            "full_name": "Pat Title",
            "email": "pat.title@example.com",
            "phone": "(317) 555-0190",
        },
    )
    print("party title", status, str(party)[:200] if status >= 400 else "ok")

    # Coordinator outbound email so Messages is not empty
    status, log = req(
        "POST",
        "/api/v1/communication-logs",
        token=staff_tok,
        body={
            "channel": "email",
            "direction": "outbound",
            "transaction_id": contract["id"],
            "recipient_emails": [FSBO_EMAIL],
            "subject": "Please upload your purchase agreement",
            "body": "Hi Yareny — please upload the signed purchase agreement when you have it.",
        },
    )
    print("comm log", status, str(log)[:240] if status >= 400 else "ok")

    # One uploaded doc on the contract file so Flag is testable
    if FIXTURE.exists():
        status, doc = req(
            "POST",
            "/api/v1/documents/upload",
            token=staff_tok,
            form={
                "transaction_id": contract["id"],
                "doc_type": "purchase_agreement",
                "doc_label": "Purchase Agreement",
            },
            files={"file": ("purchase-agreement.txt", FIXTURE.read_bytes(), "text/plain")},
        )
        print("upload", status, str(doc)[:240] if status >= 400 else (doc or {}).get("id"))
    else:
        print("missing fixture", FIXTURE)

    # Confirm FSBO can see them
    fsbo_tok = login(FSBO_EMAIL)
    status, overview = req("GET", "/api/v1/dashboard/fsbo/overview", token=fsbo_tok)
    props = (overview or {}).get("properties") or []
    print(
        "overview after seed",
        status,
        {
            "n": len(props),
            "addresses": [p.get("address") for p in props],
            "missing": overview.get("missing_documents_count") if isinstance(overview, dict) else None,
            "next": [(s.get("title"), s.get("action_kind")) for s in (overview.get("critical_next_steps") or [])[:3]]
            if isinstance(overview, dict)
            else None,
        },
    )


if __name__ == "__main__":
    main()
