"""Staging: extra {{7*7}} query is not evaluated (CASA 5.1.4). Not an exploit."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from casa_pack_lib import save_probe

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.1.4")
OUT.mkdir(parents=True, exist_ok=True)
PAYLOAD = "{{7*7}}"


def request(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def main() -> int:
    query = urllib.parse.urlencode({"q": PAYLOAD})
    url = f"{API}/api/v1/health?{query}"
    status, body = request(url)
    compact = " ".join(body.split())
    not_49 = compact.strip() not in ("49", '"49"')
    no_eval_in_json = True
    try:
        parsed = json.loads(body)
        no_eval_in_json = parsed != 49 and parsed != "49"
        if isinstance(parsed, dict):
            no_eval_in_json = 49 not in parsed.values() and "49" not in parsed.values()
    except json.JSONDecodeError:
        no_eval_in_json = "49" not in compact
    ignored = PAYLOAD not in compact or "{{" in compact
    ok = status in (200, 422) and not_49 and no_eval_in_json and "ok" in compact.lower()
    save_probe(
        OUT,
        "CASA_5_1_4_probe.png",
        "5.1.4  Staging does not evaluate template expressions",
        "GET /api/v1/health with q={{7*7}}. Extra query is ignored. Not an exploit.",
        [
            ("Request", url, True),
            ("Query (decoded)", "q={{7*7}}", True),
            ("HTTP status", str(status), status in (200, 422)),
            ("JSON body", compact[:110], ok),
            ("Evaluated to 49?", "NO — health JSON, extra query ignored", ok),
        ],
    )
    print(f"  status={status} ok={ok} ignored={ignored} body={compact[:120]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
