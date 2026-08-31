# Dependency audits — 21 Aug 2026

Not a CASA-mapped SAST/DAST. Morning JSON dumps (`deps/pip-audit.json`, `deps/npm-audit.json`) are the **pre-bump** baseline.

## Frontend

Pinned `react-router-dom` **7.18.2** (was 7.13.1). `npm audit --omit=dev` → **0 vulnerabilities**. Lint + production build passed. Dev-only toolchain vulns (Vitest UI critical, etc.) remain out of the CloudFront SPA.

## Backend (after local bumps)

`pip-audit` now **4 vulns in 4 packages** (was 56 in 9).

| Package | Now | Status |
| --- | --- | --- |
| python-multipart | 0.0.32 | cleared |
| python-jose | 3.5.0 | cleared (still pulls unfixed **ecdsa** 0.19.2) |
| cryptography | 50.0.0 | cleared |
| FastAPI / Starlette | 0.135.4 / 1.3.1 | cleared |
| Pillow | 12.3.0 | cleared |
| pydantic-ai-slim | 1.22.0 | **open** — PYSEC-2026-2980; fix 1.56.0 needs AI-stack + `opentelemetry-api<1.44` revisit |
| PyPDF2 | 3.0.1 | **open** — audit says 3.9.0; PyPI latest is still 3.0.1. Migrate to `pypdf` later |
| pytest | 8.3.4 | **split coded 21 Aug** — moved to `requirements-dev.txt`. Live staging image still has pytest until the next backend deploy. |
| ecdsa | 0.19.2 | **open** — no fix listed; transitive of python-jose |

`ruff check .` passed. **pytest 2015 passed** on the bumped stack. FastAPI/crypto pins **deployed to staging 21 Aug 2026**. pytest/ruff split is a follow-up image.

## Accepted for now

- `ecdsa` — no upstream fix; JWT path uses `python-jose[cryptography]`.
- pytest in the **current** staging image — operational, not a request-path High; next image drops it.
- `PyPDF2` / `pydantic-ai-slim` — need dedicated bumps, not mixed into this FastAPI jump.
