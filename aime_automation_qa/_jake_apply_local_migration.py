"""Apply Jake TME SQL to the local Supabase project if tables are missing."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import psycopg

BACKEND = Path(r"c:\Projects\velvet-elves-backend")
SQL_PATH = BACKEND / "supabase" / "migrations" / "20261008090000_jake_tme_intelligence.sql"


def _dsn(raw: str) -> str:
    url = raw.strip().strip('"').strip("'")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def main() -> int:
    load_dotenv(BACKEND / ".env")
    raw = os.getenv("SUPABASE_DB_URL")
    if not raw:
        print("no SUPABASE_DB_URL")
        return 2
    if not SQL_PATH.exists():
        print("missing migration file")
        return 2
    dsn = _dsn(raw)
    try:
        with psycopg.connect(dsn, connect_timeout=20) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.transaction_facts')")
                facts = cur.fetchone()[0]
                cur.execute(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'transaction_parties'
                      AND column_name = 'is_decision_maker'
                    """
                )
                party_col = cur.fetchone()
                print(f"transaction_facts={facts} party_is_decision_maker={bool(party_col)}")
                if facts and party_col:
                    print("jake_schema=already_present")
                    return 0
                sql = SQL_PATH.read_text(encoding="utf-8")
                cur.execute(sql)
            conn.commit()
            print("jake_schema=applied")
            return 0
    except Exception as exc:  # noqa: BLE001
        print(f"migrate_error={type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
