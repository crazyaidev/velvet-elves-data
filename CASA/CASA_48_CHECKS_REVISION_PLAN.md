# CASA AL1 — 48-check revision plan (fix first, then upload)

**Date:** 27 Aug 2026 · **Phase 1 code complete same day** (backend 2069 tests green, frontend 546 green, tsc/eslint clean, pip-audit clean save two documented notes)
**Google deadline:** 18 Nov 2026 (LOV must be issued and sent by TAC before then)
**Portal state:** Step 3 "Assessment Review" In Progress. Scan zip accepted 26 Aug. All 48 evidence rows empty. Confirm box unchecked.
**Companions:** `TAC_ESOF_PORTAL_GUIDE.md` (§7 = row-by-row comments), `../casa_al1_evidence/m9/CASA_PORTAL_PACK.md` (comments + image descriptions; filename is fixed), `../casa_al1_evidence/m9/GAP_ANALYSIS_48_CHECKS.md` (verdicts), `../casa_al1_evidence/m9/` (write-ups)

Target: every row filled with a true statement + PNG evidence. All four known gaps are now **fixed in code**; they become true claims after the owner deploys. TAC Premium has unlimited retests — the bar is **no false claims**, not 48 greens on the first pass.

## Hard rules (unchanged)

- Never claim: HttpOnly session cookies, default MFA for **all** users, a live breached-password API (the denylist is static), Disconnect token wipe, Zero Data Retention.
- **Deploys are owner-run.** The agent never runs `git commit`/`push`; staging gets code only after local tests, production only after staging verification.
- Portal comments: English letters and symbols/punctuation are allowed. Do not paste secrets.
- Per-row upload modal: PNG/JPG/JPEG only, max 10 files. Markdown never goes into the portal.
- No secrets in screenshots (no API keys, no JWTs, no Fernet keys, no Supabase service keys).
- Don't check "I confirm…" or click Submit until all 48 rows are done.
- Google Cloud Console OAuth on `velvet-vles` stays frozen.

---

## Phase 1 — Code fixes ✅ LANDED 27 Aug (deploys pending, owner-run)

All Phase 1 code + tests are complete locally. What remains in this phase is only the deploy train: **staging → manual verify → production**, run by the owner.

### 1.1 Logout revocation — fixes row 10 (2.2.1) — ✅ CODE DONE

- [x] Backend: `POST /api/v1/users/logout` revokes the Supabase session (`auth.admin.sign_out`, scope `local`); invalid/expired bearer still returns 204 without a Supabase call.
- [x] Backend test: `test_logout_revokes_supabase_session`, `test_logout_requires_bearer_token`.
- [x] Frontend: `AuthContext.logout()` fires the revoke call (keepalive, best-effort) before `clearTokens()`.
- [ ] Deploy staging → manual check: login, logout, replay saved refresh token → 401.
- [ ] Deploy production (normal `main` → `prod` flow).
- [x] §7 row 10 comment updated in `TAC_ESOF_PORTAL_GUIDE.md`.

### 1.2 Login hardening — strengthens row 1 (1.1.1) — ✅ CODE DONE

- [x] `_login_limiter`: 10 req / 60 s per IP on `POST /users/login` (same in-process pattern as register).
- [x] Per-account soft lockout: 20 failed attempts / rolling hour, IP-rotation-proof, cleared on success (`app/core/login_throttle.py`) — satisfies ADA 1.1.1 option 2.1 (≤100/hour).
- [x] Common-password denylist (~200 entries, `app/core/weak_passwords.py`) shared by register / invite-accept / password-reset validators — makes the 2.4 claim real. Static list; never call it HIBP.
- [x] Tests: `test_login_is_rate_limited_per_ip`, `test_login_account_lockout_survives_ip_rotation`, `test_login_success_clears_failure_history`, `test_register_rejects_common_breached_password`.
- [x] `CASA_1_1_1_brute_force.md` rewritten to the new true state.
- [ ] Regenerate `tac_images/1.1.1/CASA_1_1_1_page1/2.png` from the rewritten write-up **after the production deploy**.

### 1.3 Platform-admin MFA — row 26 (3.3.1) — ✅ OPTION A IMPLEMENTED

- [x] Backend: TOTP via Supabase GoTrue — `POST /users/mfa/enroll` (QR + secret), `POST /users/mfa/verify` (challenge+verify → AAL2 session), `GET /users/mfa/factors`, `DELETE /users/mfa/factors/{id}` (`app/services/mfa_service.py`).
- [x] Login step-up: accounts with a verified TOTP factor get `mfa_required=true` + an AAL1 token only (refresh token withheld) until the code is verified.
- [x] Enforcement: `require_platform_admin` demands the `aal2` JWT claim (`PLATFORM_ADMIN_MFA_REQUIRED=true` by default; env escape hatch for emergencies).
- [x] SPA: login challenge step on `LoginPage`, enrollment QR/code gate on platform routes (`PlatformMfaGate` inside `PlatformAdminGuard`).
- [x] Tests: `test_mfa_api.py` (13) + `LoginPage` MFA unit tests.
- [ ] After production deploy: each platform admin logs in → gate appears → scan QR in authenticator app → verified. Then screenshot the gate + a code prompt for the row.

### 1.4 Dependency cleanup — row 42 (6.1.1) — ✅ CODE DONE

- [x] `pydantic-ai-slim` 1.22.0 → **1.107.5** (PYSEC-2026-2980 fixed). Rode the extras' floors: `openai` 3.5.0, `anthropic` 1.1.0, `pydantic` 2.13.4; `opentelemetry-api` unpinned (1.44.0 works). Packet-parsing transport now hands ready-made SDK clients to pydantic-ai (the new SDKs run on httpx2 and reject pydantic-ai's classic httpx client injection).
- [x] `PyPDF2` → **`pypdf` 6.16.2** (PYSEC-2026-1835 fixed) across code + tests; PyPDF2 uninstalled.
- [x] Dockerfile upgrades pip at build time (pip advisories).
- [x] Full pytest suite green on the new stack (2069 passed).
- [x] pip-audit residuals — exactly two, both documented: `ecdsa` (PYSEC-2026-1325, **no fix exists**, transitive via python-jose, accepted-risk note) and `pytest` (PYSEC-2026-1845, dev-only, never shipped).
- [ ] After deploy: re-run `pip-audit` and `npm audit --omit=dev` → fresh screenshots for the row (S12).

---

## Phase 2 — Verify settings, no code (screenshot batch)

All Velvet Elves screenshots go to `casa_al1_evidence/m9/tac_images/<check-id>/` (one folder per row). Filenames `CASA_<row-id>_<what>.png`. No keys in frame. **Owner captures** any screenshot of another product (Supabase, SSL Labs, AWS, Google Cloud). The agent does not take those.

| # | What | Where | Feeds rows |
| --- | --- | --- | --- |
| S1 | Auth rate limits page | Supabase dashboard → Authentication → Rate Limits (production project) | 1 |
| S2 | Access-token expiry — **done 28 Aug 2026** via live staging JWT `exp − iat` = 8 h (not the 1 h default). Packed as 2.2.3. Owner Sessions/JWT dashboard shot is optional backup. | Staging login decode + `decode_access_token` | 12 |
| S3 | OTP / reset token expiry + single-use | Supabase → Authentication → Email settings | 5–8 |
| S4 | Password change revokes other sessions — **done 28 Aug 2026** via GoTrue source (`UpdatePassword` → LogoutAllExceptMe / Logout), not a dashboard toggle. Packed as 2.2.2. | GoTrue public source + confirm code | 11 |
| S5 | SSL Labs grade `app.velvetelves.com` | ssllabs.com/ssltest | 27, 28 |
| S6 | SSL Labs grade `api.prod.velvetelves.com` | ssllabs.com/ssltest | 27, 28 |
| S7 | Register 429 after 6 rapid signups | staging, DevTools network tab | 1, 22 |
| S8 | Register password-rules UI (8+, upper, lower, digit, symbol) | staging register page | 1, 2 |
| S9 | Route 53 hosted zone review — no dangling CNAMEs | AWS console | 45 |
| S10 | Logout → refresh replay 401 (after 1.1 lands) | staging, DevTools | 10 |
| S11 | Prod `/api/docs` 404 + security headers | browser / curl | 43 |
| S12 | `pip-audit` + `npm audit` fresh summaries (after 1.4) | terminal | 42 |

Already on disk: `openai-data-controls.png` (subprocessor/AI questions), `CASA_1_1_1_page1/2.png` (regenerate after 1.2).

---

## Phase 3 — Render the write-ups as PNG evidence pages

The portal rejects `.md`. Each write-up becomes 1–3 PNG "pages" (same Pillow script as the 1.1.1 pages; script lives in this session's shell history and is rerunnable).

| Source (m9) | PNG set | Feeds rows |
| --- | --- | --- |
| `CASA_1_1_1_brute_force.md` (regenerated) | `CASA_1_1_1_page1/2` | 1 |
| `self_attestation_draft.md` | `CASA_attest_page1..n` | 2, 4–8, 11, 17, 41 |
| `M9d_token_storage.md` | `CASA_M9d_page1` | 3, 9, 15, 16, 48 |
| `compensating_controls.md` | `CASA_comp_page1..n` | 10*, 12, 13, 14, 22, 37, 47 |
| `M9f_tenant_isolation.md` | `CASA_M9f_page1` | 18–21, 44 |
| `M9a_architecture.md` | `CASA_M9a_page1` | 23, 27, 28, 43, 45 |
| `M9c_scope_to_google_api.md` + `M9b_data_flow.md` | `CASA_oauth_page1` | 24, 25, 32 |
| `M9e_pii_encryption.md` | `CASA_M9e_page1` | 29, 30 |
| `SAST_SUMMARY.md` | `CASA_sast_page1` | 33, 34, 39 |
| `DAST_SUMMARY.md` (incl. false-positive replays) | `CASA_dast_page1/2` | 31, 35, 36, 38, 40 |
| `DEPS_SUMMARY.md` (refreshed) | `CASA_deps_page1` | 42 |
| `M9g_logging.md` | `CASA_M9g_page1` | 46 |
| New: 2.2.1 logout note (after fix) | `CASA_2_2_1_page1` | 10 |
| New: 3.3.1 MFA statement (per 1.3 decision) | `CASA_3_3_1_page1` | 26 |

- [ ] Update the source markdowns whose facts change in Phase 1 (logout, login limiter, MFA, deps) **before** rendering.
- [ ] Render all sets; eyeball each PNG for cut-off text.

---

## Phase 4 — Fill the portal (one sitting, ~2 h)

- [ ] Work top to bottom in domain batches: rows 1–8, 9–17, 18–26, 27–30, 31–41, 42–48.
- [ ] Per row: paste the comment from `TAC_ESOF_PORTAL_GUIDE.md` §7 (punctuation allowed; use the updated comments for rows 1, 10, 26, 42) → Upload Evidences → attach the PNGs for that row (≤10) → Upload.
- [ ] Screenshot the page after each batch (recovery point if the portal loses state).
- [ ] After all 48: re-scroll the whole list — every row has a comment and at least one file.
- [ ] Check "I confirm that all checklist items have been reviewed and verified".
- [ ] Click **Submit**. Screenshot the dashboard (step 3 should move to review).

## Phase 5 — After submit

- [ ] Watch the portal bell + email for tester/manager comments. Fix and re-upload only what they reject (Uploaded Evidence section).
- [ ] If 3.3.1 fails under Option B → implement MFA (1.3 Option A), redeploy, re-upload that row.
- [ ] Clean report → download from Scan List → email `casasupport@tacsecurity.com`.
- [ ] TAC submits LOV to Google → reply-all on the Trust and Safety thread (text in `TAC_ESOF_PORTAL_GUIDE.md` §8). Watch Verification Center.

## Suggested timeline

| Day | Work |
| --- | --- |
| Day 1 (27 Aug) | ✅ All Phase 1 code + tests landed (logout, login hardening, MFA Option A, dep bumps) |
| Day 2 | Owner deploys staging → verify (logout replay 401, login throttle, MFA enroll, platform gate) → prod; platform admins enroll TOTP; screenshots (S7, S10, S12 need the deploys) |
| Day 3 | Phase 3 rendering; Phase 4 upload + Submit |
| Day 4+ | TAC review responses |

Buffer to 18 Nov is wide, but TAC review + Google reverification (5–6 business days) sit at the end — submitting this week keeps every retest cycle cheap.

---

## Appendix — per-row status tracker

Verdicts from `GAP_ANALYSIS_48_CHECKS.md`. Comments: §7 of the portal guide.

| Row | ID | Verdict | Evidence set | Done |
| --- | --- | --- | --- | --- |
| 1 | 1.1.1 | Code landed → deploy, regen PNGs + S1/S7/S8 | CASA_1_1_1 (regenerated) | [ ] |
| 2 | 1.1.2 | Ready | attest + S8 | [ ] |
| 3 | 1.1.3 | Ready | M9d | [ ] |
| 4 | 1.2.1 | Ready | attest | [ ] |
| 5 | 1.3.1 | Ready | attest + S3 | [ ] |
| 6 | 1.3.2 | Ready | attest + S3 | [ ] |
| 7 | 1.3.3 | Ready | attest + S3 | [ ] |
| 8 | 1.3.4 | Ready | attest + S3 | [ ] |
| 9 | 2.1.1 | Ready | M9d + dast | [ ] |
| 10 | 2.2.1 | Code landed → deploy + S10 | CASA_2_2_1 + S10 | [ ] |
| 11 | 2.2.2 | Ready (GoTrue default terminate-others; no live two-device reset) | CASA_2_2_2 | [ ] |
| 12 | 2.2.3 | Ready (staging JWT 8 h < 24 h) | CASA_2_2_3 | [ ] |
| 13 | 2.3.1 | Ready (honest N/A — not a cookie session) | CASA_2_3_1 | [ ] |
| 14 | 2.3.2 | Ready (honest N/A — not a cookie session) | CASA_2_3_2 | [ ] |
| 15 | 2.3.3 | Ready (GoTrue JWT minted per login) | CASA_2_3_3 | [ ] |
| 16 | 2.3.4 | Ready (jose verifies JWT; ZAP lists no JWT-sig/none alerts) | CASA_2_3_4 | [ ] |
| 17 | 2.4.1 | Ready (valid session on PATCH /me; password via recovery email; MFA disable needs TOTP) | CASA_2_4_1 | [ ] |
| 18 | 3.1.1 | Ready (API RBAC + tenant/assignment guards; staging unsigned 401) | CASA_3_1_1 | [ ] |
| 19 | 3.1.2 | Ready (server profile attrs; register/OAuth ignore client tenant_id) | CASA_3_1_2 | [ ] |
| 20 | 3.1.3 | Ready (fail closed 401/403; cron secret unset is unreachable; generic 500) | CASA_3_1_3 | [ ] |
| 21 | 3.1.4 | Ready (ID-parameter APIs + tenant/assignment guards; staging unsigned ID paths 401) | CASA_3_1_4 | [ ] |
| 22 | 3.1.5 | Ready (Bearer not cookie; CORS origin allowlist; register 5/min; ZAP no 10202) | CASA_3_1_5 | [ ] |
| 23 | 3.1.6 | Ready (SPA HTML shell not Index of; API JSON 404; ZAP no plugin 0) | CASA_3_1_6 | [ ] |
| 24 | 3.2.1 | Ready (authorization code + PKCE S256; no implicit/ROPC; staging start 200) | CASA_3_2_1 | [ ] |
| 25 | 3.2.2 | Ready | oauth | [ ] |
| 26 | 3.3.1 | Option A landed → deploy, enroll admins | CASA_3_3_1 | [ ] |
| 27 | 4.1.1 | Ready + S5/S6 | M9a + SSL Labs | [ ] |
| 28 | 4.1.2 | Ready + S5/S6 | M9a + SSL Labs | [ ] |
| 29 | 4.1.3 | Ready | M9e | [ ] |
| 30 | 4.1.4 | Ready | M9e | [ ] |
| 31 | 5.1.1 | Ready | dast | [ ] |
| 32 | 5.1.2 | Ready | oauth | [ ] |
| 33 | 5.1.3 | Ready | sast | [ ] |
| 34 | 5.1.4 | Ready | sast | [ ] |
| 35 | 5.1.5 | Ready | dast + attest | [ ] |
| 36 | 5.1.6 | Ready | dast | [ ] |
| 37 | 5.1.7 | Ready (comp CSP) | comp + dast | [ ] |
| 38 | 5.1.8 | Ready (FP note) | dast | [ ] |
| 39 | 5.1.9 | Ready | sast | [ ] |
| 40 | 5.1.10 | Ready (FP note) | dast | [ ] |
| 41 | 5.2.1 | Ready | attest | [ ] |
| 42 | 6.1.1 | Code landed → deploy + S12 | deps (refreshed) + S12 | [ ] |
| 43 | 6.2.1 | Ready | M9a + S11 | [ ] |
| 44 | 6.3.1 | Ready | M9f | [ ] |
| 45 | 6.4.1 | Verify S9 | M9a + S9 | [ ] |
| 46 | 6.5.1 | Ready | M9g | [ ] |
| 47 | 6.6.1 | Ready (verified 27 Aug) | comp | [ ] |
| 48 | 6.7.1 | Ready | M9d | [ ] |
