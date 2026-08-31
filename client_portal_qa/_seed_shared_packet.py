"""Upload a staff packet onto Bradyn's focused deal and share it for acknowledge."""
from __future__ import annotations

import json
from pathlib import Path

import httpx

API = "http://127.0.0.1:8000"
ADMIN_EMAIL = "shyna.elene@minafter.com"
AGENT_EMAIL = "keison.londyn@minafter.com"
PASSWORD = "QWE!@#asd234"
TX_ID = "f8bf6263-99cd-4ed6-8225-b9a5a951de07"
FIXTURE = Path(__file__).with_name("fixtures") / "qa-upload.txt"


def login(client: httpx.Client, email: str) -> str:
    r = client.post(
        f"{API}/api/v1/users/login",
        data={"username": email, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def main() -> None:
    if not FIXTURE.exists():
        raise SystemExit(f"missing fixture {FIXTURE}")
    with httpx.Client() as client:
        token = None
        staff_email = ADMIN_EMAIL
        for email in (ADMIN_EMAIL, AGENT_EMAIL):
            try:
                token = login(client, email)
                staff_email = email
                break
            except httpx.HTTPStatusError as exc:
                print("login failed", email, exc.response.status_code)
        if not token:
            raise SystemExit("no staff login")
        headers = {"Authorization": f"Bearer {token}"}
        files = {"file": ("Closing-wire-notice.txt", FIXTURE.read_bytes(), "text/plain")}
        data = {
            "transaction_id": TX_ID,
            "doc_type": "other",
            "doc_label": "Closing wire notice",
        }
        up = client.post(
            f"{API}/api/v1/documents/upload",
            headers=headers,
            data=data,
            files=files,
            timeout=60,
        )
        print("upload", up.status_code, up.text[:400])
        up.raise_for_status()
        doc = up.json()
        doc_id = doc.get("id") or (doc.get("item") or {}).get("id")
        if not doc_id:
            raise SystemExit(f"no document id: {doc}")
        share = client.post(
            f"{API}/api/v1/transactions/{TX_ID}/documents/{doc_id}/share-with-client",
            headers=headers,
            json={"action": "acknowledge"},
            timeout=30,
        )
        print("share", share.status_code, share.text[:500])
        share.raise_for_status()
        print(json.dumps({"staff": staff_email, "document_id": doc_id, "transaction_id": TX_ID}))


if __name__ == "__main__":
    main()
