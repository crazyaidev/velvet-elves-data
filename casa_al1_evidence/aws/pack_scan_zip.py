"""Pack velvet-elves-backend for Fluid Attacks CodeBuild (no .venv / .env)."""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

ROOT = Path(r"c:\Projects\velvet-elves-backend")
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\2026-08-21\sast\velvet-elves-backend-scan.zip")
AWS = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\aws")

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    ".ruff_cache",
    "logs",
    ".mypy_cache",
    ".tox",
    "dist",
    "build",
}
SKIP_NAMES = {".env", ".coverage"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".log"}


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            rel_dir = Path(dirpath).relative_to(ROOT)
            if any(p in SKIP_DIRS for p in rel_dir.parts):
                continue
            for name in filenames:
                if name in SKIP_NAMES or name.startswith(".env.") or Path(name).suffix in SKIP_SUFFIXES:
                    continue
                src = Path(dirpath) / name
                arc = str(Path(*rel_dir.parts) / name) if rel_dir.parts else name
                z.write(src, arc.replace("\\", "/"))
                count += 1
        extra = {
            "config.yaml": AWS / "config.yaml",
            "buildspec.yml": AWS / "buildspec.yml",
        }
        for arc, path in extra.items():
            z.write(path, arc)
            count += 1

    names = zipfile.ZipFile(OUT).namelist()
    print("files", count)
    print("bytes", OUT.stat().st_size)
    print("has_env", any(n == ".env" or n.endswith("/.env") for n in names))
    print("has_config", "config.yaml" in names)
    print("has_dockerfile", "Dockerfile" in names)
    print("has_venv", any(".venv" in n for n in names))


if __name__ == "__main__":
    main()
