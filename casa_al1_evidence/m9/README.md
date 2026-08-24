# M9 evidence packet (draft)

Honest against **production** when the artifact is live; otherwise labeled staging-only or code-only. Short statements. Do not paste secrets, JWTs, or Fernet keys.

Folder: `casa_al1_evidence/m9/`. Fluid Attacks SAST CSV and official ZAP CASA XML exist (see `M9h_scan_process.md`). Production CSP + API headers + Swagger-off are live (22 Aug 2026).

| ID | File | Status 22 Aug 2026 |
| --- | --- | --- |
| M9a | `M9a_architecture.md` | draft — CloudFront SPA + ECS API (not the old EC2 diagram) |
| M9b | `M9b_data_flow.md` | draft — connect → inbound → draft → send → calendar → disconnect → deletion |
| M9c | `M9c_scope_to_google_api.md` | draft from code |
| M9d | `M9d_token_storage.md` | draft from code (disconnect is soft-deactivate) |
| M9e | `M9e_pii_encryption.md` | draft from code |
| M9f | `M9f_tenant_isolation.md` | draft + passing test names |
| M9g | `M9g_logging.md` | draft — `_mask_email`; no token/body log claim beyond code inspection |
| M9h | `M9h_scan_process.md` | draft — Fluid CSV + official ZAP SPA/API unauth + API auth XML |
| M9i | `M9i_incident_response.md` | draft — notify Google; 30-day public SLA; code gaps on token wipe |
| M9j | `M9j_subprocessors_ai.md` | draft — AWS opt-out live; OpenAI Data-controls screenshot **not captured** |

Also: `self_attestation_draft.md`.
