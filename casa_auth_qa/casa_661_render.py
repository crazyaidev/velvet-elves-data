"""Render 6.6.1 storage PNG from Playwright JSON. Never copies token values."""
from __future__ import annotations

import json
from pathlib import Path

from casa_pack_lib import save_probe

SRC = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\6.6.1\_storage.json")
OUT = SRC.parent


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    before = data["before"]
    after = data["after"]
    remain = ", ".join(after.get("names") or []) or "(none)"
    url_after = data.get("url_after") or ""
    ok = (
        before["token"]
        and before["refresh"]
        and (not after["token"])
        and (not after["refresh"])
        and url_after.endswith("/login")
    )
    save_probe(
        OUT,
        "CASA_6_6_1_storage.png",
        "6.6.1  Staging localStorage key presence around logout",
        "Key names only. Token values are not shown. Playwright evaluate, not DevTools Application panel.",
        [
            (
                "Before Log Out",
                f"velvet_elves_token={before['token']}  velvet_elves_refresh_token={before['refresh']}",
                before["token"] and before["refresh"],
            ),
            (
                "After Log Out",
                f"velvet_elves_token={after['token']}  velvet_elves_refresh_token={after['refresh']}",
                (not after["token"]) and (not after["refresh"]),
            ),
            ("Keys remaining after logout", remain, True),
            ("URL after logout", url_after, url_after.endswith("/login")),
        ],
    )
    SRC.unlink()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
