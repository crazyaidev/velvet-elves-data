"""Print local env hostnames only. No secrets."""
from pathlib import Path
from urllib.parse import urlparse

root = Path(r"c:\Projects\velvet-elves-backend")
for p in sorted(root.glob(".env*")):
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("SUPABASE_URL="):
            raw = line.split("=", 1)[1].strip().strip('"').strip("'")
            print(f"{p.name} supabase={urlparse(raw).hostname}")
        elif line.startswith("FRONTEND_URL="):
            raw = line.split("=", 1)[1].strip().strip('"').strip("'")
            print(f"{p.name} frontend={raw}")
        elif line.startswith("APP_ENV="):
            print(f"{p.name} {line.strip()}")
