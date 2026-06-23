# Document Template Library — Tenant-Uploaded Fillable-PDF Plan

**Status:** Plan only — reviewed and corrected; awaiting Jan's approval before implementation
**Owner:** Jan (sole dev)
**Last updated:** 2026-06-21 (rev 2 — workflow/logic review applied; see §12 Review log)
**Frontend root:** `velvet-elves-frontend/src/pages/settings/` (new admin page) + `src/pages/documents/DocumentsPage.tsx` (chooser)
**Backend roots:** `velvet-elves-backend/app/api/v1/documents.py`, `app/services/document_template_registry.py`, `app/api/v1/dashboard.py`
**Builds on:** the shipped `generate-from-template` flow (deterministic code templates + `_collect_template_context` data sourcing + `clear`/`template` priority event + flattened-PDF output).

---

## 0. Goal

Let a brokerage use **its own authorized forms** for "Generate from template" instead of our hardcoded text. A **tenant admin** uploads a **fillable PDF** (AcroForm) once; the form's fields are mapped to our canonical data keys; from then on, clicking **Generate** fills that form deterministically with the deal's data and flattens it to a finished PDF.

This removes the accuracy/compliance risk of AI-written legal text (it's the tenant's real form), gives currency without web search (re-upload when a form changes), and keeps per-document cost near zero (the fill is pure code; AI is used only once, at upload, to *suggest* the field mapping).

### 0.1 Relationship to existing "template" concepts (avoid confusion)
This is a **new, distinct** subsystem:
- **Document templates** (this plan) = binary fillable-PDF *legal forms* + a field mapping, in a dedicated `document_templates` table (PDFs can't live in JSON).
- Not the existing **checklist templates** (closing checklists in `profile_settings_json`, per requirements.txt §4.10) nor **task_templates** (master task library).
- Naming and admin-CRUD follow the established convention (`/api/v1/task-templates`, `/api/v1/vendor-communications/templates`).

### Locked decisions (Jan, 2026-06-21)
1. **Management:** Tenant admins only (`UserRole.ADMIN`, *not* the platform super-admin) may upload/edit/delete templates.
2. **Multiplicity:** Multiple templates per doc type; the user picks at generate time.
3. **Built-ins:** Built-in code templates retire *per doc type* once the tenant uploads their own (precedence; built-ins remain the default for uncovered types).
4. **Output:** Always flatten the filled form to a static PDF.

---

## 1. Resolution model

### 1.1 How a template is matched to a Generate request
The generate request carries `item_key` (the requirement, e.g. `lead_paint_disclosure`) and `doc_type` (a `DocumentType`). A stored template carries a **`doc_type` (primary link)** and an **optional `item_key` (advanced, finer targeting)**. A template matches when:
- `template.item_key` is set AND `normalize(template.item_key) == normalize(request.item_key)`  → **specific match**, or
- `template.item_key` is null AND `template.doc_type == request.doc_type`  → **type match**.

Normalize with the existing `normalize_template_item_key` so `missing:{tx}:{key}` and bare `{key}` compare equal. Specific (item_key) matches rank above type matches.

### 1.2 Generate precedence
1. **Tenant template(s)** matching (active):
   - exactly one match → fill + flatten + store. No missing-fields gate (see §4.4) — the tenant's form is filled with whatever data exists and blanks remain for the reviewer.
   - 2+ matches and no `template_id` → return `status="choose_template"` with `[{id, name}]`; UI shows a chooser; user picks → re-call with `template_id` → fill + flatten + store.
2. else **built-in code template** (`_TEMPLATE_RULES`) → existing behavior, including its `required`-field **`missing_fields`** flow + the inline fill modal.
3. else **`no_template`** → existing Upload / Request modal.

"Retire built-ins" = step 1 wins over step 2 for any doc type the tenant has covered. No built-in code is deleted; it is simply unreachable when a tenant template matches.

> **Corrected logic (rev 2):** the inline **missing-fields** flow belongs to **built-in** templates only (they declare `required` fields). Uploaded templates do **not** gate on missing data — they fill-and-flatten with available values, leaving form blanks for the reviewer. This removes the earlier §4.4↔§5.2 contradiction and means the `choose_template` path never needs to thread `template_id` through a missing-fields loop.

---

## 2. Data model

New migration `supabase/migrations/<ts>_document_templates.sql`, following the RLS pattern in `20260513090000_documents_priority_completion.sql` (`service_role_all` + `tenant_isolation` via `public.auth_tenant_id()`):

```sql
CREATE TABLE public.document_templates (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  doc_type        TEXT,                 -- DocumentType value (primary link)
  item_key        TEXT,                 -- optional requirement key for finer targeting
  storage_path    TEXT NOT NULL,        -- uploaded fillable PDF in the documents bucket
  field_mapping   JSONB NOT NULL DEFAULT '{}'::jsonb,   -- {pdf_field_name: canonical_key}
  detected_fields JSONB NOT NULL DEFAULT '[]'::jsonb,   -- [{name,type}] snapshot at upload
  is_active       BOOLEAN NOT NULL DEFAULT FALSE,        -- false until the admin finalizes
  created_by      UUID NOT NULL REFERENCES public.users(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT document_templates_link_chk CHECK (doc_type IS NOT NULL OR item_key IS NOT NULL)
);
CREATE INDEX ix_document_templates_lookup
  ON public.document_templates (tenant_id, is_active, doc_type, item_key);
```

- `CHECK` guarantees every template is matchable (at least one of `doc_type`/`item_key`).
- `is_active` defaults **FALSE** — a freshly uploaded template is a draft until the admin confirms the mapping (see §4.5), so a half-configured template never fills a real document.
- `repositories/document_template_repository.py` (tenant-scoped) with `list_for_tenant`, `match_for(tenant_id, item_key, doc_type)`, and `active_links_for_tenant(tenant_id) -> set` (for the queue gate).

---

## 3. Storage

- Template PDF stored in the existing `documents` bucket under `templates/{tenant_id}/{uuid}_{safe_name}.pdf`, via the service-role upload (`_upload_storage_object`). The bucket already has a `service_role_*_all` policy (`202603111900_storage_documents_bucket.sql`), so no new storage policy is needed; authorization is enforced at the API layer.
- Templates live only in `document_templates`, never in the `documents` table, so they never appear in All Documents.

---

## 4. Backend

### 4.1 Canonical field vocabulary
The mapping targets a fixed key set, resolved by extending `_collect_template_context` (today: address, buyer_name, seller_name, title_company, purchase_price). Add: `property_city/state/zip`, `buyer_email/phone`, `seller_email/phone`, `earnest_money`, `closing_date`, `acceptance_date`, `listing_agent_name`, `buyers_agent_name`, `today_date`. Each resolves transaction → parties → parsed `ai_extracted_data` (reusing `_name_from`, `_extracted_value`, `_compose_address`; the `ExtractionResult` already carries closing_date/earnest_money/listing_agent/buyers_agent/title_company).

### 4.2 Field detection (PyMuPDF — verified on 1.27.2.2)
```python
import fitz
doc = fitz.open(stream=pdf_bytes, filetype="pdf")
fields = [
    {"name": w.field_name, "type": w.field_type_string}
    for page in doc for w in (page.widgets() or [])
    if w.field_name
]
```
If `fields` is empty → reject (`422`): "This PDF has no fillable fields. Upload a fillable PDF (AcroForm)." **Phase 1 maps only Text fields**; checkbox/radio/dropdown/signature widgets are listed (so the UI can show "not yet supported") but not mappable until Phase 3.

### 4.3 AI-suggested mapping (one-time, human-confirmed) — Phase 2
`AIService.suggest_field_mapping(field_names, canonical_keys) -> {field_name: key|null}`. **Sends only PDF field names + the key vocabulary — no transaction PII** (privacy-safe, cacheable), using the tenant's selected provider (no auto-switch). Phase 1 ships a code auto-match (case-insensitive / `snake_case` similarity) so the feature is usable before the AI assist lands; the admin always confirms before the template goes active.

### 4.4 Fill engine (deterministic — verified)
```python
doc = fitz.open(stream=template_bytes, filetype="pdf")
for page in doc:
    for w in (page.widgets() or []):
        key = mapping.get(w.field_name)
        value = context.get(key) if key else None
        if value not in (None, ""):
            w.field_value = str(value)
            w.update()
doc.bake()            # flatten form fields to static content — confirmed present & working on 1.27.2.2
return doc.tobytes()
```
Verified end-to-end: filled values render and 0 widgets remain after `bake()`. Unmapped fields and fields with no data stay blank. The result is stored as a draft document (`acceptance_status='draft'`, `review_status='unreviewed'`) with the same `clear`/`template` priority event + audit row as today (extract `_persist_generated_draft(...)` and reuse for both built-in and uploaded fills).

### 4.5 Template management endpoints (tenant admins only — `require_role(UserRole.ADMIN)`)
Single-step upload (no "bytes in limbo"): the upload call **persists** the PDF and a **draft** (`is_active=false`) row, then the admin finalizes via PATCH.
- `POST   /api/v1/document-templates` — multipart upload. Validates PDF + AcroForm fields; stores the PDF; creates a draft row with `detected_fields` + a code auto-matched `field_mapping`; returns the row.
- `GET    /api/v1/document-templates` — list tenant templates.
- `PATCH  /api/v1/document-templates/{id}` — edit `name`/`doc_type`/`item_key`/`field_mapping`/`is_active` (setting `is_active=true` finalizes). Enforces the `doc_type`-or-`item_key` rule.
- `DELETE /api/v1/document-templates/{id}` — soft-delete (set `is_active=false` + tombstone) so in-flight references degrade gracefully.

### 4.6 generate-from-template integration
- `DocumentTemplateGenerateRequest`: add `template_id: str | None`.
- `DocumentTemplateGenerateResponse`: add `status="choose_template"` + `templates: list[{id, name}]`.
- Endpoint applies §1: resolve tenant matches → (one) fill / (many) choose_template / (none) built-in → no_template. Reuses `_persist_generated_draft`.

### 4.7 Priority-queue gating (tenant-aware) — Phase 1
`dashboard.py` currently drops the `template` alt-action **and** demotes a `template` `suggested_action` when `not template_registered(req["key"])`. Make that single condition tenant-aware:
```python
offers_template = template_registered(req["key"]) or req["key"] in tenant_template_links \
    or req.get("doc_type") in tenant_template_doc_types
if not offers_template:
    # drop template from alt_actions AND demote suggested_action (unchanged logic)
```
Load `tenant_template_links` / `tenant_template_doc_types` **once per queue build** (one `active_links_for_tenant` call), not per item. This is what surfaces Generate for requirements we never hand-coded (e.g. Appraisal Report, Title Commitment) the moment a tenant uploads a matching form.

---

## 5. Frontend

### 5.1 Settings → Document Templates (tenant-admin only)
New page under the Settings hub, registered in `settingsCards.ts` (card shown only to `UserRole.ADMIN`) and routed under `/settings/*` with an **admin-gated** `RoleRoute` (precedent: `AdminTeamSettingsPage`, not the default `INTERNAL_AND_ATTORNEY` gate the other settings pages use). Flow: list templates (name, doc type, linked requirement, active toggle); **Upload** → backend returns detected fields + auto-match suggestion → admin maps each **Text** field to a canonical key (dropdowns), sets `name`, picks `doc_type` from a **`DocumentType` dropdown** (primary link) and optionally an `item_key` (advanced) → Save (sets `is_active=true`). Non-text fields are shown read-only with a "not yet supported" tag. Edit mapping / activate / soft-delete. Radix dialogs, consistent with the app.

### 5.2 Generate flow
Unchanged for the common single-template and built-in cases. New: when the backend returns `status="choose_template"`, show a small chooser (template names); on pick, re-call `generateTemplateDraft({..., templateId})`. Uploaded-template generation goes straight to the flattened-PDF preview (no missing-fields step). The built-in path keeps its existing `missing_fields` modal + inline fill. Add `templateId` to the `useGenerateDocumentFromTemplate` input and the frontend `TemplateGenerateResponse` union (`choose_template`).

---

## 6. Security & validation
- All management endpoints: **tenant admins** (`require_role(UserRole.ADMIN)`); tenant-scoped repo + RLS (`auth_tenant_id()`); platform super-admin is a separate concept and not required here.
- Upload: `application/pdf`, must contain AcroForm fields, ≤ 20 MB (reuse limits); reject non-fillable PDFs with guidance.
- Every template must set `doc_type` or `item_key` (DB CHECK + API validation) so it is matchable.
- Output PDF is flattened — no live form fields remain.
- Generated doc stays draft/unreviewed; human review before send (existing guardrail). It is a normal document, so the existing Send-for-Signature flow works on it.
- AI mapping call carries only field names + key vocabulary, never transaction data; tenant's chosen provider, no auto-switch.

---

## 7. Edge cases
| Case | Behavior |
| --- | --- |
| Uploaded PDF has no form fields | Reject at upload with clear guidance. |
| Mapped field has no value at generate | Leave blank in the output (no gate — uploaded templates are fill-and-flatten). |
| Template saved with neither doc_type nor item_key | Blocked by DB CHECK + API validation. |
| 2+ matching templates | `choose_template` response; `template_id` selects one. |
| Template deactivated/deleted while referenced | Generate falls back to next match → built-in → no_template. |
| Non-text widgets (checkbox/radio/signature) | Listed but unmappable in P1; ignored at fill; Phase 3 adds them. |
| Duplicate field name across pages | All instances receive the value (AcroForm semantics) — fine. |
| Encrypted values (address/names) | Decrypted in context building (existing `_safe_decrypt_value`). |
| `bake()` raises on a malformed PDF | Defensive fallback: set `NeedAppearances` and keep values, log a warning, still return a PDF. (`bake()` itself confirmed working on 1.27.) |
| Tenant template matches a built-in key | Tenant template wins (retirement rule). |

---

## 8. Test plan
**Backend**
- Build a fillable PDF in-test (`fitz` `add_widget`); detect its fields.
- Fill engine sets mapped fields and flattens; extracted text shows values; no widgets remain.
- Generate prefers an active tenant template over the built-in for the same doc type.
- 2+ active matches → `choose_template`; `template_id` selects one and fills it.
- Tenant template retires the built-in for that type; uncovered types still use the built-in.
- Admin-only enforcement (non-admin / platform-only → 403); tenant isolation (no cross-tenant read/use/fill).
- `is_active=false` draft template is NOT used by generate until finalized.
- Template with neither doc_type nor item_key rejected (CHECK/validation).
- AI mapping suggestion (mock `AIService`) maps obvious names; manual override persists.
- Priority queue offers `template` (alt + suggested) once a tenant template matches; not before.
- Fallback to `no_template` when neither tenant nor built-in matches.

**Frontend**
- Settings page: list/upload/map/finalize; admin-only visibility (hidden for non-admin roles).
- Chooser appears with 2+ matches; selection drives generate.
- Generate previews the flattened PDF.

---

## 9. Phases
- **Phase 1 — Core (no AI):** migration + repo + storage + single-step admin upload (+ PATCH finalize) + field detection + **code auto-match** mapping + deterministic fill/flatten + generate integration (precedence + chooser + retirement) + **tenant-aware queue gating** + tests.
- **Phase 2 — AI mapping assist:** `AIService.suggest_field_mapping` at upload (field names only), human-confirmed.
- **Phase 3 — Field breadth:** checkbox/radio/dropdown/signature-tag mapping; template versioning (re-detect on re-upload).
- **Phase 4 — DOCX templates (future):** `{{merge}}` DOCX + a DOCX→PDF converter (LibreOffice/Gotenberg) — separate infra decision.

---

## 10. Open questions / future
- e-sign anchor placement: let templates tag where DocuSign signature/date anchors go, so a generated draft flows straight into Send for Signature. (Flattened PDFs lose form fields, which is fine — DocuSign places its own tags; this would just pre-position them.)
- Platform-level shared starter library (cross-tenant, `tenant_id=NULL`, mirroring `task_templates`' system-wide tier) — out of scope here.
- Per-state default template packs.

---

## 11. Definition of done (Phase 1)
- A tenant admin can upload a fillable PDF, map its text fields to canonical keys, link it to a doc type (and optionally a requirement), and activate it.
- Clicking Generate for a covered doc type fills the tenant's form with the deal's data and produces a flattened PDF draft (no built-in text), reviewable in the existing preview; multiple matches show a chooser.
- The built-in template is no longer used for a covered type; uncovered types still use the built-in; the priority queue offers Generate for newly-covered requirements.
- All management is tenant-admin-only and tenant-isolated; tests green; no regressions in the existing generate/All-Documents flows.

---

## 12. Review log (rev 2 — 2026-06-21)

Verified against source/docs:
- **PyMuPDF 1.27.2.2** supports `Widget`/`add_widget`/`page.widgets()`/`field_value`/`update()`/**`bake()`**/`tobytes()` — smoke-tested: filled text renders, 0 widgets after bake. (Removed the earlier "verify bake()" hedge.)
- **`UserRole.ADMIN` = tenant admin**, distinct from `User.is_platform_admin` / `require_platform_admin`. Management uses `require_role(UserRole.ADMIN)`.
- **RLS**: follow `20260513090000_documents_priority_completion.sql` (`service_role_all` + `tenant_isolation` on `auth_tenant_id()`); **storage** documents bucket already has a service-role policy.
- **`DocumentType`** enum values (lead_paint_disclosure, amendment, wire_transfer_authorization, …) are the template `doc_type` vocabulary.
- **Settings** live in `src/pages/settings/` (`SettingsRouter`, `settingsCards.ts`, `SettingsHubPage`) with an admin-gated precedent (`AdminTeamSettingsPage`).
- Distinct from existing checklist templates (`profile_settings_json`) and `task_templates`; CRUD naming follows `*-templates` convention.

## 13. Flat (non-fillable) PDF support — field placement (Jan, 2026-06-21)

Decision: accept ANY PDF, not just AcroForms. The blunt "no fillable fields"
rejection is replaced by a placement path that still fills the tenant's exact
form (no AI-regenerated legal text, no per-generate AI overlay).

### 13.1 Two fill modes
- **`acroform`** (existing): the PDF has form fields → map field names to
  canonical keys → `fill_and_flatten`.
- **`overlay`** (new): the PDF has no fields → the admin places labeled boxes
  on the rendered pages, each assigned a canonical key → at generate we draw
  the value into each box's rectangle and output. Deterministic, free per-doc,
  preserves the exact form.

The Wizard's parsing extracts data FROM a doc; placement is the inverse
(positioning values INTO a blank), so AI here ASSISTS placement (proposes
label→key + positions from the text layer/OCR) with a human confirm — it never
regenerates the document or positions values at generate time.

### 13.2 Data model (additive migration)
Add to `document_templates`:
- `fill_mode TEXT NOT NULL DEFAULT 'acroform'` CHECK in ('acroform','overlay').
- `field_placements JSONB NOT NULL DEFAULT '[]'` — `[{page,x,y,w,h,key,font_size?}]`
  in PDF points (PyMuPDF coordinates, origin top-left).

### 13.3 Backend
- **Upload**: detect AcroForm fields. If present → `acroform` (as today). If
  none → DON'T reject; create an `overlay` draft (admin places fields next).
- **Page rendering** (for the editor): `GET /document-templates/{id}/pages` →
  `{page_count, width, height}`; `GET /document-templates/{id}/page/{n}` →
  PNG via PyMuPDF `get_pixmap`. Admin-only.
- **Overlay fill engine** in `pdf_form_fill.py`: for each placement, draw the
  value with `page.insert_textbox(rect, value, fontname="helv")`; return bytes.
- **Generate** picks `fill_overlay` vs `fill_and_flatten` by `fill_mode`.
- **Activation gate**: an `overlay` template needs ≥1 placement to activate.

### 13.4 Frontend (placement editor)
The Edit dialog, for `overlay` templates, renders each page image with
absolutely-positioned, draggable/resizable field boxes; the admin adds a box,
assigns a canonical key, positions it; coordinates map image-pixels ↔ PDF
points by the render scale. Save persists `field_placements` via PATCH.

### 13.5 AI assist (later slice)
`POST /document-templates/{id}/suggest-placements` reads the text layer
(`page.get_text`) to find labels and proposes `{page,rect,key}` boxes
(heuristic label→key, optionally LLM for the label→key step using text only).
Admin reviews/adjusts — positions stay deterministic from the text layer.

### 13.6 Phasing
- 13a (backend): migration + accept flat + overlay fill + page-render endpoints
  + generate wiring + tests.
- 13b (frontend): the visual placement editor.
- 13c: AI-assisted placement proposals.

---

Logic/workflow flaws corrected:
1. **Missing-fields contradiction** (old §4.4 vs §5.2): uploaded templates now explicitly fill-and-flatten with no missing-fields gate; that flow stays built-in-only. Also dissolves the chooser→missing-fields→`template_id` threading concern.
2. **Upload "bytes in limbo"**: replaced the upload→separate-confirm design with a single upload that persists the PDF + a draft (`is_active=false`) row; finalize via PATCH.
3. **Template→request matching** made precise (doc_type primary, item_key optional/specific, normalized) and `is_active=false` excluded from generate.
4. **Queue gating**: the single condition controlling both the `alt_actions` drop and the `suggested_action` demotion is made tenant-aware, with the tenant link set loaded once per build.
5. **Linkage integrity**: DB CHECK + validation require doc_type or item_key; Settings offers a `DocumentType` dropdown so links are always valid.
6. **Field-type handling**: only Text fields mappable in P1; other widget types surfaced but ignored.
