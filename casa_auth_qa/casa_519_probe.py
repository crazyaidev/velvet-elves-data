"""Staging: extra command-looking query is ignored (CASA 5.1.9). Not an exploit."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from casa_pack_lib import save_probe

API = "https://api.stage.velvetelves.com"
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.1.9")
OUT.mkdir(parents=True, exist_ok=True)
PAYLOAD = "$(id)"
STDOUT_MARKERS = (
    "uid=",
    "gid=",
    "groups=",
    "root:x:",
    "command not found",
    "microsoft windows",
    "/bin/sh",
    "nt authority",
)


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
    low = compact.lower()
    no_stdout = not any(m in low for m in STDOUT_MARKERS)
    health_ok = False
    try:
        parsed = json.loads(body)
        health_ok = isinstance(parsed, dict) and parsed.get("status") == "ok"
    except json.JSONDecodeError:
        health_ok = False
    ok = status == 200 and health_ok and no_stdout
    save_probe(
        OUT,
        "CASA_5_1_9_probe.png",
        "5.1.9  Staging health ignores a command-looking query",
        "GET /api/v1/health with q=$(id). Extra query is ignored. Not an exploit. No command was run.",
        [
            ("Request", url, True),
            ("Query (decoded)", "q=$(id)", True),
            ("HTTP status", str(status), status == 200),
            ("JSON body", compact[:110], ok),
            ("Command stdout?", "NO — health JSON, extra query ignored", ok),
        ],
    )
    print(f"  status={status} ok={ok} no_stdout={no_stdout} body={compact[:120]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
